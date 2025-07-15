import random

from cv_library import CVLibrary
from gradcracker import GradCracker
from linkedin import Linkedin
from reed import Reed
from otta import Otta
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


async def main():
    link_set = set()
    link_lock = asyncio.Lock()
    jm = JobManager()
    site_managers = [TargetJobs]#Linkedin, GradCracker, CVLibrary, Otta, GradCracker, Reed, EFinancialCareers]
    search_terms = ["graduate software engineer", "junior software developer", "graduate cyber security"]
    task_list = []
    NUM_THREADS = 1
    sem = asyncio.Semaphore(NUM_THREADS)
    PAGE_SEARCH_LIMIT = 10
    for term in search_terms:
        for manager in site_managers:
            manager = manager()
            task_list.append(
                asyncio.create_task(manager.get_search_results(link_set, link_lock, sem, term, PAGE_SEARCH_LIMIT)))
    for manager in site_managers:
        manager = manager()
        task_list.append(asyncio.create_task(manager.get_recommendations(link_set, link_lock, sem, PAGE_SEARCH_LIMIT)))
    await asyncio.gather(*task_list)
    print("Found", len(link_set), "jobs...")
    existing_link_set = await JobManager.db_link_set()
    link_set = link_set.difference(existing_link_set)
    print("Documenting", len(link_set), "jobs...")
    await asyncio.sleep(2)
    link_list = list(link_set)
    random.shuffle(link_list)
    for link in link_set:
        print(link.link)
    link_tasks = []
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    for link in link_list:
        link_tasks.append(asyncio.create_task(link.scrape(browser, sem, jm)))
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
