import telebot, schedule, time, json, os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from dotenv import load_dotenv
from modules import get_all_news, load_env, RateLimiter
from threading import Thread


# Load environment variables from the .env file
load_dotenv()
BOT_TOKEN, CHAT, ADMIN, TIMER = load_env()
seminars = ['Отдел Т: Эксперименты на токамаках', 'Инженерно-физические проблемы термоядерных реакторов', 'Теория магнитного удержания плазмы', 'Инженерно-физический семинар по токамакам']
filedir = 'news'
filepath = os.path.join(filedir, 'news.json')
limiter = RateLimiter(0.5)

# Create the bot
bot = telebot.TeleBot(BOT_TOKEN)

# Handling greetings
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    while not limiter.ready():
        time.sleep(0.5)
    text = 'Приветствую! Я умею присылать последние новости о семинарах и искать среди них записи, содержащие интересующий вас текст.'
    bot.reply_to(message, text)

# ==============================================================================
# ==============================================================================
@bot.message_handler(commands=['find'])
def handle_find(message):
    try:
        # Extract the argument from the message text
        arg = message.text.split(' ')[1]
        # Convert the argument to an integer
        search = arg
    except (IndexError, ValueError):
        search = ''
    
    while not limiter.ready():
        time.sleep(0.5)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(seminars[0], callback_data='find_0' + '_' + search))
    keyboard.row(InlineKeyboardButton(seminars[1], callback_data='find_1' + '_' + search))
    keyboard.row(InlineKeyboardButton(seminars[2], callback_data='find_2' + '_' + search))
    keyboard.row(InlineKeyboardButton(seminars[3], callback_data='find_3' + '_' + search))
    keyboard.row(InlineKeyboardButton('Все!',      callback_data='find_4' + '_' + search))

    bot.send_message(message.chat.id, "Какие семинары вас интересуют?:", reply_markup=keyboard)


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

@bot.callback_query_handler(func=lambda call: call.data.startswith('last_'))
def last_callback_handler(call):
    bot.answer_callback_query(call.id)

    selected = int(call.data[5])
    entries  = int(call.data[7:])
    bot.delete_message(call.message.chat.id, call.message.message_id)
    news = load_news(filepath)

    if selected == 4:
        for i in range(4):
            bot.send_message(call.message.chat.id, f"Последние семинары в {seminars[i]}:")
            for j in range(entries):
                while not limiter.ready():
                    time.sleep(0.5)
                bot.send_message(call.message.chat.id, news[i][j])
    else:
        bot.send_message(call.message.chat.id, f"Последние семинары в {seminars[selected]}:")
        for i in range(entries):
            while not limiter.ready():
                time.sleep(0.5)
            bot.send_message(call.message.chat.id, news[selected][i])



@bot.callback_query_handler(func=lambda call: call.data.startswith('find_'))
def find_callback_handler(call):
    bot.answer_callback_query(call.id)

    selected = int(call.data[5])
    prompt = call.data[7:]
    bot.delete_message(call.message.chat.id, call.message.message_id)

    something_found = False
    if prompt != '':
        news = load_news(filepath)

        matching_indexes = [[],[],[],[]]
        for i in range(len(seminars)):
            sublist = news[i]
            for index, element in enumerate(sublist):
                if prompt in element:
                    matching_indexes[i].append(index)
                    something_found = True


    if something_found:
        if selected == 4:
            for i in range(4):
                founds = matching_indexes[i]
                if len(founds) > 0:
                    bot.send_message(call.message.chat.id, f"Найдено среди семинаров {seminars[i]}:")
                    for j in founds:
                        while not limiter.ready():
                            time.sleep(0.5)
                        bot.send_message(call.message.chat.id, news[i][j])
        else:
            founds = matching_indexes[selected]
            if len(founds) > 0:
                bot.send_message(call.message.chat.id, f"Найдено среди семинаров {seminars[selected]}:")
                for j in founds:
                    while not limiter.ready():
                        time.sleep(0.5)
                    bot.send_message(call.message.chat.id, news[selected][j])
    else:
        bot.send_message(call.message.chat.id, 'Ничего не найдено.')


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
        else:
            bot.send_message(chat_id=CHAT, text='Nothing new, working good')




# ==============================================================================
# ==============================================================================

update_news(filedir, filepath)
news = load_news(filepath)
bot.send_message(chat_id=CHAT, text='Бот запущен! Вот последние записи о семинарах:')
# for i in range(len(seminars)):
#     bot.send_message(chat_id=CHAT, text=seminars[i] + ': \n' + news[i][0])

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