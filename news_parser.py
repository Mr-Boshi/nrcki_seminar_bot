import requests
from bs4 import BeautifulSoup
import re

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
    
    return merged_paragraphs
    

