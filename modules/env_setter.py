import os
from dotenv import load_dotenv

def load_env():
    # Load environment variables from the .env file
    load_dotenv()

    # Access the environment variables
    BOT_TOKEN  = os.getenv("bot_token")
    CHAT_ID    = os.getenv("chat_id")
    ADMIN_ID   = os.getenv("admin_id")
    MODERATORS = os.getenv("moderators_id")
    TIMER      = os.getenv("timer")
    RATE       = os.getenv("rate_limit")
    SILENT_SRT = os.getenv("silent_start")

    return BOT_TOKEN, CHAT_ID, ADMIN_ID, string_to_number_list(MODERATORS), int(TIMER), float(RATE), str_to_bool(SILENT_SRT)

def str_to_bool(envar):
    if envar == 'True':
        return True
    elif envar == 'False':
        return False
    else:
        return None

def string_to_number_list(input_string):

    number_strings = [num.strip() for num in input_string.split(',')]
    
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
