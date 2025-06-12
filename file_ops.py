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
        write_to_json(data, filename)
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {filename}. Returning empty dictionary.")
        data = {}
    return data

def load_strings_from_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            strings_list = file.read().splitlines()
    except FileNotFoundError:
        strings_list = []
    return strings_list

def write_strings_to_file(filename, strings_list):
    """Writes a list of strings to a file, one string per line."""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            for item in strings_list:
                file.write(f"{item}\n")
    except Exception as e:
        print(f"Error writing to file {filename}: {e}")