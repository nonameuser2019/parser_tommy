import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import *

basedir = os.path.abspath(os.path.dirname(__file__))
db_engine = create_engine("sqlite:///calvin.db", echo=True)
proxy = {'HTTPS': '163.172.182.164:3128'}
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'calvin.db')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0',
    'authority': 'usa.tommy.com',
    'method': 'GET',
    'scheme': 'https',
    'Accept': 'text/html, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'adrum': 'isAjax:true',
    'Referer': 'https://usa.tommy.com/en/new-arrivals-men',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'x-requested-with': 'XMLHttpRequest'
}
cat_url_list = []
MAIN_URL = 'https://usa.tommy.com/ProductListingView'


payload = {
    'catalogId': '10551',
    'isHomeDepartment': 'false',
    'pageSize': '30',
    'disableProductCompare': 'true',
    'langId': '-1',
    'storeId': '10151', #CommerceSearch
    'categoryId': '', #pageId
    'beginIndex': '30',
    'minFacetCount': '1',
    'colorfacetselected': 'false',
    'cache': 'true'
}

def read_file_url():
    with open('input.txt', 'r') as file:
        for line in file:
            cat_url_list.append(line.strip('\n'))
    return cat_url_list


def get_html(url, payload=None):
    while True:
        time.sleep(random.randint(random.randint(6, 10), random.randint(12, 27)))
        html = requests.get(url, headers=HEADERS, proxies=proxy, params=payload)
        if html.status_code == 200:
            print(html.status_code)
            return html
        elif html.status_code == 403:
            print(html.status_code)
            print('weit to 600 sec')
            time.sleep(random.randint(600,800))
        else:
            time.sleep(random.randint(14, 27))
            print(html.status_code)
            continue


def get_url_category(html):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    count = 0
    soup = BeautifulSoup(html.content, 'html.parser')
    page_count = soup.find('div', id='filterInfo')['data-total-count']
    all_page = int(page_count) // 30
    prod = soup.find('div', class_='grid').find_all('div', class_='productCell')
    for i in prod:
        url = i.find('a', class_='productThumbnail')['href']
        try:
            full_price = i.find('div', id='price_display').find_all('span')[0].text[1:]
        except:
            full_price = None
        try:
            discount_price = i.find('div', id='price_display').find_all('span')[1].text[1:]
        except:
            discount_price = None

        new_element = TommyPrice(full_price, discount_price, url)
        session.add(new_element)
        session.commit()

    category_id = soup.find('head').find('meta', {'name': 'pageId'})['content']
    payload.update({'categoryId': category_id})
    for page in range(1, all_page + 1):
        count += 30
        payload.update({'beginIndex': count})
        # response = requests.get(MAIN_URL, headers=HEADERS, proxies=proxy, params=payload)
        response = get_html(MAIN_URL, payload=payload)
        print(html.status_code)
        sp = BeautifulSoup(response.content, 'html.parser')
        prod = soup.find('div', class_='grid').find_all('div', class_='productCell')
        for i in prod:
            url = i.find('a', class_='productThumbnail')['href']
            try:
                full_price = i.find('div', id='price_display').find_all('span')[0].text[1:]
            except:
                full_price = None
            try:
                discount_price = i.find('div', id='price_display').find_all('span')[1].text[1:]
            except:
                discount_price = None

            new_element = TommyPrice(full_price, discount_price, url)
            session.add(new_element)
            session.commit()


def main():
    cat_url_list = read_file_url()
    for cat_url in cat_url_list:
        html = get_html(cat_url)
        get_url_category(html)


if __name__ == '__main__':
    main()
