from JobRanker.settings import SECRETS
from JobRanker.rate_limit_manager import Limiter
from .processor import Processor
from bs4 import BeautifulSoup
from jobs.models import *
import requests
import json

class Reed(Processor):
    l = Limiter(2000,"rph")
    endpoint = "https://www.reed.co.uk/api/1.0/"

    @staticmethod
    def discover(search_term,limit=500):
        max_pages = limit // 100
        def reformat_date(date):
            date = date.split("/")
            date.reverse()
            return "-".join(date)

        page = 0
        keywords = search_term.replace(" ","+")
        while page < max_pages:
            Reed.l.wait()
            r = requests.get(f"{Reed.endpoint}search?keywords={keywords}&resultsToSkip={str(page*100)}", auth=(SECRETS["reed"],""))
            listings = json.loads(r.text)
            print("Total:",listings["totalResults"],"this:",len(listings["results"]))
            for l in listings["results"]:
                if l["employerName"].lower() in Company.BLACKLIST:
                    print("emplyer be blacklisted")
                if l["employerName"].lower() not in Company.BLACKLIST:
                    j = Job()
                    j.title = l["jobTitle"]
                    j.set_salary(l["minimumSalary"],l["maximumSalary"])
                    if l["minimumSalary"]:
                        j.salary = (l["minimumSalary"] + l["maximumSalary"]) / 2
                    j.deadline = reformat_date(l["expirationDate"])
                    j.posted = reformat_date(l["date"])
                    j.description = l["jobDescription"]
                    j.url = l["jobUrl"]
                    j.scrape_method="reed"
                    if j.quick_check():
                        j.company = Company.fetch(l["employerName"])
                        j.location = PreciseLocation.fetch(l["locationName"])
                        print(j)
                        j.rank = j.get_word_rank()
                        j.save()
            page += 1
            if page*100 > listings["totalResults"]:
                break

    @staticmethod
    def evaluate(job) -> tuple[bool,str]:
        try:
            Reed.l.wait()
            jobID = job.url.split("/")[-1]
            r = requests.get(f"{Reed.endpoint}jobs/{jobID}",auth=(SECRETS["reed"], ""))
            r = json.loads(r.text)
            if r["jobUrl"] != r["externalUrl"]:
                job.url = r["externalUrl"]
            job.description_html = r["jobDescription"]
            soup = BeautifulSoup(job.description_html, "html.parser")
            job.description = soup.get_text()
            job.evaluate()
            print(job.title,"-",job.location,"-","£"+str(job.salary),"|",job.status,job.rank)
            return True, ""
        except:
            return False, "crawler"
        #job.save()

