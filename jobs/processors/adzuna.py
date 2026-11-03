import random
from time import sleep

from JobRanker.settings import SECRETS
from JobRanker.rate_limit_manager import Limiter
from .processor import Processor
from bs4 import BeautifulSoup
from jobs.models import *
import requests
import json

class Adzuna(Processor):
    #l = Limiter(2000,"rph")

    @staticmethod
    def discover(search_term,limit=50):
        no_pages = limit//50
        print("Calling Adzuna API")
        for i in range(no_pages):
            api_call = f"https://api.adzuna.com/v1/api/jobs/gb/search/{i+1}" \
                       f"?app_id={SECRETS["adzuna_uid"]}" \
                       f"&app_key={SECRETS["adzuna_key"]}" \
                       f"&results_per_page=50" \
                       f"&what_or={search_term.replace(' ', '%20')}" \
                       f"&what_exclude=Senior" \
                       f"&salary_include_unknown=1"\
                       f"&category=graduate-jobs"
            # It'll only ever send max 50 per page.
            sleep(random.uniform(1, 3))
            response = requests.get(api_call)
            response = json.loads(response.content)
            for listing in response["results"]:
                if "display_name" in listing["company"] and listing["company"]["display_name"].lower() not in Company.BLACKLIST:
                    job = Job()
                    job.title = listing["title"]
                    job.description = listing["description"]
                    job.set_salary(listing["salary_min"], listing["salary_max"])
                    job.posted = listing["created"][:10]
                    job.url = "https://www.adzuna.co.uk/jobs/details/" + listing["id"]
                    job.scrape_method = "adzuna"
                    if job.quick_check():
                        if "display_name" in listing["company"]:
                            job.company = Company.fetch(listing["company"]['display_name'])
                        job.location = PreciseLocation.fetch(listing["location"]["area"][-1])
                        print(job)
                        job.rank = job.get_word_rank()
                        job.save()

            if i + 1 * 50 > response["count"]:
                break
        print("Adzuna API Documented for:",search_term)
        return

    @staticmethod
    def evaluate(job) -> tuple[bool,str]:
        pass
