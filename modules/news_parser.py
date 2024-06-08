import requests
from bs4 import BeautifulSoup
import re
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

# This is so  we would not create browsers every time we want to get a page
def create_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")

    # Initialize the Chrome driver with headless option
    browser = webdriver.Chrome(options=chrome_options)
    return browser

# Getting the content of the page with predefined browser and returning the pretty soup
def page_loader(browser, url):
    browser.get(url)
    page_content = browser.page_source    
    # Create a BeautifulSoup object
    return BeautifulSoup(page_content, 'html.parser')

#This thing looks for a link with a keyed str in href
def link_finder(browser, text : str, url = 'http://nrcki.ru'):
    page_soup = page_loader(browser, url)
    with open("output.html", "w", encoding="utf-8") as file:
        file.write(page_soup.prettify())
    for link in page_soup.find_all('a', href=True):
        if text in link.text:
            return link.get('href')
    
# This thing finds the links to seminars pages. Didn't want to hardcode them in case they change
def seminar_link_finder(browser = None):
    base_url = 'http://nrcki.ru'
    all_seminars_key = 'Семинары'
    pages_of_interest = ['Эксперименты на токамаках', 'Инженерно-физические проблемы термоядерных реакторов', 'Теория магнитного удержания плазмы', 'Инженерно-физический семинар по токамакам']

    if browser is None:
        browser = create_browser()

    all_seminars_page = link_finder(browser, all_seminars_key)
    seminar_pages = []
    for enrty in pages_of_interest:
        seminar_pages.append(base_url + link_finder(browser, enrty, base_url + all_seminars_page))
    return seminar_pages

# Function to find a class containing a specific string
def find_class_of_dev_with_news(tag):
    return tag.name == 'div' and 'Тема: ' in tag.text

def parse_seminars_soup(soup):
    date_pattern = r'\d{1,2}\s(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)'
    year_pattern = r'\d{4}\sгод'

    
    # Loop through each <p> tag inside the content div and extract the text
    seminars_div = soup.find(find_class_of_dev_with_news)
    # Initialize an empty list to store the text content of <p> tags
    paragraphs = []
    for p_tag in seminars_div.find_all('p'):
        paragraphs.append(p_tag.get_text())
    

    filtered_empty_paragraphs = [item for item in paragraphs if len(item) > 2]
    indexes_of_years = [index for index, string in enumerate(filtered_empty_paragraphs) if re.match(year_pattern, string)]
    filtered_paragraphs = filtered_empty_paragraphs[indexes_of_years[0]:]

    # print(indexes_of_years)
    
    indexes_of_dates = [index for index, string in enumerate(filtered_paragraphs) if re.match(date_pattern, string)]
    indexes_of_years = [index for index, string in enumerate(filtered_paragraphs) if re.match(year_pattern, string)]

    merged_paragraphs = []

    for index in range(len(filtered_paragraphs)):
        if index in indexes_of_years:
            prefix = filtered_paragraphs[index]
        elif index in indexes_of_dates:
            merged_paragraphs.append(prefix + ', ' + filtered_paragraphs[index])
        elif index >0:
            merged_paragraphs[-1] += '\n'
            merged_paragraphs[-1] += filtered_paragraphs[index]

    return merged_paragraphs


# Main function to check for updates and send notifications
def get_all_news():
    # Getting the URL of the webpage with seminars
    browser = create_browser()
    urls = seminar_link_finder(browser)

    news = []
    for url in urls:
        page_soup = page_loader(browser, url)
        news.append(parse_seminars_soup(page_soup))
    
    return news
