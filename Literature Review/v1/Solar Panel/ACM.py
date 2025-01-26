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
chrome_options.add_argument("--headless")
caps = webdriver.DesiredCapabilities().CHROME
caps["pageLoadStrategy"] = "normal"
service = Service(ChromeDriverManager().install())

LINK = 'https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&field1=AllField&text1=LEACH+AND+WSN+AND+ENERGY&pageSize=50&expand=all'

class ACMPublisher():
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

        PATH = './result/ACM/'
        if self.pageChoices == '1':
            self.FILE_NAME = os.path.join(PATH, f'ACM_single_page_article_page_{self.pageArticle}_{np.random.randint(10000, 99999)}.csv')
        else:
            self.FILE_NAME = os.path.join(PATH, f'ACM_multiple_page_article_page_{self.startPage}-{self.endPage}_{np.random.randint(10000, 99999)}.csv')
        
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
                allow_all_cookies_button = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
                )

                # Click the 'Allow all cookies' button
                allow_all_cookies_button.click()
                html = driver.page_source
                driver.close()
                soup = BeautifulSoup(html, 'html.parser')

                for i in soup:
                    self.total += len(i.find_all('li', class_='search__item issue-item-container'))

                yield soup
                
            except:
                driver.close()
                print(f"Failed to retrieve {link}")

    def getInfoArticle(self, soups):
        for soup in soups:
            for article in soup.find_all('li', class_='search__item issue-item-container'):
                time.sleep(np.random.random() * 3)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                try:
                    self.trial += 1
                    link_article        = 'https://dl.acm.org' + article.find('h5', class_='issue-item__title').find('a')['href']
                    article_type       = article.find('div', class_='issue-heading').get_text()
                    article_title = article.find('h5', class_='issue-item__title').get_text()

                    driver.get(link_article)
                    driver.implicitly_wait(5)
                    allow_all_cookies_button = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.ID, "CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll"))
                    )
                    allow_all_cookies_button.click()
                    html = driver.page_source

                    article_soup = BeautifulSoup(html, 'html.parser')
                    publication_title = article_soup.find('div', class_='core-enumeration')
                    if publication_title != None:
                        publication_title = publication_title.get_text()
                    else:
                        publication_title = article_soup.find('div', property='isPartOf')
                        publication_title = publication_title.get_text()
                            # if publication_title != None:                   

                    # info_click = driver.find_element(By.XPATH, '//*[@id="article_collateral_menu"]/ul/li[1]/a')
                    # driver.execute_script("arguments[0].scrollIntoView(true);", info_click)

                    # info_click =  WebDriverWait(driver, 30).until(
                    #     EC.element_to_be_clickable(
                    #         (By.XPATH, '//*[@id="article_collateral_menu"]/ul/li[1]/a'))
                    # )
                    # info_click.click()

                    info_click = None

                    # Click on 'Info' section with error handling
                    try:
                        info_click = driver.find_element(By.XPATH, '//*[@id="article_collateral_menu"]/ul/li[1]/a')
                        driver.execute_script("arguments[0].scrollIntoView(true);", info_click)
                        
                        max_attempts = 3
                        for attempt in range(max_attempts):
                            try:
                                info_click = WebDriverWait(driver, 30).until(
                                    EC.element_to_be_clickable((By.XPATH, '//*[@id="article_collateral_menu"]/ul/li[1]/a'))
                                )
                                info_click.click()
                                break
                            except selenium.common.exceptions.ElementClickInterceptedException:
                                if attempt < max_attempts - 1:
                                    print("Retrying click after a short delay...")
                                    time.sleep(1)
                                else:
                                    print("Failed to click after multiple attempts.")
                                    raise

                    except selenium.common.exceptions.TimeoutException:
                        print("Element was not clickable within the given time.")
                        continue
                        
                    html = driver.page_source
                    article_soup_info = BeautifulSoup(html, 'html.parser')

                    contribution_button = driver.find_element(By.ID, 'tab-contributors-label')
                    contribution_button.click()

                    contribution_button =  WebDriverWait(driver, 30).until(
                        EC.visibility_of_element_located((By.ID, "tab-contributors"))
                    )
                    html = driver.page_source
                    article_soup_author = BeautifulSoup(html, 'html.parser')
                    driver.close()
                    number_of_citation = article_soup.find('span', class_="citation")

                    if number_of_citation:
                        number_of_citation = number_of_citation.get_text().replace('citation', '')
                    else:
                        number_of_citation = 'none'

                    abstract = article_soup.find('section', id="abstract") 

                    if abstract != None:
                        abstract = abstract.get_text().replace("Abstract", '')
                    else:
                        abstract = article_soup.find('section', id="author-abstract") 
                        abstract = abstract.get_text().replace("Abstract", '')
                        
                    publication_date = article_soup.find('span', class_='core-date-published').get_text()

                    keywords = article_soup_info.find('section', property='keywords')
                    if keywords != None:
                        keywords = keywords.find_all('li')
                        keywords = ','.join([keyword.get_text() for keyword in keywords])
                    else:
                        keywords = 'none'

                    author_informations = article_soup_author.find('div', class_='contributors').find_all('span', property="author")
                    authors = ''
                    countries = ''
                    affiliations = ''
                    count = 0

                    for author_information in author_informations:
                        author = author_information.find('a').get_text()
                        affiliation = author_information.find('div', class_='content').get_text()
                        affiliation = affiliation.replace('View Profile', '')

                        authors += author
                        affiliations += f'({affiliation})'

                        affiliation = affiliation.split(', ')
                        country = affiliation[len(affiliation)-1]
                        countries += country

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
                        'publisher'                     : 'ACM',
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
            print(f'Start collecting data from multiple ACM article pages from {self.startPage}-{self.endPage}')
        else:
            print(f'\n\nStart collecting data from single ACM article pages at {self.pageArticle}')

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
