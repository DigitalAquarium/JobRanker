#from jobs.models import *
from time import time

from bs4 import BeautifulSoup
from ddgs import DDGS

from jobs.processors.scraper import Scraper


#x = DDGS().extract("https://mbda.wd3.myworkdayjobs.com/en-US/MBDA-UK/job/Bristol/Product-Cyber-Security---Undergraduate-Placement-2027_R37719?source=flexa","text")
#DDGS().text("python programming", max_results=5)

class DuckDuck(Scraper):

    @staticmethod
    def discover(search_term:str,limit:int=200,level:str="") -> int:
        # Discover should be the main scraping operation:
        # For some search term, look over all job listings (up to limit) for matches to this criteria
        # Save those jobs as complete / incomplete items to the database
        # Return number of jobs added
        pass