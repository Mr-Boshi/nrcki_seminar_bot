import os
import time
import json
from modules.env_setter import load_env

_, _, _, _, TIMER, _, _, _, _, _ = load_env()

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
    chars_to_remove = ",.!?\/()[]}{:;'#*"
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