import logging

import azure.functions as func

import json

from __app__.scripts import commodity_matcher

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    if req.method == "GET":
        brand = req.params["brand"] if "brand" in req.params else ""
        text = req.params["description"] if "description" in req.params else ""
        try:
            topn = int(req.params["topn"])
        except:
            topn = 1
        rows = [{"Brand": brand, "id": "1", "text": text}]
        results = commodity_matcher.add_commodities_to_stocks(rows, topn=topn, parallel=False)
    elif req.method == "POST":
        try:
            params = req.get_body().decode("utf-8").split("&")
            for param in params:
                if param[:5] == "rows=":
                    rows = param[5:].split("%0D%0A")
                    break
            assert rows
        except Exception as e:
            # Add "\n"+str(e) when debugging for convenience
            return func.HttpResponse("The rows data parameter was malformatted or empty.", status_code=400)
        inputs = []
        
        for i, row in enumerate(rows):
            inputs.append({"Brand": "", "id": str(i), "text": row})
        results = commodity_matcher.add_commodities_to_stocks(inputs, parallel=False)
        #else:
        #    return func.HttpResponse("The POST request did not include a 'rows' data parameter.", status_code=400)
    else:
        return func.HttpResponse("Request method not supported.", status_code=405)
    results = results[0]
    for result in results:
        result["Description"] = result.pop("text") # Rename text -> Description
        result["Similarity"] = result.pop("Jaccard") # Rename Jaccard -> Similarity
        for i in range(2,topn+1):
            try:
                result["Similarity "+str(i)] = result.pop("Jaccard "+str(i))
            except Exception as e:
                print(result)
                print(e)
    return func.HttpResponse(json.dumps(results))

    # name = req.params.get('name')
    # if not name:
    #     try:
    #         req_body = req.get_json()
    #     except ValueError:
    #         pass
    #     else:
    #         name = req_body.get('name')

    # if name:
    #     return func.HttpResponse(f"Hello {name}!")
    # else:
    #     return func.HttpResponse(
    #          "Please pass a name on the query string or in the request body",
    #          status_code=400
    #     )
