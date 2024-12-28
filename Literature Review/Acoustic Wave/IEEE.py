import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import argparse
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from csv import DictWriter
from threading import Thread
import os, csv, re, queue, time, winsound, traceback
import pycountry

chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--ignore-ssl-errors')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--incognito')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
chrome_options.add_argument("--start-maximized")
# chrome_options.add_argument("--headless")
caps = webdriver.DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = "normal"
service = Service(ChromeDriverManager().install())

LINK = 'https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&matchBoolean=true&queryText=(%22All%20Metadata%22:physics-informed)%20AND%20(%22All%20Metadata%22:wave)'

class IEEEPublisher():
    def __init__(self):
        self.MAXIMUM_PAGES = 10
        self.information_keys = [
            'title', 
            'link', 
            'number_of_citation', 
            'article_type', 
            'publisher', 
            'keyword', 
            'abstract', 
            'publish_date', 
            'publication_title', 
            'authors',  
            'affiliations', 
            'countries'
        ]
        self.success = 0
        self.failed = 0
        self.trial = 0
        self.total = 0
        self.pageArticle = 0
        self.startPage = 0
        self.endPage = 0

        self.pageChoices = str(input('Single page (1) or Multiple page (2)?: '))
        if self.pageChoices == '1':
            self.pageArticle   = int(input('Insert single page for article: '))
        elif self.pageChoices == '2':
            self.startPage   = int(input('Insert start page: '))
            self.endPage     = int(input('Insert end page: '))

        PATH = './result/IEEE/'
        if self.pageChoices == '1':
            self.FILE_NAME = os.path.join(PATH, f'IEEE_single_page_article_page_{self.pageArticle}_{np.random.randint(10000, 99999)}.csv')
        else:
            self.FILE_NAME = os.path.join(PATH, f'IEEE_multiple_page_article_page_{self.startPage}-{self.endPage}_{np.random.randint(10000, 99999)}.csv')
        
        with open(self.FILE_NAME, 'w', newline='', encoding='utf-8') as file:
            writer = DictWriter(file, fieldnames=self.information_keys)
            writer.writeheader()

    def getLinks(self):
        '''
            This link consist of Article and Conference paper        
        '''
        LINK_ALL_PAGES = [] 
        if self.pageChoices == '1':
            if self.pageArticle < self.MAXIMUM_PAGES + 1:
                LINK_ALL_PAGES = [
                    LINK + f'&startPage={i-1}' for i in range(self.pageArticle, self.pageArticle+1)
                ]
            else:
                LINK_ALL_PAGES = []
        else:
            print('asdad')
            if self.endPage < self.MAXIMUM_PAGES + 1:
                LINK_ALL_PAGES = [
                    LINK + f'&startPage={i-1}' for i in range(self.startPage, self.endPage+1)
                ]
            else:
                LINK_ALL_PAGES = []
        return LINK_ALL_PAGES
    
    def split_range(self, _range): #split a range to chunks
        if len(_range) > 7:
            parts = 5
        if ((len(_range) > 3) and (len(_range) < 7)):
            parts = 3
        else:
            parts = 1

        chunk_size = int(len(_range)/parts)
        chunks = [_range[x:x+chunk_size] for x in range(0, len(_range), chunk_size)]
        return chunks
    
    def getAllArticles(self, links):
        for link in links:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            try:
                driver.get(link)
                article_bodies = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "List-results-items"))
                )
                html = driver.page_source
                driver.close()
                soup = BeautifulSoup(html, 'html.parser')

                for i in soup:
                    self.total += len(i.find_all('div', class_='List-results-items'))
                yield soup
                
            except:
                driver.close()
                print(f"Failed to retrieve {link}")

    def getInfoArticle(self, soups):
        for soup in soups:
            for article in soup.find_all('div', class_='List-results-items'):
                # time.sleep(np.random.random() * 3)
                try:
                    self.trial += 1
                    link_article        = 'https://ieeexplore.ieee.org' + article.find('h3', class_='text-md-md-lh').find('a')['href']
                    article_information = article.find('div', class_='publisher-info-container').get_text()
                    article_information = article_information.split(' | ')
                    publication_date = article_information[0][:len('Year: 2022')]
                    if len(article_information) == 4:
                        # Journal article
                        article_type = article_information[2]
                    elif len(article_information) == 3:
                        # Conference
                        article_type = article_information[1]

                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.get(link_article)
                    title = WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="xplMainContentLandmark"]/div/xpl-document-details/div/div[1]/section[2]/div/xpl-document-header/section/div[2]/div/div/div[1]/div/div[1]/h1'))
                    )
                    button = driver.find_element(By.ID, 'authors')
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    button.click()

                    button = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="authors"]/div[1]/xpl-author-item/div/div[1]')))
                    html = driver.page_source
                    article_soup_author = BeautifulSoup(html, 'html.parser')

                    button = driver.find_element(By.ID, 'keywords')
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    button.click()

                    button = WebDriverWait(driver, 30).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="keywords"]/xpl-document-keyword-list/section/div/ul/li[1]/strong')))

                    html = driver.page_source
                    driver.close()

                    article_soup = BeautifulSoup(html, 'html.parser')

                    article_title = article_soup.find('h1', class_="document-title text-2xl-md-lh").get_text()
                    number_of_citation = article_soup.find('div', class_="document-banner-metric-container d-flex").find_all('button')
                    if number_of_citation:
                        if len(number_of_citation) > 1:
                            number_of_citation = number_of_citation[0].find('div', class_='document-banner-metric-count').get_text()
                        else:
                            number_of_citation = 'none'
                    else:
                        number_of_citation = 'none'

                    abstract = article_soup.find('div', class_="abstract-text row g-0")
                    abstract = abstract.find('div').get_text()[len('Abstract:')+1:]

                    publication_date = article_soup.find('div', class_='u-pb-1 doc-abstract-pubdate')

                    if publication_date != None:
                        publication_date = publication_date.get_text()
                    else:
                        publication_date = article_soup.find('div', class_='u-pb-1 doc-abstract-dateadded').get_text()
                        publication_date = publication_date.replace('Date Added to IEEE Xplore: ', '')
                        

                    publication_title = article_soup.find('a', class_='stats-document-abstract-publishedIn')

                    if publication_title != None:
                        publication_title = publication_title.get_text()
                    else:
                        publication_title = article_soup.find('div', class_='u-pb-1 stats-document-abstract-publishedIn').get_text().replace('Published in: ', '')

                    keywords = article_soup.find_all('ul', class_='u-mt-1 u-p-0 List--no-style List--inline')[2].get_text(strip=True)

                    authors = ''
                    countries = ''
                    affiliations = ''
                    count = 0
                    author_informations = article_soup_author.find_all('div', 'col-14-24')
                    
                    if len(author_informations) > 0:
                        n_author_informations = len(author_informations)//2
                        author_informations = author_informations[:n_author_informations]
                    else:
                        author_informations = article_soup_author.find_all('xpl-author-item')

                    for author_information in author_informations:
                        author = author_information.find('span').get_text()
                        authors += author_information.find('span').get_text()
                    
                        temp = author_information.find_all('div')[1].get_text()
                        affiliations += f"({temp.replace(author, '')})"
                        temp = temp.split(', ')
                        countries += temp[len(temp)-1]

                        if count < len(author_informations)-1:
                            authors         += ','
                            countries       += ','
                            affiliations    += ','
                        count += 1
                    
                    occurrences = countries.split(',')
                    found_countries = []

                    for country in pycountry.countries:
                        for occurrence in occurrences:
                            if country.name in occurrence:
                                found_countries.append(country.name)

                    countries = ','.join(found_countries)
                        

                    
                    row_data = {
                        'title'                         : article_title,
                        'link'                          : link_article,
                        'number_of_citation'            : number_of_citation,
                        'article_type'                  : article_type,
                        'publisher'                     : 'IEEE',
                        'keyword'                       : keywords,
                        'abstract'                      : abstract,
                        'publish_date'                  : publication_date,
                        'publication_title'             : publication_title,
                        'authors'                       : authors,
                        'affiliations'                  : affiliations,
                        'countries'                     : countries
                    }
                    
                    print("\n"*3)
                    print("=="*80)
                    print(f'''{100*(self.success/self.total):.2f} % | Sucess: {(self.success)} | Failed: {(self.failed)} | trial: {(self.trial)} | Total Article: {self.total}''')
                    print("=="*80)
                    print("\n"*1)
                    
                    for col in row_data.keys():
                        print(f"{col}:\n\t\t\t\t{row_data[col]}")

                    # Append new row to the CSV file directly
                    with open(self.FILE_NAME, 'a', newline='', encoding='utf-8') as file:
                        writer = DictWriter(file, fieldnames=self.information_keys)
                        writer.writerow(row_data)
                    
                    self.success += 1
                    
                except Exception as e:
                    self.failed += 1
                    print("\n"*3)
                    print("== ! Error ! =="*10)
                    print("\n"*1)
                    print(f"Failed to retrieve article: \n{article_title}\n{link_article}\n{e}")
                    traceback.print_exc()
                    print("\n"*3)
                    print("== ! Error ! =="*10)
                    print("\n"*1)
    
    def main(self, links):
        soups = self.getAllArticles(links)
        self.getInfoArticle(soups)

    def startCollect(self):
        if self.pageChoices == '2':
            print(f'Start collecting data from multiple IEEE article pages from {self.startPage}-{self.endPage}')
        else:
            print(f'\n\nStart collecting data from single IEEE article pages at {self.pageArticle}')

        links = self.getLinks()
        print(links)
        if self.pageChoices == '1':
            if (self.pageArticle < self.MAXIMUM_PAGES + 1):
                chunks = self.split_range(links)
                thread_workers = []
                for chunk in chunks:
                    t = Thread(target=self.main, args=(chunk, ))
                    thread_workers.append(t)
                    t.start()
                
                for t in thread_workers:
                    t.join()
        else:
            if ((self.endPage < self.MAXIMUM_PAGES + 1) and (self.pageArticle < self.MAXIMUM_PAGES  + 1)):
                chunks = self.split_range(links)
                thread_workers = []
                for chunk in chunks:
                    t = Thread(target=self.main, args=(chunk, ))
                    thread_workers.append(t)
                    t.start()
                
                for t in thread_workers:
                    t.join()
