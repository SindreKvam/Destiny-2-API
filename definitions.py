import json


def printjson(input):
    input_json = input.json()
    json_string = json.dumps(input_json)
    json_object = json.loads(json_string)
    json_formatted_str = json.dumps(json_object, indent=4)
    print(json_formatted_str)


def printdict(input):
    print(json.dumps(input, indent=4))
