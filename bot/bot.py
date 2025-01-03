import os

from bot.command_handlers import (
    echo_simple_commands,
    echo_last_find,
    echo_keyboard_callback,
    echo_notify,
    echo_responces,
)


# Load environment variables from the .env file
CHAT = int(os.getenv("chat_id"))
ADMIN = int(os.getenv("admin_id"))
RATE = float(os.getenv("rate_limit"))
TIMER = int(os.getenv("timer"))


## Setting bot handlers
# ==============================================================================
def setup_handlers(bot, config, limiter):
    echo_simple_commands(bot, limiter, config)
    echo_last_find(bot, config["seminars"])
    echo_keyboard_callback(bot, config, limiter)
    echo_notify(bot, config["states_file"])
    echo_responces(bot, config, limiter)


def run_bot(bot):
    while True:
        try:
            bot.polling(timeout=10, long_polling_timeout = 5)
        except Exception as e:
            print(f"Got an error while polling: {e}")
