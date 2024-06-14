import telebot, schedule, time, json, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from dotenv import load_dotenv
from modules import get_all_news, load_env, RateLimiter, pagagraphs_md
from threading import Thread


# Load environment variables from the .env file
load_dotenv()
BOT_TOKEN, CHAT, ADMIN, MODERATORS, TIMER, RATE, SILENT_SRT = load_env()

seminars = ['Отдел Т: Эксперименты на токамаках', 'Инженерно-физические проблемы термоядерных реакторов', 'Теория магнитного удержания плазмы', 'Инженерно-физический семинар по токамакам']
keybord_options = seminars + ['Все!']
# Dir name and file name are static so there is no need to forward them to any functions
filedir = 'news'
os.makedirs(filedir, exist_ok=True)
filepath = os.path.join(filedir, 'news.json')
subsfile = os.path.join(filedir, 'subscribtions.json')

# Create the bot and some sotrage variables
limiter = RateLimiter(1/RATE)
user_states = {}
subscriptions = []
bot = telebot.TeleBot(BOT_TOKEN)

# Handling greetings
# ==============================================================================
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    while not limiter.ready():
        time.sleep(0.5)
    text = 'Приветствую! Я умею присылать сообщения о объявленных семинарах. Еще можно вывести сообщения о последних семинарах в чат. Для этого воспользуйтесь командой `/last` и выберите интересующие вас тематики. Если хочется больше семинаров, можно ввести `/last N` для вывода N последних семинаров. \
            Также я могу искать записи, содержащие интересующий вас текст. Для этого введите `/find` и свой поисковый запрос в следующем сообщении.'
    bot.reply_to(message, text)

# Setting the keyboard to choose the seminar
# ==============================================================================
def setup_keyboard(prefix, num):
    keyboard = InlineKeyboardMarkup()
    for i in range(len(keybord_options)):
        keyboard.row(InlineKeyboardButton(keybord_options[i], callback_data=f'{prefix}_{i}_{num}'))
  
    return keyboard

# Handling '/last' request
# ==============================================================================
@bot.message_handler(commands=['last'])
def handle_last(message):
    try:
        # Extract the argument from the message text
        arg = message.text.split(' ')[1]
        # Convert the argument to an integer
        num = arg
    except (IndexError, ValueError):
        num = '1'
    
    while not limiter.ready():
        time.sleep(0.5)
        
    keyboard = setup_keyboard('last', num)
    bot.send_message(message.chat.id, "Какие семинары вас интересуют?:", reply_markup=keyboard)

# Handling '/find' request
# ==============================================================================
@bot.message_handler(commands=['find'])
def handle_find(message):
    user_id = message.from_user.id
    # Set the state for the user
    user_states[user_id] = 'waiting_for_prompt'
    bot.reply_to(message, "Пожалуйста, отправьте свой поисковый запрос в следующем сообщении.")

# Handling '/notify' request
# ==============================================================================
@bot.message_handler(commands=['notify'])
def handle_notify(message):
    user_id = message.from_user.id
    # Set the state for the user
    if user_id in MODERATORS + [ADMIN]:
        user_states[user_id] = 'waiting_for_message'
        bot.reply_to(message, "Пожалуйста, отправьте сообщение для пересылки в чат.")

# Handling '/subscribe' request
# ==============================================================================
@bot.message_handler(commands=['subscribe'])
def handle_notify(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Вы были успешно добавлены в список рассылки")
    # Set the state for the user
    if not user_id in subscriptions:
        subscriptions.append(user_id)
        with open(subsfile, "w") as json_file:
            json.dump(subscriptions, json_file)

# Handling '/unsubscribe' request
# ==============================================================================
@bot.message_handler(commands=['unsubscribe'])
def handle_notify(message):
    user_id = message.from_user.id
    bot.reply_to(message, "Больше уведомления вам приходить не будут")
    # Set the state for the user
    if user_id in subscriptions:
        subscriptions.remove(user_id)
        with open(subsfile, "w") as json_file:
            json.dump(subscriptions, json_file)

# Handling find-messages and forward-messages
# ==============================================================================
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'waiting_for_prompt':
        # Process the text provided by the user
        search = message.text
        
        # Clear the state for the user
        del user_states[user_id]
        keyboard = setup_keyboard('find', search)
        bot.send_message(message.chat.id, "Какие семинары вас интересуют?:", reply_markup=keyboard)

    elif user_id in user_states and user_states[user_id] == 'waiting_for_message':
        new_post = message.text
        
        # Clear the state for the user
        del user_states[user_id]

        bot.send_message(chat_id=CHAT, text=new_post)
        bot.send_message(chat_id=message.chat.id, text='Ваше сообщение отправлено.')

# Handling responses from the keyboard
# ==============================================================================
# ==============================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('last_'))
def last_callback_handler(call):
    # Answer the callback query
    bot.answer_callback_query(call.id)

    # Extract selected index and entries range from call data
    selected = int(call.data[5])
    entries = range(int(call.data[7:]))

    # Delete the original message
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass

    # Load news data
    news = load_news()

    # Define the info text template
    info_text_template = "Последние семинары в '{}':"

    # If all seminars are selected
    if selected == 4:
        for i in range(4):
            info_text = info_text_template.format(seminars[i])
            send_news_for_seminar(call.message.chat.id, i, entries, news, info_text)
    # If one seminar is selected
    else:
        info_text = info_text_template.format(seminars[selected])
        send_news_for_seminar(call.message.chat.id, selected, entries, news, info_text)

# ==============================================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith('find_'))
def find_callback_handler(call):
    bot.answer_callback_query(call.id)

    selected = int(call.data[5])
    prompt = call.data[7:]
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    bot.delete_message(chat_id, message_id)

    if not prompt:
        bot.send_message(chat_id, 'Ничего не найдено.')
        return

    news = load_news(filepath)
    matching_indexes = find_matching_indexes(news, prompt)

    if any(matching_indexes):
        send_matching_news(chat_id, selected, matching_indexes, news)
    else:
        bot.send_message(chat_id, 'Ничего не найдено.')

def find_matching_indexes(news, prompt):
    matching_indexes = [[] for _ in range(4)]
    prompt_lower = prompt.lower()  # Convert the prompt to lowercase
    
    for i, sublist in enumerate(news):
        for index, element in enumerate(sublist):
            if prompt_lower in element.lower():  # Convert element to lowercase for comparison
                matching_indexes[i].append(index)
    return matching_indexes

def send_matching_news(chat_id, selected, matching_indexes, news):
    if selected == 4:
        for i in range(4):
            info_text = f"Найдено среди семинаров '{seminars[i]}':"
            send_news_for_seminar(chat_id, i, matching_indexes[i], news, info_text)
    else:
        info_text = f"Найдено среди семинаров '{seminars[selected]}':"
        send_news_for_seminar(chat_id, selected, matching_indexes[selected], news, info_text)

def send_news_for_seminar(chat_id, seminar_index, founds, news, info_text = None):
    if founds:
        if info_text:
            bot.send_message(chat_id, info_text)
        for index in founds:
            while not limiter.ready():
                time.sleep(0.5)
            bot.send_message(chat_id, pagagraphs_md(news[seminar_index][index]), parse_mode='HTML')


# Background news checking functions
# ==============================================================================
# ==============================================================================

def update_news():
    # Calculate the time difference in hours if the file exists
    if os.path.exists(filepath):
        last_modified_time = os.path.getmtime(filepath)
        current_time = time.time()
        time_diff_hours = (current_time - last_modified_time) / 3600
    else:
        time_diff_hours = float('inf')  # Use infinity to ensure news is fetched if file doesn't exist
    
    # Fetch news if the file is older than 1 hour or doesn't exist
    if time_diff_hours >= 0.75:
        news = get_all_news()
        with open(filepath, "w") as json_file:
            json.dump(news, json_file)


def load_news():
    with open(filepath, "r") as json_file:
        news = json.load(json_file)
    return news

def check_new_entries():
    if not os.path.exists(filepath):
        update_news()
    
    old_news = load_news()
    update_news()
    new_news = load_news()

    for i in range(len(seminars)):
        old_news_seminar = old_news[i]
        new_news_seminar = new_news[i]
       
        new_entries = len(new_news_seminar) - len(old_news_seminar)
        chats = [CHAT] +  subscriptions
        if new_entries == 1:
            for chat in chats:
                info_text = f'Внимание! Новый семинар. {seminars[i]}'
                send_news_for_seminar(chat, i, 0, new_news_seminar, info_text)
        elif new_entries > 1:
            for chat in chats:
                bot.send_message(chat_id=chat, text=f'Внимание! Объявлено {new_entries} новых семинаров.' + ' ' + seminars[i])
                for j in range(new_entries, 0, -1):
                    send_news_for_seminar(chat, i, j-1, new_news_seminar)
            
        elif new_entries < 0:
            bot.send_message(chat_id=ADMIN, text='Number of entries got LOWER. Something is WRONG.')
        # for debugging
        # else:
        #     bot.send_message(chat_id=CHAT, text='Nothing new, working good')


# Loading list of subscribed users:
# ==============================================================================
def load_subscribtions():
    if os.path.exists(subsfile):
        with open(subsfile, "r") as json_file:
            subs = json.load(json_file)
        return subs
    else:
        return []


# Preparation before main loop
# ==============================================================================
# ==============================================================================
subscriptions = load_subscribtions()
check_new_entries()
print(SILENT_SRT)
if not SILENT_SRT:
    bot.send_message(chat_id=ADMIN, text='Бот запущен!')

# Schedule the hourly job to run every hour
schedule.every(TIMER).hours.do(lambda: check_new_entries(seminars))

# ==============================================================================
# ==============================================================================

# Main loop to run the scheduler
def run_bot():
    bot.infinity_polling()


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# ==============================================================================
# ==============================================================================

if __name__ == '__main__':
    Thread(target=run_bot).start()
    Thread(target=run_schedule).start()