from jobs.models import *
from jobs.processors.adzuna import Adzuna
from jobs.processors.reed import Reed
from jobs.processors.scraper import Scraper

default_processors = {"reed":Reed,"adzuna":Adzuna}
complex_processors = {"scraper":Scraper}
processors = default_processors | complex_processors

def discover():
    limit = 500

    search_terms = {("Cyber Security","placement"),("Embedded Security","graduate")}
    num_processors = len(default_processors)
    num_terms = len(search_terms)
    searches =  num_processors * num_terms
    for processor in default_processors.values():
        for term,level in search_terms:
            attempts = limit // searches
            added = processor.discover(term, attempts, level)
            print(processor, term, level, "lim="+str(attempts),"discovered:",added)
            limit -= added
            searches -= 1

def evaluate():
    limit = 100
    jobs = []
    print(Job.objects.filter(status="N").order_by("-rank"))
    for j in Job.objects.filter(status="N").order_by("-rank"):
        processors[j.scrape_method].evaluate(j)
        jobs.append(j)
        limit -= 1
        if limit <= 0:
            break
    Job.objects.bulk_update(jobs, ["title", "description", "description_html", "rank", "status", "salary", "deadline",
                                   "posted", "location", "company"])