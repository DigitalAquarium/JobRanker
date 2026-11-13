#Scraping Services:
# https://scrapfly.io/ * 1000
# https://www.firecrawl.dev/ * 1000
# https://geonode.com/products/scraper-api * 1500
# https://brightdata.com/products/web-scraper * 5000
# https://finedata.ai/blog/free-scraper-api-finedata-tier/ * 1000
from jobs.models import *

total_remaining=0    

class Scraper:
    # Interface for different methods of aquireing jobs!

    @staticmethod
    def discover(search_term:str,limit=200) -> int:
        # Discover should be the main scraping operation:
        # For some search term, look over all job listings (up to limit) for matches to this criteria
        # Save those jobs as complete / incomplete items to the database
        pass
    @staticmethod
    def evaluate(job:Job) -> tuple[bool,str]: #
        # This should be the main operation to finalise all details within a specific job
        # Open up the URL for the job and get the full information, after that save it to the db and return success.
        pass
