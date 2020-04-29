from json import JSONDecodeError

import uncurl
import xerox
import json


def get_query_dict(query):
    result = {}
    for param in query.split("&"):
        key, value = param.split("=")
        result[key] = value
    return result


def main():
    curl_input = xerox.paste()
    context = uncurl.parse_context(curl_input)
    try:
        request_data = json.loads(context.data)
    except JSONDecodeError:
        request_data = context.data
    print(request_data.replace("\\n", "\n"))
    print(request_data["operationName"])
    print("-----\n\n")
    print(request_data["query"])
    print("-----\n\n")
    print(json.dumps(request_data["variables"], indent=2))


if __name__ == "__main__":
    main()
