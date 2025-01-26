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

LINK_BASE = 'https://link.springer.com/search/page/'
LINK_QUERY_ARTICLE = '?query=LEACH+AND+WSN+AND+ENERGY&date-facet-mode=between&showAll=true&facet-content-type="Article"'
LINK_QUERY_CONFERENCE = "?query=LEACH+AND+WSN+AND+ENERGY&date-facet-mode=between&showAll=true&facet-content-type=%22ConferencePaper%22"

class SpringerPublisher():
    def __init__(self):
        self.ARTICLE_MAXIMUM_PAGE = 78
        self.CONFERENCE_MAXIMUM_PAGE = 64
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
        self.pageConference = 0
        self.startPageArticle = 0
        self.endPageArticle = 0
        self.startPageConference = 0
        self.endPageConference = 0

        self.articleTypes = str(input('Only Collect Article Paper (1) Only Collect Conference Paper (2) Collect Both (3)?: '))
        self.pageChoices = str(input('Single page (1) or Multiple page (2)?: '))
        PATH = './result/Springer/'

        # Insert page for article and conference

        if (self.articleTypes == "1"):
            if self.pageChoices == '1':
                self.pageArticle   = int(input('Insert single page for article: '))
            elif self.pageChoices == '2':
                self.startPageArticle   = int(input('Insert start page for article: '))
                self.endPageArticle     = int(input('Insert end page for article: '))

        elif ((self.articleTypes == "2") or (self.articleTypes == "3")):
            if self.pageChoices == '1':
                self.pageConference   = int(input('Insert single page for Conference: '))
            elif self.pageChoices == '2':
                self.startPageConference   = int(input('Insert start page for Conference: '))
                self.endPageConference     = int(input('Insert end page for Conference: '))

        # Create a new file based on user input
        
        if (self.articleTypes == "1"):
            if self.pageChoices == '1':
                self.FILE_NAME = os.path.join(PATH, f'Springer_single_page_article{self.pageArticle}_{np.random.randint(10000, 99999)}.csv')
            elif self.pageChoices == '2':
                self.FILE_NAME = os.path.join(PATH, f'Springer_multiple_page_article{self.startPageArticle}-{self.endPageArticle}_{np.random.randint(10000, 99999)}.csv')

        elif (self.articleTypes == "2"):
            if self.pageChoices == '1':
                self.FILE_NAME = os.path.join(PATH, f'Springer_single_page_conference_{self.pageConference}_{np.random.randint(10000, 99999)}.csv')
            elif self.pageChoices == '2':
                self.FILE_NAME = os.path.join(PATH, f'Springer_multiple_page_conference_{self.startPageConference}-{self.endPageConference}_{np.random.randint(10000, 99999)}.csv')

        elif (self.articleTypes == "3"):
            if self.pageChoices == '1':
                self.FILE_NAME = os.path.join(PATH, f'Springer_single_page_article_{self.pageArticle}_and_conference_{self.pageConference}_{np.random.randint(10000, 99999)}.csv')
            elif self.pageChoices == '2':
                self.FILE_NAME = os.path.join(PATH, f'Springer_multiple_page_article_{self.startPageArticle}-{self.endPageArticle}_and_conference_{self.startPageConference}-{self.endPageConference}_{np.random.randint(10000, 99999)}.csv')

        with open(self.FILE_NAME, 'w', newline='', encoding='utf-8') as file:
            writer = DictWriter(file, fieldnames=self.information_keys)
            writer.writeheader()

    def getLinks(self):
        '''
            This link consist of Article and Conference paper        
        '''
        LINK_ALL_PAGES = {}  # Initialize as dictionary
        if ((self.articleTypes == "1") or (self.articleTypes == "3")):
            if self.pageChoices == '1':
                if self.pageArticle < self.ARTICLE_MAXIMUM_PAGE + 1:
                    LINK_ALL_PAGES['article'] = [
                        f'{LINK_BASE}{i}{LINK_QUERY_ARTICLE}' for i in range(self.pageArticle, self.pageArticle + 1)
                    ]
            elif self.pageChoices == '2':
                if self.endPageArticle < self.ARTICLE_MAXIMUM_PAGE + 1:
                    LINK_ALL_PAGES['article'] = [
                        f'{LINK_BASE}{i}{LINK_QUERY_ARTICLE}' for i in range(self.startPageArticle, self.endPageArticle)
                    ]
                    print([
                        f'{LINK_BASE}{i}{LINK_QUERY_ARTICLE}' for i in range(self.startPageArticle, self.endPageArticle)
                    ])

        if ((self.articleTypes == "2") or (self.articleTypes == "3")):
            if self.pageChoices == '1':
                if self.pageConference < self.CONFERENCE_MAXIMUM_PAGE + 1:
                    LINK_ALL_PAGES['conference'] = [
                        f'{LINK_BASE}{i}{LINK_QUERY_CONFERENCE}' for i in range(self.pageConference, self.pageConference + 1)
                    ]
            elif self.pageChoices == '2':
                if self.endPageConference < self.CONFERENCE_MAXIMUM_PAGE + 1:
                    LINK_ALL_PAGES['conference'] = [
                        f'{LINK_BASE}{i}{LINK_QUERY_CONFERENCE}' for i in range(self.startPageConference, self.endPageConference)
                    ]
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
    
    def getAllArticles(self, links, article_type):
        for link in links:
            driver = webdriver.Chrome(service=service, options=chrome_options)
            try:
                driver.get(link)
                allow_cookies_button = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-cc-action='accept']"))
                )
                allow_cookies_button.click()
                html = driver.page_source
                driver.close()
                soup = BeautifulSoup(html, 'html.parser')
                for i in soup:
                    self.total += len(i.find('ol', id='results-list').find_all('li'))
                yield soup
            except:
                driver.close()
                print(f"Failed to retrieve {link}")

    def getInfoArticle(self, soups, article_type):
        for soup in soups:
            for article in soup.find('ol', id='results-list').find_all('li'):
                try:
                    self.trial += 1
                    link_article = 'https://link.springer.com' + article.find('h2').find('a')['href']
                    publication_date   = int(article.find('span', class_='year').get_text()[-5:-1])
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.get(link_article)
                    allow_cookies_button = WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, "button[data-cc-action='accept']")
                        )
                    )
                    allow_cookies_button.click()
                    html = driver.page_source
                    driver.close()
                    article_soup = BeautifulSoup(html, 'html.parser')
                    article_title = article_soup.find('h1', class_="c-article-title").get_text()
                    number_of_citation = article_soup.find_all('p', class_="app-article-metrics-bar__count")
                    if number_of_citation:
                        if len(number_of_citation) > 1:
                            number_of_citation = re.search(r'\d+', number_of_citation[1].get_text()).group()
                        else:
                            number_of_citation = 'none'
                    else:
                        number_of_citation = 'none'

                    abstract = article_soup.find('div', class_="c-article-section__content").get_text()

                    publication_date = article_soup.find('time')
                    if publication_date == None:
                        publication_date   = int(article.find('span', class_='year').get_text()[-5:-1])
                    else:
                        publication_date = publication_date.get_text()
                    publication_title = article_soup.find('span', class_='app-article-masthead__journal-title').get_text()

                    
                    keywords = 'none'
                    if article_type == 'article':
                        keyword_elements = article_soup.find_all('ul', class_="c-article-subject-list")
                        
                        if keyword_elements:
                            # If there's more than one `ul`, select the second one, otherwise select the first one
                            keyword_elements = keyword_elements[1] if len(keyword_elements) > 1 else keyword_elements[0]

                            # Find all list items within the keyword elements
                            keyword_items = keyword_elements.find_all('li')
                            
                            # If keyword items are found, join them into a string
                            if keyword_items:
                                keywords = ','.join([keyword.get_text(strip=True) for keyword in keyword_items])


                    authors = ''
                    countries = ''
                    affiliations = ''
                    author_informations = article_soup.find('ol', class_='c-article-author-affiliation__list').find_all('li')

                    count = 0
                    for author_information in author_informations:
                        temp = author_information.find('p', class_='c-article-author-affiliation__address').get_text().replace(', ', ',')
                        affiliations += f'({temp})'
                        temp = temp.split(',')
                        print(temp[len(temp)-1])
                        countries += temp[len(temp)-1]
                        temp = author_information.find('p', class_='c-article-author-affiliation__authors-list').get_text()

                        if '&' in temp:
                            temp = temp.replace('&', ',').replace(u'\xa0', u'')
                        authors += temp
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
                        'publisher'                     : 'Springer',
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
    
    def main(self, links, article_type):
        soups = self.getAllArticles(links, article_type)
        self.getInfoArticle(soups, article_type)

    def startCollect(self):
        article_types = self.getLinks()
        for article_type in article_types.keys():
            if article_type == 'article': 
                if(
                    (self.pageArticle < self.ARTICLE_MAXIMUM_PAGE + 1) and 
                    (self.endPageArticle < self.ARTICLE_MAXIMUM_PAGE + 1)
                ):
                    chunks = self.split_range(article_types[article_type])
                    thread_workers = []
                    for chunk in chunks:
                        t = Thread(target=self.main, args=(chunk, article_type, ))
                        thread_workers.append(t)
                        t.start()
                    
                    for t in thread_workers:
                        t.join()

            if article_type == 'conference':
                if (
                    (self.endPageConference < self.CONFERENCE_MAXIMUM_PAGE + 1) and 
                    (self.pageConference < self.CONFERENCE_MAXIMUM_PAGE + 1)
                ):
                    chunks = self.split_range(article_types[article_type])
                    thread_workers = []
                    for chunk in chunks:
                        t = Thread(target=self.main, args=(chunk, article_type, ))
                        thread_workers.append(t)
                        t.start()
                
                    for t in thread_workers:
                        t.join()
