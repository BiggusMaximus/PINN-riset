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

LINK = 'https://onlinelibrary.wiley.com/action/doSearch?AllField=LEACH+AND+WSN+AND+ENERGY&PubType=journal&pageSize=100'

class WileyPublisher():
    def __init__(self):
        self.MAXIMUM_PAGES = 9
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

        PATH = './result/Wiley/'
        if self.pageChoices == '1':
            self.FILE_NAME = os.path.join(PATH, f'Wiley_single_page_article_page_{self.pageArticle}_{np.random.randint(10000, 99999)}.csv')
        else:
            self.FILE_NAME = os.path.join(PATH, f'Wiley_multiple_page_article_page_{self.startPage}-{self.endPage}_{np.random.randint(10000, 99999)}.csv')
        
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
                WebDriverWait(driver, 30).until(
                    EC.visibility_of_element_located(
                        (
                            By.ID, "search-result"
                        )
                    )
                )
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                for i in soup:
                    self.total += len(i.find_all('li', class_='clearfix separator search__item bulkDownloadWrapper'))
                yield soup
                
            except:
                driver.close()
                print(f"Failed to retrieve {link}")

    def getInfoArticle(self, soups):
        for soup in soups:
            for article in soup.find_all('li', class_='clearfix separator search__item bulkDownloadWrapper'):
                time.sleep(np.random.random() * 3)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                try:
                    self.trial += 1
                    link_article        = 'https://onlinelibrary.wiley.com' + article.find('h2').find('a')['href']

                    driver.get(link_article)
                    driver.implicitly_wait(5)
                    
                    html = driver.page_source
                    article_soup = BeautifulSoup(html, 'html.parser')
                    driver.close()
                    
                    article_type = article_soup.find('span', class_='primary-heading').get_text()
                    article_title = article_soup.find('meta', attrs={'name': 'citation_title'})['content']

                    publication_title = article_soup.find('meta', attrs={'name': 'citation_journal_title'})['content']
                    # if publication_title != None:
                    #     publication_title = publication_title.get_text()
                    # else:
                    #     publication_title = article_soup.find('div', property='isPartOf')
                    #     publication_title = publication_title.get_text()
                            # if publication_title != None:                   

                    
                    number_of_citation = article_soup.find('div', class_='epub-section cited-by-count')

                    if number_of_citation:
                        number_of_citation = number_of_citation.find('a').get_text()
                    else:
                        number_of_citation = 'none'

                    abstract = article_soup.find('div', class_='article-section__content en main').find('p').get_text()

                    # if abstract != None:
                    #     abstract = abstract.get_text().replace("Abstract", '')
                    # else:
                    #     abstract = article_soup.find('section', id="author-abstract") 
                    #     abstract = abstract.get_text().replace("Abstract", '')
                        
                    publication_date = article_soup.find('span', class_='epub-date').get_text()

                    keywords = article_soup.find_all('meta', attrs={'name': 'citation_keywords'})
                    if keywords != None:
                        keywords = [meta['content'] for meta in keywords]
                        keywords = ','.join(keywords)
                    else:
                        keywords = 'none'

                    authors = ''
                    countries = ''
                    affiliations = ''

                    author = article_soup.find_all('meta', attrs={'name': 'citation_author'})
                    author = [meta['content'] for meta in author]
                    affiliation = article_soup.find_all('meta', attrs={'name': 'citation_author_institution'})
                    affiliation = [meta['content'] for meta in affiliation]
                    count = 0

                    for i in range(len(author)):
                        authors += author[i]
                        affiliations += f'({affiliation[i]})'

                        temp = affiliations.split(', ')
                        country = temp[len(temp)-1]
                        countries += country

                        if count < len(authors)-1:
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
                        'publisher'                     : 'Wiley',
                        'keyword'                       : keywords,
                        'abstract'                      : abstract,
                        'publish_date'                  : publication_date,
                        'publication_title'             : publication_title,
                        'authors'                       : authors,
                        'affiliations'                  : affiliations,
                        'countries'                     : countries
                    }
                    
                    self.success += 1
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
            print(f'Start collecting data from multiple Wiley article pages from {self.startPage}-{self.endPage}')
        else:
            print(f'\n\nStart collecting data from single Wiley article pages at {self.pageArticle}')

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
