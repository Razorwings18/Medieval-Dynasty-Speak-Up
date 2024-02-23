import json

def write_to_json(dictionary, filename):
    try:
        with open(filename, 'w') as json_file:
            json.dump(dictionary, json_file, indent=4)
    except Exception as e:
        print(f"Error writing JSON: {e}")

def load_from_json(filename):
    try:
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        # If the file doesn't exist, create an empty dictionary
        data = {}
        write_to_json(filename, data)
    return data

def load_strings_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        strings_list = file.read().splitlines()
    return strings_list