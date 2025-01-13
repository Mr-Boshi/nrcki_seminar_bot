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
    resend_message,
)

# Load environment variables from the .env file
CHAT = int(os.getenv("chat_id"))
ADMIN = int(os.getenv("admin_id"))
MODERATORS = string_to_number_list(os.getenv("moderators_id"))
TIMER = int(os.getenv("timer"))
RATE = float(os.getenv("rate_limit"))
REQ_CHAT = int(os.getenv("request_target"))


## Some general purpose functions
# ==============================================================================
# Creating keyboard for /last, /find and /setcount commands
def setup_keyboard(keybord_options, prefix, num, include_all = True):
    keyboard = InlineKeyboardMarkup()
    for i in range(len(keybord_options)):
        keyboard.row(
            InlineKeyboardButton(
                keybord_options[i], callback_data=f"{prefix}_{i}_{num}"
            )
        )

    if include_all:
        keyboard.row(
            InlineKeyboardButton(
                'Все!', callback_data=f"{prefix}_{-1}_{num}"
            )
        )
    
    keyboard.row(
            InlineKeyboardButton(
                'Отмена', callback_data=f"{prefix}_{-10}_{num}"
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

            bot.reply_to(message, config["hello_text"])

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
                text = f"Бот запущен, новости проверены в {news_modified} UTC, записаное количество семинаров: "
                if isinstance(news, list):
                    for seminar, name in zip(news, seminars):
                        line = '\n' + f"{name} — {len(seminar)}, "
                        text += line
                    text = text[0:-2] + "."

                bot.reply_to(message, text=text)
            else:
                bot.reply_to(message, text="Для этого нужно быть админом бота.")


# Handle commands that require a keyboard: /last, /find and /setcount
def echo_last_find(bot: TeleBot, keybord_options):
    @bot.message_handler(commands=["last", "find", "setcount"])
    def find_last_keyboard(message):
        if message.chat.type == "private":
            user_id = message.from_user.id
            command, num = command_extractor(message.text)

            # Sleep for 0.5 to avoid rate-limit
            time.sleep(0.5)
            if command in ["last", "find"]:
                keyboard = setup_keyboard(keybord_options, command, num)
            
            elif command == "setcount" and user_id == ADMIN:
                keyboard = setup_keyboard(keybord_options, command, num, include_all = False)
            
            else:
                bot.reply_to(message, text="Для этого нужно быть админом бота.")
                return
            
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


# Handle keyboard responce for /last, /find and /setcount commands
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
        call_data = call.data.split('_')
        command = call_data[0]
        selected = int(call_data[1])
        entries = range(int(call_data[2]))

        # Delete the original message
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            # Handle the error if the message does not exist
            print(f"Error deleting message: {e}")

        if selected != -10:
            if command == "last":
                news = load_json(newsfile)
                info_text = "Последние семинары тематики '{}':"
                if selected == -1:
                    entries = [entries, entries, entries, entries]
                    send_entries_from_all_seminars(
                        config, bot, limiter, chat_id, seminars, entries, news, info_text, hashtags
                    )
                else:
                    hashtag = "\n" + hashtags[selected] + " " + hashtags[-1]
                    info_text = info_text.format(seminars[selected])
                    send_entries_from_one_seminar(
                        config, bot, limiter, chat_id, selected, entries, news, info_text, hashtag
                    )

            elif command == "find":
                user_states = load_json(states_file, "dict")
                user_states[user_id] = "waiting_for_prompt" + "_" + str(selected)
                dump_json(user_states, states_file)
                bot.send_message(
                    chat_id, "Пожалуйста, отправьте поисковый запрос следующим сообщением."
                )
            
            elif command == "setcount":
                user_states = load_json(states_file, "dict")
                user_states[user_id] = "waiting_for_counter" + "_" + str(selected)
                dump_json(user_states, states_file)
                bot.send_message(
                    chat_id, "Пожалуйста, отправьте номер последнего семинара следующим сообщением."
                )


# Handle /notify and /request command
def echo_notify(bot: TeleBot, states_file):
    @bot.message_handler(commands=["notify", "request"])
    def handle_forward(message):
        command, _ = command_extractor(message.text)
        user_states = load_json(states_file, "dict")
        user_id = message.from_user.id
        authorised_users = MODERATORS + [ADMIN]

        # Set the state for the user
        if command == 'notify':
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
        else:
            user_states[user_id] = "waiting_for_request"
            dump_json(user_states, states_file)
            bot.reply_to(
                message, "Пожалуйста, отправьте свой запрос."
            )


# Handling find-messages and forward-messages
def echo_responces(bot: TeleBot, config, limiter):
    @bot.message_handler(func=lambda message: True, chat_types=['private'], content_types = ['text', 'photo', 'document'])
    def handle_all_messages(message):
        seminars = config["seminars"]
        user_states = load_json(config["states_file"], "dict")
        user_id = str(message.from_user.id)
        chat_id = message.chat.id
        forwarded_file = config["forw_file"]
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

            if selected == -1:
                if any(sublist for sublist in matching_indexes):
                    info_text = "Найдено среди семинаров '{}':"
                    print(matching_indexes)
                    send_entries_from_all_seminars(
                        config,
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
                        config, 
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

        elif user_id in user_states and ("message" in user_states[user_id] or "request" in user_states[user_id]):

            if "message" in user_states[user_id]:
                resend_message(bot, message, CHAT)
                bot.send_message(chat_id=chat_id, text="Ваше сообщение отправлено.")
            else:
                forwarded_message = bot.forward_message(chat_id=REQ_CHAT, from_chat_id=message.chat.id, message_id=message.message_id)
                bot.send_message(chat_id=chat_id, text="Ваш запрос отправлен.")

                forwarded_messages = load_json(forwarded_file, "dict")
                forwarded_messages[forwarded_message.message_id] = message.chat.id
                dump_json(forwarded_messages, forwarded_file)

            # Clear the state for the user
            del user_states[user_id]
            dump_json(user_states, config["states_file"])
            
        
        elif user_id in user_states and "counter" in user_states[user_id]:
            try:
                new_counter = int(message.text)
                selected = int(user_states[user_id][-1])
            except Exception as e:
                print(f'Problem getting number from message: {e}')
                bot.send_message(chat_id=chat_id, text=f"Ошибка: {e}. Вы точно отправили число?")
                new_counter = None

            # Clear the state for the user
            del user_states[user_id]
            dump_json(user_states, config["states_file"])

            if new_counter is not None: 
                counters = load_json(config["nums_file"], "dict")
                counters[selected] = new_counter
                dump_json(counters, config["nums_file"])
                
                bot.send_message(chat_id=chat_id, text=f"Последнему семинару в '{seminars[selected]}' задан номер {new_counter}.")

def echo_reply_from_chat(bot: TeleBot, config):
    @bot.message_handler(func=lambda message: message.reply_to_message is not None, chat_types=['group', 'supergroup'], content_types = ['text', 'photo', 'document'])
    def handle_reply(message):
        if message.chat.id == REQ_CHAT:
            forwarded_file = config["forw_file"]
            # Check if the reply is to a forwarded message
            forwarded_messages = load_json(forwarded_file)
            replied_message = message.reply_to_message.message_id
            print(forwarded_messages)
            original_chat_id = forwarded_messages.get(str(replied_message))
            print(original_chat_id)

            if original_chat_id:
                resend_message(bot, message, original_chat_id)
            else:
                bot.send_message(chat_id=REQ_CHAT, text=f"Не найден отправитель сообщения с id {replied_message}.")