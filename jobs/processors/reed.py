from JobRanker.settings import SECRETS
from jobs.models import *
import requests
import json




def discover():
    max_pages = 5
    def reformat_date(date):
        date = date.split("/")
        date.reverse()
        return "-".join(date)
        
    page = 0
    while page < max_pages:
        r = requests.get("https://www.reed.co.uk/api/1.0/search?keywords=cyber+security+placement&resultsToSkip="+str(page*100), auth=(SECRETS["reed"],""))
        listings = json.loads(r.text)
        print("Total:",listings["totalResults"],"this:",len(listings["results"]))
        for l in listings["results"]:
            if l["employerName"].lower() not in Company.BLACKLIST:
                j = Job()
                j.title = l["jobTitle"]
                if l["minimumSalary"]:
                    j.salary = (l["minimumSalary"] + l["maximumSalary"]) / 2
                j.deadline = reformat_date(l["expirationDate"])
                j.posted = reformat_date(l["date"])
                j.description = l["jobDescription"]
                j.url = l["jobUrl"]
                j.scrape_method="reed"
                if j.quick_check():
                    j.company = Company.fetch(l["employerName"])
                    j.location = Location.fetch(l["locationName"])
                    if j.location.name != l["locationName"].lower():
                        j.precise_location = l["locationName"]
                    print(j)
                    j.save()
        page += 1
        if page*100 > listings["totalResults"]:
            break