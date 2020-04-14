import uncurl
import xerox
import json
from urllib.parse import urlparse


def get_query_dict(query):
    result = {}
    for param in query.split("&"):
        key, value = param.split("=")
        result[key] = value
    return result


def main():
    curl_input = xerox.paste()
    print("Input: -----")
    print(curl_input)
    print("-----\n\n")
    context = uncurl.parse_context(curl_input)
    request_data = json.loads(context.data)
    url = urlparse(context.url)
    query_params = get_query_dict(url.query)
    cookie_string = ";".join(f"{key}={value}" for key, value in context.cookies.items())
    postman_collection = {
        "info": {
            "name": request_data["operationName"],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [
            {
                "name": request_data["operationName"],
                "request": {
                    "method": "POST",
                    "header": [],
                    "body": {
                        "mode": "graphql",
                        "graphql": {
                            "query": request_data["query"],
                            "variables": json.dumps(request_data["variables"]),
                        },
                    },
                    "url": {
                        "raw": context.url,
                        "protocol": url.scheme,
                        "host": [url.hostname],
                        "port": url.port,
                        "path": url.path.split("/"),
                        "query": [
                            {"key": key, "value": value}
                            for key, value in query_params.items()
                        ],
                    },
                },
                "response": [],
            }
        ],
        "protocolProfileBehavior": {},
    }
    result = json.dumps(postman_collection)
    print("----- Postman Collection ----")
    print(result)
    print("---- Headers -----")
    for key, value in context.headers.items():
        print(f"{key}:{value}")
    print(f"Cookie:{cookie_string}")
    print("-----")
    xerox.copy(result)


if __name__ == "__main__":
    main()
