import random
from time import sleep

from JobRanker.settings import SECRETS
from JobRanker.rate_limit_manager import Limiter
from .processor import Processor
import jobs.processors.scraper as scraper
from bs4 import BeautifulSoup
from jobs.models import *
import requests
import json

class Adzuna(Processor):
    #l = Limiter(2000,"rph")

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
                       f"{category}" # THIS MAY NOT ALWAYS BE DESIRABLE
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
                        data = url[1].split("&")
                        for d in data:
                            #https://www.adzuna.co.uk/jobs/land/ad/5944891607utm_source=1ef98434&v=144C4D970F28C7B98BCAC5AA3D5000C5BBCE6ED2
                            if d[:2] == "v=":
                                url = url[0] + "?" + d
                                break
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
        #Created With Heavy Help From ChatGPT
        url = job.url
        if url.split("/")[4] == "land": # Redirect URL
            if scraper.total_remaining > Adzuna.check_job_cache():
                return False,"scraper"
            else:
                url = url.split("?")
                job_id = url[0].split("/")
                job_id = job_id[-1]
                url = "https://www.adzuna.co.uk/jobs/details/"+job_id


        sleep(0.2 + random.random()/3 + random.betavariate(1,1)/3)
        with (requests.Session() as session):
            session.headers.update(Processor.headers)
            response = session.get(
                url,
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



