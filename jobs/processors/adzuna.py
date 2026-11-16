import json
import random
from time import sleep

import requests
from bs4 import BeautifulSoup

from JobRanker.settings import SECRETS
from jobs.models import *
from .processor import Processor


class Adzuna(Processor):
    #l = Limiter(2000,"rph")
    browser = None

    @staticmethod
    def discover(search_term,limit=50,level=""):
        tally = 0
        if level == "graduate":
            category = "&category=graduate-jobs"
        else:
            category = ""
            if level != "":
                search_term = search_term + " " + level
        no_pages = limit//50
        for i in range(no_pages):
            api_call = f"https://api.adzuna.com/v1/api/jobs/gb/search/{i+1}" \
                       f"?app_id={SECRETS["adzuna_uid"]}" \
                       f"&app_key={SECRETS["adzuna_key"]}" \
                       f"&results_per_page=50" \
                       f"&what_or={search_term.replace(' ', '%20')}" \
                       f"&what_exclude=Senior" \
                       f"&salary_include_unknown=1"\
                       f"{category}"
            # It'll only ever send max 50 per page.
            sleep(random.uniform(1, 3))
            response = requests.get(api_call)
            response = json.loads(response.content)
            for listing in response["results"]:
                if "display_name" in listing["company"] and listing["company"]["display_name"].lower() not in Company.BLACKLIST:
                    job = Job()
                    job.title = listing["title"]
                    job.description = listing["description"]
                    try:
                        job.set_salary(listing["salary_min"], listing["salary_max"])
                    except:
                        job.set_salary(listing["salary_min"])
                    job.posted = listing["created"][:10]

                    url = listing["redirect_url"]
                    url = url.split("?")
                    if url[0].split("/")[4] == "land":
                        url = url.split("?")
                        job_id = url[0].split("/")
                        job_id = job_id[-1]
                        url = "https://www.adzuna.co.uk/jobs/details/" + job_id
                    else:
                        url = url[0]
                    job.url = url

                    job.scrape_method = "adzuna"
                    if job.quick_check():
                        if "display_name" in listing["company"]:
                            job.company = Company.fetch(listing["company"]['display_name'])
                        job.location = PreciseLocation.fetch(listing["location"]["area"][-1])
                        print(job)
                        job.rank = job.get_word_rank()
                        job.save()
                        tally += 1

            if i + 1 * 50 > response["count"]:
                break
        return tally

    @staticmethod
    def evaluate(job) -> tuple[bool,str]:
        sleep(0.2 + random.random()/3 + random.betavariate(1,1)/3)
        print(job.url)
        if "land/ad" in job.url:
            url = job.url.split("?")
            job_id = url[0].split("/")
            job_id = job_id[-1]
            job.url = "https://www.adzuna.co.uk/jobs/details/" + job_id
        with (requests.Session() as session):
            session.headers.update(Processor.headers)
            response = session.get(
                job.url,
                timeout=(10, 30),
                allow_redirects=True
            )
            if response.status_code in [410,404]:
                print("410/404, Job gone")
                job.status = "X"
                job.save()
                return True,""
            elif response.status_code != 200:
                print("Status:", response.status_code)
                return False,"scraper"
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        details = None
        # Created With Heavy Help From ChatGPT
        # Find the embedded az_details JavaScript object
        for script in soup.find_all("script"):

            js = script.string or script.get_text()

            marker = 'window["az_details"]'
            position = js.find(marker)

            if position == -1:
                continue

            equals = js.find("=", position)

            if equals == -1:
                continue

            # Extract the JSON object following the equals sign
            raw = js[equals + 1:].lstrip()

            try:
                details, _ = json.JSONDecoder().raw_decode(raw)
                break
            except json.JSONDecodeError:
                continue

        if not details:
            print("Could not locate Adzuna job details")
            return False,"scraper"


        description_html = details.get("description", "")
        job.description_html = description_html

        # Convert HTML description into readable text
        description_text = BeautifulSoup(
            description_html,
            "html.parser"
        ).get_text("\n", strip=True)
        job.description = description_text

        job.evaluate()
        print(job.title,"-",str(job.location).split(" | ")[1],"-","£"+str(job.salary),"|",job.status,job.rank)
        return True, ""