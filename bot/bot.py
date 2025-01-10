import os

from bot.command_handlers import (
    echo_simple_commands,
    echo_last_find,
    echo_keyboard_callback,
    echo_notify,
    echo_responces,
    echo_reply_from_chat
)

from modules.common import str_to_bool


# Load environment variables from the .env file
CHAT = int(os.getenv("chat_id"))
ADMIN = int(os.getenv("admin_id"))
RATE = float(os.getenv("rate_limit"))
TIMER = int(os.getenv("timer"))
DEBUG = str_to_bool(os.getenv("check_debug"))


## Setting bot handlers
# ==============================================================================
def setup_handlers(bot, config, limiter):
    echo_simple_commands(bot, limiter, config)
    echo_last_find(bot, config["seminars"])
    echo_keyboard_callback(bot, config, limiter)
    echo_notify(bot, config["states_file"])
    echo_responces(bot, config, limiter)
    echo_reply_from_chat(bot, config)


def run_bot(bot):
    while True:
        try:
            bot.polling(timeout=10, long_polling_timeout = 5)
        except Exception as e:
            text = f"Got an error while polling: {e}"
            print(text)
            if DEBUG:
                bot.send_message(ADMIN, text)
