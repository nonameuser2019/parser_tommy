import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import random
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from model import *
from user_agent import generate_user_agent
import re


MAIN_URL = 'https://usa.tommy.com/ProductListingView'
db_engine = create_engine("sqlite:///calvin.db", echo=True)
basedir = os.path.abspath(os.path.dirname(__file__))
size_list = []
details_list = []
color_list = []
url_list = []
cat_url_list = []
cookie = {
    'sr_browser_id': '33df22be-572e-4904-ba40-0ad50c8bf097',
    'sr_pik_session_id': 'a93a676-c1cc-79d7-d8d1-e0f2e070f5ea',
    '__utma': '230066073.559163455.1579546275.1583593346.1583599172.13',
    '__utmb': '230066073.9.10.1583599172',
    '__utmc': '230066073',
    '__utmz': '230066073.1581354246.9.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
    '__wid': '496949504',
    '_ga': 'GA1.2.559163455.1579546275',
    '_px2': 'eyJ1IjoiNDdkNjNiNzAtNjA5NC0xMWVhLWE2NDQtZjFhZjM2YWNiMDBkIiwidiI6ImQ2MGQxMGEyLTNiYjUtMTFlYS1hMjE1LTAyNDJhYz'
           'EyMDAwNSIsInQiOjE1ODM2MDA1OTkzNTgsImgiOiJlMTMzMjExNGY0YjE4N2VkZDU0OThlNTY5ZDRkZjIzYjU3NTgwMTVjY2FjNGFlYjk0N'
           'DAyNzYwZWU1Y2ExMzJlIn0=',
    '_pxvid': 'eyJ1IjoiNDdkNjNiNzAtNjA5NC0xMWVhLWE2NDQtZjFhZjM2YWNiMDBkIiwidiI6ImQ2MGQxMGEyLTNiYjUtMTFlYS1hMjE1LTAyNDJh'
              'YzEyMDAwNSIsInQiOjE1ODM2MDA1OTkzNTgsImgiOiJlMTMzMjExNGY0YjE4N2VkZDU0OThlNTY5ZDRkZjIzYjU3NTgwMTVjY2FjNGFl'
              'Yjk0NDAyNzYwZWU1Y2ExMzJlIn0=',
    'sctr': '1|1583532000000',
    'ADRUM': 's=1583600052675&r=https%3A%2F%2Fusa.tommy.com%2Fen%2Fwomen%2Fnewarrivals-women%2Ficon-wide-leg-stripe-pant-ww28013%3F0',
    'JSESSIONID': '0000einWRcx7PVbTVe62TS9mlJv:1crovuh4f'

}

proxy = {'HTTPS': '157.245.138.230:8118'}
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'calvin.db')
HEADERS = {
    'User-Agent': generate_user_agent(device_type="desktop", os=('mac', 'linux')),
    'Accept':'*/*',
    'Cache-Control':'no-cache',
    'Host':'usa.tommy.com',
    'Accept-Encoding':'gzip, deflate, br',
    'Connection':'keep-alive',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,uz;q=0.6'}

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


engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()

def read_file_url():
    with open('input.txt', 'r') as file:
        for line in file:
            cat_url_list.append(line.strip('\n'))
    return cat_url_list


def get_html(url, payload=None):
    while True:
        time.sleep(random.randint(random.randint(6, 10), random.randint(12, 27)))
        html = requests.get(url, headers=HEADERS, proxies=proxy, params=payload, cookies=cookie)
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

def parser_content(html, image_list):
    # порсит все данные из карточки кроме фото, подумать разбить на несколько функций
    soup = BeautifulSoup(html.text, 'html.parser')
    link = html.url
    try:
        # имя товара
        product_name = soup.find('span', class_='productNameInner').text
    except:
        product_name = None

    try:
        # базовая цена(без скидки)
        price = soup.find('div', id='price_display').find_all('span')[0].text[1:]
    except:
        price = None
    try:
        # акционная цена
        price_sale = soup.find('div', id='price_display').find_all('span')[1].text[1:]
    except (IndexError, ValueError):
        price_sale = None

    try:
        # доступные размеры, на сайте все доступные размеры имеют класс available, поэтому парсим только их
        block_size = soup.find('ul', id='sizes').find_all('li')
        for li in block_size:
            if li['class'] == ['available']:
                size_list.append(li.find('span').text)
    except:
        print(f'Size {None}')

    try:
        # маркированый список Details с доп инфой снизу карточки
        details_group = soup.find('ul', class_='bullets')
        for details in details_group.find_all('li'):
            details_list.append(details.text)
    except:
        details_list.append('')

    try:
        # цветовая схема доступных цветов с сайта
        radiogrup = soup.find('ul', class_='productswatches')
        for color in radiogrup.find_all('li'):
            color_list.append(color['data-color-swatch'])
    except:
        color_list.append('')


    try:
        # парсим 1 цвет
        color = soup.find('ul', class_='productswatches').find('li', class_='active')['data-color-swatch']
    except:
        color = ''

    try:
        # айди обьявления
        universal_id = soup.find('div', class_='universalStyleNumber').find_all('span')[1].text
    except:
        universal_id = ''

    try:
        # парсим категорию товара
        category = soup.find('div', id='breadcrumb').find_all('a')[-2].text + ' ' + \
                   soup.find('div', id='breadcrumb').find_all('a')[-1].text
    except:
        category = ''
    count = 1
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        new_element = Tommy(product_name, price, price_sale, ','.join(size_list), color, ','.join(image_list),
                             ','.join(details_list), category, ','.join(color_list), link)
        session.add(new_element)
        session.commit()
    except:
        pass
    count += 1
    size_list.clear()
    color_list.clear()
    details_list.clear()



def create_dir_name():
    dir_name = 'images'
    try:
        os.mkdir(dir_name)
    except OSError:
        print('Папка существует')
    return dir_name


def chek_images():
    # проверяет номер последней фото в папке, и при запуске парсера след фото будет +1
    num_file = []
    last_image = 0
    try:
        file_list = os.listdir('images')
        for list in file_list:
            num_file.append(int(re.findall(r'\d*', list)[0]))
        num_file.sort()
        print(num_file[-1])
    except(IndexError):
        num_file.append(0)
    last_image = num_file[-1]
    return last_image


def get_photo(html, dir_name):
    count_photo = chek_images()
    image_list = []
    img_name = []
    soup = BeautifulSoup(html.content, 'html.parser')
    image_url = soup.find('div', class_='product_main_image').find('img')['data-src']
    image_list.append(image_url)
    image_list.append(image_url.replace('main', 'alternate1'))
    image_list.append(image_url.replace('main', 'alternate2'))
    image_list.append(image_url.replace('main', 'alternate3'))
    for img in image_list:
        try:
            photo_name = count_photo
            file_obj = requests.get(img, stream=True)
            if file_obj.status_code == 200:
                with open(dir_name+'/'+str(photo_name)+'.JPG', 'bw') as photo:
                    for chunk in file_obj.iter_content(8192):
                        photo.write(chunk)
                count_photo +=1
                img_name.append(str(photo_name))
        except:
            print('Error file_obj')
    return img_name


def get_url_category(html):
    # функция будет парсить в список url всех карточек в список(отсылает отдельные запросы)
    count = 0
    soup = BeautifulSoup(html.content, 'html.parser')
    page_count = soup.find('div', id='filterInfo')['data-total-count']
    all_page = int(page_count) // 30
    prod = soup.find('div', class_='grid').find_all('a', class_='productThumbnail')
    for i in prod:
        url_list.append(i['href'])
    category_id = soup.find('head').find('meta', {'name': 'pageId'})['content']
    payload.update({'categoryId': category_id})
    for page in range(1, all_page + 1):
        count += 30
        payload.update({'beginIndex': count})
        #response = requests.get(MAIN_URL, headers=HEADERS, proxies=proxy, params=payload)
        response = get_html(MAIN_URL, payload=payload)
        print(html.status_code)
        sp = BeautifulSoup(response.content, 'html.parser')
        try:
            prod = sp.find('div', class_='grid').find_all('a', class_='productThumbnail')
            for i in prod:
                url_list.append(i['href'])
        except:
            continue
    return url_list


def main():
    Session = sessionmaker(bind=db_engine)
    session = Session()
    dir_name = create_dir_name()
    cat_url_list = read_file_url()
    for cat_url in cat_url_list:
        html = get_html(cat_url)
        url_list = get_url_category(html)
    for url in url_list:
        card_exist = session.query
        html = get_html(url)
        image_list = get_photo(html, dir_name)
        parser_content(html, image_list)



if __name__ == '__main__':
    main()