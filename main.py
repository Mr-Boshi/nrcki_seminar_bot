import os
from dotenv import load_dotenv

# Load environment variables from the .env file
if not os.getenv("IN_DOCKER"):
    load_dotenv()

import telebot
from time import sleep
from threading import Thread
from bot.bot import setup_handlers, run_bot
from bot.common import check_new_entries
from bot.rate_limiter import RateLimiter
from modules.common import str_to_bool, dump_json, load_config
from modules.news_handler import seminar_link_finder


def run_schedule(TIMER):
    wait_time = TIMER * 3600
    while True:
        try:
            check_new_entries(config, bot, limiter)
            sleep(wait_time)
        except Exception as e:
            print(f"Got error while background news check: {e}")


# Load environment variables
BOT_TOKEN = os.getenv("bot_token")
ADMIN = int(os.getenv("admin_id"))
RATE = float(os.getenv("rate_limit"))
SILENT_MODE = str_to_bool(os.getenv("silent_mode"))
TIMER = int(os.getenv("timer"))
CONFIG_FILE = os.getenv("config_file")

# Setting up the names of files to store news and subscriptions.
filedir = "data"
os.makedirs(filedir, exist_ok=True)

# Setup config dict
config = load_config(CONFIG_FILE)
config["hashtags"] = config["hashtags"] + ["#Семинар"]
config["news_file"] = os.path.join(filedir, "news.json")
config["subs_file"] = os.path.join(filedir, "subscribtions.json")
config["states_file"] = os.path.join(filedir, "states.json")
config["links_file"] = os.path.join(filedir, "links.json")
config["nums_file"] = os.path.join(filedir, 'nums.json')
config["forw_file"] = os.path.join(filedir, 'forwarded_messages.json')


# Main loop
# ==============================================================================
# ==============================================================================

if __name__ == "__main__":
    # If links are not already stored - find links to seminars
    if not os.path.exists(config["links_file"]):
        seminar_link_finder(link_file=config["links_file"])

    # If file with seminar counters does not exist - create a placeholder with zeroes.
    if not os.path.exists(config["nums_file"]):
        seminar_nums = []
        for _ in range(len(config["seminars"])):
            seminar_nums.append(0)
        
        dump_json(seminar_nums, config["nums_file"])
        print("Seminar counter file is initilised.")

    # Creating rate-limiter object
    limiter = RateLimiter(1 / RATE)

    # Create the TeleBot instance
    bot = telebot.TeleBot(BOT_TOKEN)
    setup_handlers(bot, config, limiter)

    # Remove user states if exist
    if os.path.exists(config["states_file"]):
        os.remove(config["states_file"])

    # Send greeting message
    if not SILENT_MODE:
        bot.send_message(chat_id=ADMIN, text="Бот запущен!")

    Thread(target=run_bot, args=(bot,)).start()
    Thread(target=run_schedule, args=(TIMER,)).start()
