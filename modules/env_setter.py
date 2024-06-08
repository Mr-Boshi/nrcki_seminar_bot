import os
from dotenv import load_dotenv

def load_env():
    # Load environment variables from the .env file
    load_dotenv()

    # Access the environment variables
    BOT_TOKEN  = os.getenv("bot_token")
    CHAT_ID    = os.getenv("chat_id")
    ADMIN_ID   = os.getenv("admin_id")
    TIMER      = int(os.getenv("timer"))
    RATE       = float(os.getenv("rate_limit"))
    SILENT_SRT = bool(os.getenv("silent_start"))

    return BOT_TOKEN, CHAT_ID, ADMIN_ID, TIMER, RATE, SILENT_SRT