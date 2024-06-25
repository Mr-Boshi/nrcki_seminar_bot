import telebot
import os
from aiohttp import web
from bot.bot import setup_handlers
from bot.rate_limiter import RateLimiter
from modules.env_setter import load_env
from modules.webhook_handler import setup_web_app
from modules.news_handler import seminar_link_finder

# Load environment variables from the .env file
BOT_TOKEN, _, ADMIN, _, _, RATE, SILENT_SRT, _, _, PORT = load_env()

# Setup webhook parameters
WEBHOOK_LISTEN = "0.0.0.0"
WEBHOOK_PORT = PORT

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
    
    # Create web app to handle webhooks
    app, context = setup_web_app(bot, config, limiter)

    # Send greeting message
    if not SILENT_SRT:
        bot.send_message(chat_id=ADMIN, text="Бот запущен!")
    
    web.run_app(
        app,
        host=WEBHOOK_LISTEN,
        port=WEBHOOK_PORT,
        ssl_context=context,
    )
