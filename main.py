import os
from dotenv import load_dotenv

# Load environment variables from the .env file
if not os.getenv('IN_DOCKER'):
    load_dotenv()

import telebot
from time import sleep
from threading import Thread
from bot.bot import setup_handlers, run_bot
from bot.common import check_new_entries
from bot.rate_limiter import RateLimiter
from modules.common import str_to_bool
from modules.news_handler import seminar_link_finder

def run_schedule(TIMER):
    wait_time = TIMER * 3600
    while True:
        check_new_entries(config, bot, limiter)
        sleep(wait_time)

# Load environment variables from the .env file
BOT_TOKEN = os.getenv('bot_token')
ADMIN = int(os.getenv('admin_id'))
RATE = float(os.getenv('rate_limit'))
SILENT_SRT = str_to_bool(os.getenv('silent_start'))
TIMER = int(os.getenv('timer'))

# Setting up the names of files to store news and subscriptions.
filedir = "data"
os.makedirs(filedir, exist_ok=True)

#Setup config dict
config = {
    'seminars' : [
        "Отдел Т: Эксперименты на токамаках",
        "Инженерно-физические проблемы термоядерных реакторов",
        "Теория магнитного удержания плазмы",
        "Инженерно-физический семинар по токамакам"
    ],
    'keybord_options' : [
        "Отдел Т: Эксперименты на токамаках",
        "Инженерно-физические проблемы термоядерных реакторов",
        "Теория магнитного удержания плазмы",
        "Инженерно-физический семинар по токамакам",
        "Все!"
    ],
    'hashtags' : ["#ОТ","#ИФП","#ТМУ","#ИФС","#Семинар"],
    'news_file' : os.path.join(filedir, "news.json"), 
    'subs_file' : os.path.join(filedir, "subscribtions.json"),
    'states_file' : os.path.join(filedir, "states.json"),
    'links_file': os.path.join(filedir, "links.json")

}

# Main loop
# ==============================================================================
# ==============================================================================

if __name__ == "__main__":
    if not os.path.exists(config['links_file']):
        seminar_link_finder(link_file = config['links_file'])

    # Creating rate-limiter object
    limiter = RateLimiter(1/RATE)

    # Create the TeleBot instance
    bot = telebot.TeleBot(BOT_TOKEN)
    setup_handlers(bot, config, limiter)

    # Remove user states if exist
    if os.path.exists(config['states_file']):
        os.remove(config['states_file'])

    # Send greeting message
    if not SILENT_SRT:
        bot.send_message(chat_id=ADMIN, text="Бот запущен!")
    

    Thread(target=run_bot, args=(bot,)).start()
    Thread(target=run_schedule, args=(TIMER,)).start()

