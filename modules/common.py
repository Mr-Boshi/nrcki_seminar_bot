import os
import time
import json

TIMER = int(os.getenv('timer'))

# Check file status
def check_news_file_status(filepath):
    if not os.path.exists(filepath):
        return "absent"
    elif (time.time() - os.path.getmtime(filepath)) / 3600 >= 0.75 * TIMER:
        return "outdated"
    else:
        return "updated"
    
# Loading data from json:
def load_json(file, type = 'list'):
    if os.path.exists(file):
        with open(file, "r") as json_file:
            data = json.load(json_file)
        return data
    else:
        if type == 'list':
            return []
        elif type == 'dict':
            return {}

# Searching in news
def dump_json(var, file):
    with open(file, "w") as json_file:
        json.dump(var, json_file)


# Searching in news
def find_matching_indexes(all_news, prompt):
    chars_to_remove = ",.!?\\/()[]}{:;'#*"
    prompt = prompt.lower()
    for char in chars_to_remove:
        prompt = prompt.replace(char, '')
    prompt_words = prompt.split()
    matching_indexes = [[] for _ in range(len(all_news))]

    for ind, seminar in enumerate(all_news):
        for index, item in enumerate(seminar):
            if all(word in item.lower() for word in prompt_words):
                matching_indexes[ind].append(index)

        return matching_indexes
    
def str_to_bool(envar):
    if envar == "True":
        return True
    elif envar == "False":
        return False
    else:
        return None


def string_to_number_list(input_string):
    number_strings = [num.strip() for num in input_string.split(",")]

    # Convert the list of strings to a list of numbers (integers or floats)
    number_list = []
    for num_str in number_strings:
        try:
            # Try to convert to integer
            number = int(num_str)
        except ValueError:
            try:
                # If it fails, try to convert to float
                number = float(num_str)
            except ValueError:
                # If it fails again, skip the value (or handle it as needed)
                continue
        number_list.append(number)

    return number_list