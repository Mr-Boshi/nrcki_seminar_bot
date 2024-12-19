import os
import time
from telebot import TeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules.common import (
    load_json,
    dump_json,
    find_matching_indexes,
    string_to_number_list,
)
from bot.common import (
    check_new_entries,
    send_entries_from_one_seminar,
    send_entries_from_all_seminars,
)

# Load environment variables from the .env file
CHAT = int(os.getenv("chat_id"))
ADMIN = int(os.getenv("admin_id"))
MODERATORS = string_to_number_list(os.getenv("moderators_id"))
TIMER = int(os.getenv("timer"))
RATE = float(os.getenv("rate_limit"))


## Some general purpose functions
# ==============================================================================
# Creating keyboard for /last and /find commands
def setup_keyboard(keybord_options, prefix, num):
    keyboard = InlineKeyboardMarkup()
    for i in range(len(keybord_options)):
        keyboard.row(
            InlineKeyboardButton(
                keybord_options[i], callback_data=f"{prefix}_{i}_{num}"
            )
        )

    return keyboard


def command_extractor(text):
    try:
        # Extract the argument from the message text
        command, *args = text.split(" ")
        # Convert the argument to an integer
        arg = args[0]
    except (IndexError, ValueError):
        command = text
        arg = "1"

    command = command.replace("/", "")
    if "@" in command:
        command = command.split("@")[0]

    return command, arg


## Commands handlers
## =============================================================================
# Handle simple commands: /hello, /subscribe, /unsubscribe, /list_subs, /update
def echo_simple_commands(bot: TeleBot, limiter, config):
    @bot.message_handler(
        commands=[
            "start",
            "hello",
            "subscribe",
            "unsubscribe",
            "list_subs",
            "update",
            "info",
        ]
    )
    def simple_commands(message):
        subs_file = config["subs_file"]
        command, _ = command_extractor(message.text)
        subscriptions = load_json(subs_file)
        user_id = message.from_user.id

        # Handle greetengs
        if command in ["start", "hello"]:
            while not limiter.ready():
                time.sleep(0.5)

            text = "Приветствую! Я умею присылать сообщения о объявленных семинарах. \nЕще можно вывести сообщения о последних семинарах в чат. Для этого воспользуйтесь командой /last и выберите интересующие вас тематики. \nЕсли хочется больше семинаров, можно ввести /last N для вывода N последних семинаров. \nТакже я могу искать записи, содержащие интересующий вас текст. Для этого введите /find и свой поисковый запрос в следующем сообщении. \nЕсли вы хотите получать уведомления о новых семинарах в личные сообщения, воспользуйтесь командой /subscribe и /unsubscribe, чтобы отменить подписку."

            bot.reply_to(message, text)

        elif command == "subscribe":
            bot.reply_to(message, "Вы были успешно добавлены в список рассылки")
            # Set the state for the user
            if user_id not in subscriptions:
                subscriptions.append(user_id)
                dump_json(subscriptions, subs_file)

        elif command == "unsubscribe":
            bot.reply_to(message, "Больше уведомления вам приходить не будут")
            # Set the state for the user
            if user_id in subscriptions:
                subscriptions.remove(user_id)
                dump_json(subscriptions, subs_file)

        elif command == "list_subs":
            if user_id == ADMIN:
                if subscriptions == []:
                    text = "No subscriptions."
                else:
                    text = ", ".join(str(x) for x in subscriptions) + "."

                bot.reply_to(message, text=text)
            else:
                bot.reply_to(message, text="Для этого нужно быть админом бота.")

        elif command == "update":
            if user_id == ADMIN:
                reply = bot.reply_to(message, text="Есть, босс!")

                check_new_entries(config, bot, limiter, "outdated")

                bot.delete_message(chat_id=message.chat.id, message_id=reply.message_id)
                bot.reply_to(message, text="Сделано, босс!")
            else:
                bot.reply_to(message, text="Для этого нужно быть админом бота.")

        elif command == "info":
            if user_id == ADMIN:
                newsfile = config["news_file"]
                seminars = config["seminars"]
                news_modified = time.ctime(os.path.getmtime(newsfile))
                news = load_json(newsfile)
                text = f"Bot runs, news checked at {news_modified}, number of seminars stored: "
                if isinstance(news, list):
                    for seminar, name in zip(news, seminars):
                        line = '\n' + f"{name} -- {len(seminar)}, "
                        text += line
                    text = text[0:-2] + "."

                bot.reply_to(message, text=text)
            else:
                bot.reply_to(message, text="Для этого нужно быть админом бота.")


# Handle commands that require a keyboard: /last, /find
def echo_last_find(bot: TeleBot, keybord_options):
    @bot.message_handler(commands=["last", "find"])
    def find_last_keyboard(message):
        if message.chat.type == "private":
            command, num = command_extractor(message.text)

            # Sleep for 0.5 to avoid rate-limit
            time.sleep(0.5)

            keyboard = setup_keyboard(keybord_options, command, num)
            bot.send_message(
                message.chat.id,
                "Какие семинары вас интересуют?:",
                reply_markup=keyboard,
            )

        else:
            bot.send_message(
                message.chat.id,
                "Данная команда предназначена только для использования в личных сообщениях.",
            )


# Handle keyboard responce for /last and /find commands
def echo_keyboard_callback(bot: TeleBot, config, limiter):
    @bot.callback_query_handler(func=lambda message: True)
    def keyboard_callback_handler(call):
        # Answer the callback query
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        newsfile = config["news_file"]
        states_file = config["states_file"]
        seminars = config["seminars"]
        hashtags = config["hashtags"]

        # Extract selected index and entries range from call data
        command = call.data[:4]
        selected = int(call.data[5])
        entries = range(int(call.data[7:]))

        # Delete the original message
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            # Handle the error if the message does not exist
            print(f"Error deleting message: {e}")

        if command == "last":
            news = load_json(newsfile)
            info_text = "Последние семинары тематики '{}':"
            if selected == 4:
                entries = [entries, entries, entries, entries]
                send_entries_from_all_seminars(
                    bot, limiter, chat_id, seminars, entries, news, info_text, hashtags
                )
            else:
                hashtag = "\n" + hashtags[selected] + " " + hashtags[-1]
                info_text = info_text.format(seminars[selected])
                send_entries_from_one_seminar(
                    bot, limiter, chat_id, selected, entries, news, info_text, hashtag
                )

        elif command == "find":
            user_states = load_json(states_file, "dict")
            user_states[user_id] = "waiting_for_prompt" + "_" + str(selected)
            dump_json(user_states, states_file)
            bot.send_message(
                chat_id, "Пожалуйста, отправьте поисковый запрос следующим сообщением."
            )


# Handle /notify command
def echo_notify(bot: TeleBot, states_file):
    @bot.message_handler(commands=["notify"])
    def handle_notify(message):
        user_states = load_json(states_file, "dict")
        user_id = message.from_user.id
        authorised_users = MODERATORS + [ADMIN]

        # Set the state for the user
        if user_id in authorised_users:
            user_states[user_id] = "waiting_for_message"
            dump_json(user_states, states_file)
            bot.reply_to(
                message, "Пожалуйста, отправьте сообщение для пересылки в чат."
            )
        else:
            bot.reply_to(
                message, "Для этого нужно быть модератором или администратором бота."
            )


# Handling find-messages and forward-messages
def echo_responces(bot: TeleBot, config, limiter):
    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        seminars = config["seminars"]
        user_states = load_json(config["states_file"], "dict")
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        if user_id in user_states and "prompt" in user_states[user_id]:
            # Process the text provided by the user
            prompt = message.text
            selected = int(user_states[user_id][-1])

            # Clear the state for the user
            del user_states[user_id]
            dump_json(user_states, config["states_file"])

            if not prompt:
                bot.send_message(chat_id, "Ничего не найдено.")
                return

            news = load_json(config["news_file"])
            matching_indexes = find_matching_indexes(news, prompt)

            if selected == 4:
                if any(sublist for sublist in matching_indexes):
                    info_text = "Найдено среди семинаров '{}':"
                    print(matching_indexes)
                    send_entries_from_all_seminars(
                        bot,
                        limiter,
                        chat_id,
                        seminars,
                        matching_indexes,
                        news,
                        info_text,
                    )
                else:
                    bot.send_message(chat_id, "Ничего не найдено.")
            else:
                matching_indexes = matching_indexes[selected]
                if matching_indexes:
                    info_text = "Найдено среди семинаров '{}':".format(
                        seminars[selected]
                    )
                    send_entries_from_one_seminar(
                        bot,
                        limiter,
                        chat_id,
                        selected,
                        matching_indexes,
                        news,
                        info_text,
                    )
                else:
                    bot.send_message(chat_id, "Ничего не найдено.")

        elif user_id in user_states and "message" in user_states[user_id]:
            new_post = message.text

            # Clear the state for the user
            del user_states[user_id]

            bot.send_message(chat_id=CHAT, text=new_post)
            bot.send_message(chat_id=chat_id, text="Ваше сообщение отправлено.")
