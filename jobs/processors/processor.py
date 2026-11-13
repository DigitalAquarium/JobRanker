from jobs.models import *
from time import time
class Processor:
    # Interface for different methods of getting jobs!
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",

        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",

        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",

        "Cache-Control": "max-age=0",
        "DNT": "1",

        "Priority": "u=0, i",

        "Sec-CH-UA": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',

        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",

        "Upgrade-Insecure-Requests": "1",
    }
    
    unevaluated_jobs_cache = {"count":Job.objects.filter(status="N").count(),"last_polled":time(),"remaining_checks":100}
    @staticmethod
    def check_job_cache():
        timeout = 120
        if Processor.unevaluated_jobs_cache["remaining_checks"] <= 0:
            Processor.unevaluated_jobs_cache = {"count":Job.objects.filter(status="N").count(),"last_polled":time(),"remaining_checks":100}
        elif time()-Processor.unevaluated_jobs_cache["last_polled"] > timeout:
            Processor.unevaluated_jobs_cache = {"count":Job.objects.filter(status="N").count(),"last_polled":time(),"remaining_checks":100}
        return Processor.unevaluated_jobs_cache["count"]

    @staticmethod
    def discover(search_term:str,limit:int=200,level:str="") -> int:
        # Discover should be the main scraping operation:
        # For some search term, look over all job listings (up to limit) for matches to this criteria
        # Save those jobs as complete / incomplete items to the database
        # Return number of jobs added
        pass
    @staticmethod
    def evaluate(job:Job) -> tuple[bool,str]: #
        # This should be the main operation to finalise all details within a specific job
        # Open up the URL for the job and get the full information, after that save it to the db and return success.
        pass
