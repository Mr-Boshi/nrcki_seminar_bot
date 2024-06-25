from modules.env_setter import load_env

from bot.command_handlers import (
    echo_simple_commands,
    echo_last_find,
    echo_keyboard_callback,
    echo_notify,
    echo_responces
)


# Load environment variables from the .env file
_, CHAT, ADMIN, _, TIMER, RATE, _, _, _, _ = load_env()

## Setting bot handlers
# ==============================================================================
def setup_handlers(bot, config, limiter):
    keybord_options = config["keybord_options"]
    states_file = config["states_file"]

    echo_simple_commands(bot, limiter, config)
    echo_last_find(bot, keybord_options)
    echo_keyboard_callback(bot, config, limiter)
    echo_notify(bot, states_file)
    echo_responces(bot, config, limiter)