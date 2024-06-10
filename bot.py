import telebot, schedule, time, json, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from dotenv import load_dotenv
from modules import get_all_news, load_env, RateLimiter, pagagraphs_md
from threading import Thread


# Load environment variables from the .env file
load_dotenv()
BOT_TOKEN, CHAT, ADMIN, MODERATORS, TIMER, RATE, SILENT_SRT = load_env()

seminars = ['Отдел Т: Эксперименты на токамаках', 'Инженерно-физические проблемы термоядерных реакторов', 'Теория магнитного удержания плазмы', 'Инженерно-физический семинар по токамакам']
filedir = 'news'
filepath = os.path.join(filedir, 'news.json')
limiter = RateLimiter(1/RATE)

# Create the bot
bot = telebot.TeleBot(BOT_TOKEN)
user_states = {}

# Handling greetings
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    while not limiter.ready():
        time.sleep(0.5)
    text = 'Приветствую! Я умею присылать сообщения о объявленных семинарах. Еще можно вывести сообщения о последних семинарах в чат. Для этого воспользуйтесь командой `/last` и выберите интересующие вас тематики. Если хочется больше семинаров, можно ввести `/last N` для вывода N последних семинаров. \
            Также я могу искать записи, содержащие интересующий вас текст. Для этого введите `/find` и свой поисковый запрос в следующем сообщении.'
    bot.reply_to(message, text)

# ==============================================================================
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
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(seminars[0], callback_data='last_0' + '_' + num))
    keyboard.row(InlineKeyboardButton(seminars[1], callback_data='last_1' + '_' + num))
    keyboard.row(InlineKeyboardButton(seminars[2], callback_data='last_2' + '_' + num))
    keyboard.row(InlineKeyboardButton(seminars[3], callback_data='last_3' + '_' + num))
    keyboard.row(InlineKeyboardButton('Все!',      callback_data='last_4' + '_' + num))

    bot.send_message(message.chat.id, "Какие семинары вас интересуют?:", reply_markup=keyboard)

# ==============================================================================
# ==============================================================================
@bot.message_handler(commands=['find'])
def handle_find(message):
    user_id = message.from_user.id
    # Set the state for the user
    user_states[user_id] = 'waiting_for_prompt'
    bot.reply_to(message, "Пожалуйста, отправьте свой поисковый запрос в следующем сообщении.")

@bot.message_handler(commands=['notify'])
def handle_notify(message):
    user_id = message.from_user.id
    # Set the state for the user
    if user_id in MODERATORS + [ADMIN]:
        user_states[user_id] = 'waiting_for_message'
        bot.reply_to(message, "Пожалуйста, отправьте сообщение для пересылки в чат.")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id] == 'waiting_for_prompt':
        # Process the text provided by the user
        search = message.text
        
        # Clear the state for the user
        del user_states[user_id]
        
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton(seminars[0], callback_data='find_0' + '_' + search))
        keyboard.row(InlineKeyboardButton(seminars[1], callback_data='find_1' + '_' + search))
        keyboard.row(InlineKeyboardButton(seminars[2], callback_data='find_2' + '_' + search))
        keyboard.row(InlineKeyboardButton(seminars[3], callback_data='find_3' + '_' + search))
        keyboard.row(InlineKeyboardButton('Все!',      callback_data='find_4' + '_' + search))

        bot.send_message(message.chat.id, "Какие семинары вас интересуют?:", reply_markup=keyboard)

    elif user_id in user_states and user_states[user_id] == 'waiting_for_message':
        new_post = message.text
        
        # Clear the state for the user
        del user_states[user_id]

        bot.send_message(chat_id=CHAT, text=new_post)
        bot.send_message(chat_id=message.chat.id, text='Ваше сообщение отправлено.')

# ==============================================================================
# ==============================================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith('last_'))
def last_callback_handler(call):
    bot.answer_callback_query(call.id)

    selected = int(call.data[5])
    entries  = range(int(call.data[7:]))
    bot.delete_message(call.message.chat.id, call.message.message_id)
    news = load_news(filepath)

    if selected == 4:
        for i in range(4):
            info_text = f"Последние семинары в '{seminars[i]}':"
            send_news_for_seminar(call.message.chat.id, i, entries, news, info_text)
    else:
        info_text = f"Последние семинары в '{seminars[selected]}':"
        send_news_for_seminar(call.message.chat.id, selected, entries, news, info_text)



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


# ==============================================================================
# ==============================================================================

def update_news(filedir, filepath):
    # Ensure the directory exists
    os.makedirs(filedir, exist_ok=True)
    
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


def load_news(filepath):
    with open(filepath, "r") as json_file:
        news = json.load(json_file)
    return news

def check_new_entries(seminar_names):
    old_news = load_news(filepath)
    update_news(filedir, filepath)
    new_news = load_news(filepath)

    for i in range(len(seminar_names)):
        old_news_seminar = old_news[i]
        new_news_seminar = new_news[i]
       
        new_entries = len(new_news_seminar) - len(old_news_seminar)
        if new_entries == 1:
            bot.send_message(chat_id=CHAT, text='Внимание! Новый семинар.' + ' ' + seminar_names[i])
            bot.send_message(chat_id=CHAT, text=new_news_seminar[0])
        elif new_entries > 1:
            bot.send_message(chat_id=CHAT, text=f'Внимание! Объявлено {new_entries} новых семинаров.' + ' ' + seminar_names[i])
            for i in range(new_entries, 0, -1):
                bot.send_message(chat_id=CHAT, text=new_news_seminar[i-1])
            
        elif new_entries < 0:
            bot.send_message(chat_id=ADMIN, text='Number of entries got LOWER. Something is WRONG.')
        ## for debugging
        # else:
        #     bot.send_message(chat_id=CHAT, text='Nothing new, working good')




# ==============================================================================
# ==============================================================================

update_news(filedir, filepath)
news = load_news(filepath)
if not SILENT_SRT:
    bot.send_message(chat_id=CHAT, text='Бот запущен! Вот последние записи о семинарах:')
    for i in range(len(seminars)):
        bot.send_message(chat_id=CHAT, text=seminars[i] + ': \n' + news[i][0])

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