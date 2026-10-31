from models import *
import urllib
import requests
import json




def discover():
    def reformat_date(date):
        date = date.split("/")
        date.reverse()
        return "-".join(date)
        
    jobs = []
    r = requests.get("https://www.reed.co.uk/api/1.0/search?keywords=cyber+security", auth=(settings.secrets["reed"],""))
    listings = json.loads(r.text)
    for l in listings["results"]:
        j = Job()
        j.company = Company.fetch(l["employerName"])
        j.location = Location.fetch(l["locationName"])
        if j.location.name != l["locationName"].lower():
            j.precise_location_name = l["locationName"]
        j.title = l["jobTitle"]
        if l["minimumSalary"]:
            j.salary = (l["minimumSalary"] + l["maximumSalary"]) / 2
        j.deadline = reformat_date(l["expirationDate"])
        j.posted = reformat_date(l["date"])
        j.description = l["jobDescription"]
        j.url = l["jobUrl"]
        j.scrape_method="reed"
        print(j)

discover()
