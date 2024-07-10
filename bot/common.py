import time
import os
from modules.news_handler import pagagraphs_md, update_news
from modules.common import check_news_file_status, load_json

# Load environment variables from the .env file
CHAT  = int(os.getenv('chat_id'))
ADMIN = int(os.getenv('admin_id'))
RATE  = float(os.getenv('rate_limit'))
TIMER = int(os.getenv('timer'))


## Some general purpose functions
# ==============================================================================
# General send function, does not support info message
def send_single_entry(bot, limiter, chat_id, seminar_index, index, news, hashtags = None):
    if isinstance(index, int):
        while not limiter.ready():
            time.sleep(0.5)
        text = pagagraphs_md(news[seminar_index][index]) 
        if hashtags:
            text = text+ '\n' + hashtags
        bot.send_message(chat_id, text, parse_mode="HTML")

# Function to send entries with indexes from list in one seminar, supports external info message
def send_entries_from_one_seminar(bot, limiter, chat_id, seminar_index, indexes, news, info_text = None, hashtags = None):
    if indexes:
        if info_text is not None:
            bot.send_message(chat_id, info_text)
        for index in indexes:
            while not limiter.ready():
                time.sleep(0.5)
            send_single_entry(bot, limiter, chat_id, seminar_index, index, news, hashtags)

# Function to send entries with indexes from indexes_list structured like [[],[],[],[]] in all seminars, can format info message with seminar names
def send_entries_from_all_seminars(bot, limiter, chat_id, seminars, indexes_list, news, info_text = None, hashtags = None):
    for seminar_index, sublist in enumerate(indexes_list):
        if info_text:
            info_text = info_text.format(seminars[seminar_index])
        if hashtags:
            hashtag = '\n' + hashtags[seminar_index] + ' ' + hashtags[-1]
        send_entries_from_one_seminar(bot, limiter, chat_id, seminar_index, sublist, news, info_text, hashtag)



def check_new_entries(config, bot, limiter, file_status = None):
    seminars = config["seminars"]
    subsfile = config["subs_file"]
    filepath = config['news_file']
    linkfile = config['links_file']

    subscriptions = load_json(subsfile)
    
    if file_status is None:
        file_status = check_news_file_status(filepath)

    if file_status == "absent":
        print("News file not found, loading news.")
        update_news(filepath, linkfile)
        return

    elif file_status == "outdated":
        old_news = load_json(filepath)
        update_news(filepath, linkfile)
        new_news = load_json(filepath)

        for i in range(len(seminars)):
            old_news_seminar = old_news[i]
            new_news_seminar = new_news[i]

            new_entries = len(new_news_seminar) - len(old_news_seminar)
            chats = [CHAT] + subscriptions

            if new_entries != 0:
                notify_new_seminar(config, bot, limiter, chats, i, new_entries, new_news)
            # for debugging
            # else:
            #     bot.send_message(chat_id=ADMIN, text="Nothing new, working good")


def notify_new_seminar(config, bot, limiter, chats, seminar_index, new_entries, news):
    seminars = config["seminars"]
    hashtags = config["hashtags"]
    hashtag = '\n' + hashtags[seminar_index] + ' ' + hashtags[-1]
    if new_entries == 1:
        for chat in chats:
            info_text = f"Внимание! Новый семинар. {seminars[seminar_index]}"
            send_entries_from_one_seminar(bot, limiter, chat, seminar_index, range(new_entries), news, info_text, hashtag)
    elif new_entries > 1:
        for chat in chats:
            bot.send_message(
                chat_id=chat,
                text=f"Внимание! Объявлено {new_entries} новых семинаров."
                + " "
                + {seminars[seminar_index]},
            )
            send_entries_from_one_seminar(bot, limiter, chat, seminar_index, range(new_entries), news, info_text, hashtag)

    elif new_entries < 0:
        bot.send_message(
            chat_id=ADMIN,
            text="Number of entries got LOWER. Something is WRONG.",
        )
