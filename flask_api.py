import os
import csv_scripts
from flask import Flask, jsonify, request
from rq import Queue
from rq.exceptions import NoSuchJobError
from rq.job import Job
from redis import Redis
import urllib.parse as urlparse
import json

app = Flask(__name__)
redis_url = os.getenv('REDISTOGO_URL')
urlparse.uses_netloc.append('redis')
url = urlparse.urlparse(redis_url)
conn = Redis(host=url.hostname, port=url.port, db=0, password=url.password)
q = Queue(connection=conn)  #no args implies the default queue

@app.route("/api", methods = ["GET", "POST"])
def api():
    if request.method == "GET":
        brand = request.args.get("brand", default="")
        text = request.args.get("description")
        rows = [{"Brand": brand, "id": "1", "text": text}]
        results = csv_scripts.add_commodities_to_stocks(rows)
        msg = "Success!"
        return {"Results": result[0], "Errors": [], "Status": status, "Message": msg}
    else:
        data = request.json
        rows = []
        for i, row in enumerate(data["rows"]):
            if "brand" in row:
                brand = row["brand"]
            else:
                brand = ""
            rows.append({"Brand": brand, "id": str(i), "text": row["description"]})
        row_hash = str(hash(json.dumps(rows)))
        try:
            j = Job.fetch(row_hash, conn)
            status = j.get_status()
            if status == "finished":
                if isinstance(j.result, Exception):
                    print(j.result)
                    msg = "Something went wrong and now everything is on fire."
                    return {"Results": [], "Errors": [str(j.result)], "Status": status, "Message": msg}
                else:
                    msg = "Success!"
                    return {"Results": j.result[0], "Errors": [], "Status": status, "Message": msg}
            else:
                msg = "Processing. Ask again in a few minutes to see your results."
                if status == "failed":
                    msg = "Time limit exceeded. Try a smaller job."
                return {"Results": [], "Errors": [], "Status": status, "Message": msg}

        except NoSuchJobError:
            j = q.enqueue(csv_scripts.add_commodities_to_stocks, rows, job_id=row_hash)
            msg = "Processing. Ask again in a few minutes to see your results."
            return {"Results": [], "Errors": [], "Status": j.get_status(), "Message": msg}

