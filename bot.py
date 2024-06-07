import telebot
import requests
from bs4 import BeautifulSoup
import re
import schedule
import time
from functools import partial

class seminar_info:
    def __init__(self, text):
        pass

    def parse_text(self, text):
        pass

# Main function to check for updates and send notifications
def get_all_news():
    # URL of the webpage to monitor
    url = 'http://nrcki.ru/product/nrcki/seminar-ehksperimenty-na-tokamakah-37157.shtml'
    date_pattern = r'\b\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\b'
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    seminars_div = soup.find('div', class_='product-full-desc-page')
    # Initialize an empty list to store the text content of <p> tags
    paragraphs = []

    # Loop through each <p> tag inside the content div and extract the text
    for p_tag in seminars_div.find_all('p'):
        paragraphs.append(p_tag.get_text())
    

    filtered_empty_paragraphs = [item for item in paragraphs if len(item) > 10]
    filtered_paragraphs = filtered_empty_paragraphs[2:]

    indexes_of_dates = [index for index, string in enumerate(filtered_paragraphs) if re.match(date_pattern, string)]

    merged_paragraphs = []

    for index in range(len(filtered_paragraphs)):
        if index in indexes_of_dates:
            merged_paragraphs.append(filtered_paragraphs[index])
        else:
            merged_paragraphs[-1] += '\n'
            merged_paragraphs[-1] += filtered_paragraphs[index]

    formated_paragraphs = []
    for paragraph in merged_paragraphs:
        modified_paragraph = paragraph.replace('"', '**')
        formated_paragraphs.append(modified_paragraph)
    
    return formated_paragraphs


BOT_TOKEN = '7287948971:AAH2WK2jVgHmhHwtK9E8GCWNjKDjaDPejno'

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")

# @bot.message_handler(commands=['get_last'])
# def send_last_enrty(message):
#     print(news[0])
#     bot.send_message(chat_id=293970271, text=news[0], parse_mode='Markdown')

news = get_all_news()

def check_new_entries(old_news):
    new_news = get_all_news()
    new_entries = len(new_news) - len(old_news)

    if new_entries == 1:
        bot.send_message(chat_id='-4112723585', text='Внимание! Объявлен новый семинар!')
        bot.send_message(chat_id='-4112723585', text=new_news[0])
    elif new_entries > 1:
        bot.send_message(chat_id='-4112723585', text=f'Внимание! Объявлено {new_entries} новых семинаров')
        for i in range(new_entries, 0, -1):
            bot.send_message(chat_id='-4112723585', text=new_news[i-1])
        
    elif new_entries < 0:
        bot.send_message(chat_id='293970271', text='Number of entries got LOWER')
    else:
        bot.send_message(chat_id='-4112723585', text='Nothing new, working good')

    old_news = new_news


# Schedule the hourly job to run every hour
schedule.every(10).seconds.do(lambda: check_new_entries(news))

# Main loop to run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)

# bot.infinity_polling()