import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import argparse
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from csv import DictWriter
from threading import Thread
import os, csv, re, queue, time, winsound
from Springer import *
from IEEE import *
from ACM import *
from Wiley import *
from MDPI import *

def getScrappingInformation():
    publishers_dict = {'1': 'springer', '2': 'ieee', '3': 'acm', '4': 'wiley', '5': 'elsevier', '6': 'mdpi'}
    publishers = 'Springer (1), IEEE (2), ACM (3), Wiley (4), Elsevier (5), MDPI (6)'
    publisher_index = str(input(f'Choose publisher {publishers}: '))
    publisher = publishers_dict[publisher_index]
    
    if publisher == "acm" :
        return ACMPublisher()
    elif publisher == "springer" :
        return SpringerPublisher()
    elif publisher == "ieee" :
        return IEEEPublisher()
    elif publisher == "sage" :
        return SagePublisher()
    elif publisher == "wiley" :
        return WileyPublisher()
    elif publisher == "elsevier" :
        return ElsevierPublisher()
    elif publisher == "mdpi" :
        return MDPIPublisher()
    else:
        raise ValueError("The publisher you input is not supported | The page is for: (Springer, ACM, IEEE, Sage, Wiley, Publisher)")


def notify():
    frequency = 800  
    duration = 3000
    n = duration//1000
    t_sleep = 100
    for _ in range(n):
        winsound.Beep(frequency, (duration//n)//2 + t_sleep)
        time.sleep(t_sleep/1000)
        winsound.Beep(frequency // 2, (duration//n)//2 + t_sleep)
        time.sleep(t_sleep/1000)

if __name__ == '__main__':
    publisher = getScrappingInformation()
    publisher.startCollect() 
    notify()