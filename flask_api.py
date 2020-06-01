import csv_scripts
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/api", methods = ["GET", "POST"])
def api():
    if request.method == "GET":
        brand = request.args.get("brand", default="")
        text = request.args.get("description")
        rows, fieldnames = csv_scripts.add_commodities_to_stocks([{"Brand": brand, "id": "1", "text": text}])
        return {"Results": rows}
    if request.method == "POST":
        json = request.json
        rows = []
        for i, row in request["rows"]:
            if "brand" in row:
                brand = row["brand"]
            else:
                brand = ""
            rows.append({"Brand": brand, "id": str(i), "text": row["description"]})
        rows, fieldnames = csv_scripts.add_commodities_to_stocks(rows)
        return {"Results": rows}

