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
import os, csv, re, queue, time, winsound, traceback, selenium
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

LINK = 'https://www.mdpi.com/search?sort=pubdate&page_count=100&year_from=1996&year_to=2024&advanced=(%40(title%2Cabstract%2Ckeywords%2Cauthors%2Caffiliations%2Cdoi%2Cfull_text%2Creferences)LEACH%40(title%2Cabstract%2Ckeywords%2Cauthors%2Caffiliations%2Cdoi%2Cfull_text%2Creferences)energy%40(title%2Cabstract%2Ckeywords%2Cauthors%2Caffiliations%2Cdoi%2Cfull_text%2Creferences)WSN)&view=abstract'

class MDPIPublisher():
    def __init__(self):
        self.MAXIMUM_PAGES = 55
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

        PATH = './result/MDPI/'
        if self.pageChoices == '1':
            self.FILE_NAME = os.path.join(PATH, f'MDPI_single_page_article_page_{self.pageArticle}_{np.random.randint(10000, 99999)}.csv')
        else:
            self.FILE_NAME = os.path.join(PATH, f'MDPI_multiple_page_article_page_{self.startPage}-{self.endPage}_{np.random.randint(10000, 99999)}.csv')
        
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
                    LINK + f'&page_no={i}' for i in range(self.pageArticle, self.pageArticle+1)
                ]
            else:
                LINK_ALL_PAGES = []
        else:
            if self.endPage < self.MAXIMUM_PAGES + 1:
                LINK_ALL_PAGES = [
                    LINK + f'&page_no={i}' for i in range(self.startPage, self.endPage+1)
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
                allow_all_cookies_button = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
                )

                # Click the 'Allow all cookies' button
                allow_all_cookies_button.click()
                driver.implicitly_wait(5)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                for i in soup:
                    self.total += len(i.find_all('div', class_='generic-item article-item'))
                driver.close()

                yield soup
                
            except:
                driver.close()
                print(f"Failed to retrieve {link}")

    def getInfoArticle(self, soups):
        for soup in soups:
            for article in soup.find_all('div', class_='generic-item article-item'):
                time.sleep(np.random.random() * 3)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                try:
                    self.trial += 1
                    link_article = str(article.find('div', class_='color-grey-dark'))
                    link_article = BeautifulSoup(link_article, 'html.parser')
                    link_article = link_article.get_text()
                    link_article = re.search(r'(https://doi\.org/\S+)', link_article).group(0)

                    article_type   = article.find('span', class_='label articletype').get_text()
                    article_title  = article.find('a', class_='title-link').get_text()
                    driver.get(link_article)
                    driver.implicitly_wait(5)
                    
                    html = driver.page_source
                    article_soup = BeautifulSoup(html, 'html.parser')
                    driver.close()
           
                    publication_title = article_soup.find('div', class_='bib-identity').find('em').get_text()

                    number_of_citation = article_soup.find('div', id='counts-wrapper').find('span', class_='count citations-number Var_ArticleMaxCitations')

                    if number_of_citation:
                        number_of_citation = number_of_citation.get_text()
                    else:
                        number_of_citation = 'none'
                
                    keywords = article_soup.find_all('div', class_='html-gwd-group')
                    if keywords != None:
                        for keyword in keywords:
                            keyword = keyword.find_all('a')
                            keyword = ','.join([i.get_text() for i in  keyword])
                        keywords = keyword
                    else:
                        keywords = 'none'

                    abstract = article_soup.find('section', class_="html-abstract") 
                    if abstract != None:
                        abstract = abstract.get_text()
                    else:
                        abstract = 'none'

                    publication_date = article_soup.find('div', class_='pubhistory').find_all('span')
                    if len(publication_date) == 3:
                        publication_date = publication_date[2].get_text()
                        publication_date = publication_date.replace('Accepted: ', '')
                    elif len(publication_date) == 4:
                        publication_date = publication_date[2].get_text()
                        publication_date = publication_date.replace('Published: ', '')
                    
                    publication_title = article_soup.find('div', class_='bib-identity').find('em').get_text()
                    
                    affiliation_info = {}
                    for i in article_soup.find_all('div', class_="affiliation"):
                        affiliation_info[i.find('sup').get_text()] = i.find('div', class_='affiliation-name').get_text()


                    affiliation_info.pop('*')
                    author_informations = article_soup.find('div', class_='art-authors hypothesis_container')
                    author_informations = author_informations.find_all('span', class_="inlineblock")

                    authors = ''
                    countries = ''
                    affiliations = ''
                    count = 0

                    for author_information in author_informations:
                        author = author_information.find('span', class_='sciprofiles-link__name').get_text()
                        index_affiliations = author_information.find('sup').get_text().split(',')
                        for index_affiliation in index_affiliations:
                            if index_affiliation != '*':
                                index_affiliation = index_affiliation.replace(" ", "")
                                affiliation = affiliation_info[index_affiliation]
                                country = affiliation.split(',')
                                countries += country[len(country)-1]

                                affiliations +=  f'({affiliation})'

                                affiliation = affiliation.split(', ')
                                country = affiliation[len(affiliation)-1]
                                countries       += ','
                                affiliations    += ','
                                    
                        authors += author
                        if count < len(author_informations)-1:
                            authors         += ','
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
                            'publisher'                     : 'MDPI',
                            'keyword'                       : keywords,
                            'abstract'                      : abstract,
                            'publish_date'                  : publication_date,
                            'publication_title'             : publication_title,
                            'authors'                       : authors,
                            'affiliations'                  : affiliations,
                            'countries'                     : countries
                        }
                    
                    for col in row_data.keys():
                        print(f"{col}:\n\t\t\t\t{row_data[col]}")

                    # Append new row to the CSV file directly
                    with open(self.FILE_NAME, 'a', newline='', encoding='utf-8') as file:
                        writer = DictWriter(file, fieldnames=self.information_keys)
                        writer.writerow(row_data)
                    
                    self.success += 1 
                    print("\n"*3)
                    print("=="*80)
                    print(f'''{100*(self.success/self.total):.2f} % | Sucess: {(self.success)} | Failed: {(self.failed)} | trial: {(self.trial)} | Total Article: {self.total}''')
                    print("=="*80)
                    print("\n"*1)
                    
                    
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
            print(f'Start collecting data from multiple MDPI article pages from {self.startPage}-{self.endPage}')
        else:
            print(f'\n\nStart collecting data from single MDPI article pages at {self.pageArticle}')

        links = self.getLinks()
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
