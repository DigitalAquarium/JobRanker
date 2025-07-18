import random

from adzuna_api import Adzuna_Api
from cv_library import CVLibrary
from glassdoor import Glassdoor
from gradcracker import GradCracker
from linkedin import Linkedin
from reed import Reed
from milkround import Milkround
from otta import Otta
from monster import Monster
from eFinancialCareers import EFinancialCareers
import playwright.async_api
from common import *
from targetjobs import TargetJobs

# TODO: glassdoor, Indeed. GRB??

# run_otta,run_cv_library,
'''async def main():
    tasks = []
    for func in [run_e_financial_careers,  run_reed,  run_gradcracker, run_linkedin]:
        tasks.append(asyncio.create_task(func()))
    for task in tasks:
        await task'''


async def wait_before(func,long=False, *args):
    await asyncio.sleep(random.uniform(1,5))
    if long:
        await asyncio.sleep(random.randrange(1, 10) * 25 - random.randint(20, 30))
    else:
        await asyncio.sleep(random.uniform(2,5))
    return await func(*args)


async def main():
    link_set = set()
    link_lock = asyncio.Lock()
    jm = JobManager()
    site_managers = [Adzuna_Api, Linkedin, Milkround, TargetJobs, GradCracker, CVLibrary, Otta, GradCracker, Reed, EFinancialCareers]#,Glassdoor,]
    search_terms = ["graduate cyber security", "graduate software engineer", "junior software developer"]
    task_list = []
    NUM_THREADS = 7
    sem = asyncio.Semaphore(NUM_THREADS)
    PAGE_SEARCH_LIMIT = 10
    for term in search_terms:
        for manager in site_managers:
            manager = manager()
            task_list.append(
                asyncio.create_task(
                    wait_before(manager.get_search_results,False, link_set, link_lock, sem, term, PAGE_SEARCH_LIMIT)))
    for manager in site_managers:
        manager = manager()
        task_list.append(
            asyncio.create_task(wait_before(manager.get_recommendations,False, link_set, link_lock, sem, PAGE_SEARCH_LIMIT)))
    await asyncio.gather(*task_list)
    print("Found", len(link_set), "jobs...")
    existing_link_set = await JobManager.db_link_set()
    link_set = link_set.difference(existing_link_set)
    print("Documenting", len(link_set), "jobs...")
    await asyncio.sleep(2)
    link_list = list(link_set)
    random.shuffle(link_list)
    for link in link_list:
        print(link.link)
    link_tasks = []
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    for link in link_list:
        link_tasks.append(asyncio.create_task(wait_before(link.scrape,True, browser, sem, jm)))
    await asyncio.gather(*link_tasks)
    return


asyncio.run(main())

job_list = list(jobs.jobs)
job_list.sort()
for j in job_list:
    print(j.title, "-", j.company + ":", j.rank, j.url)
# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(6000)
