from cv_library import CVLibrary
from gradcracker import GradCracker
from linkedin import Linkedin
from reed import Reed
from otta import Otta
from eFinancialCareers import EFinancialCareers
import playwright.async_api
from common import *

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
    site_managers = [Linkedin, GradCracker, CVLibrary, Otta, GradCracker, Reed,EFinancialCareers]
    search_terms = ["graduate software engineer", "junior software developer", "graduate cyber security"]
    task_list = []
    PAGE_SEARCH_LIMIT = 10
    for manager in site_managers:
        manager = manager()
        task_list.append(asyncio.create_task(manager.get_recommendations(link_set, link_lock, PAGE_SEARCH_LIMIT)))
        for term in search_terms:
            task_list.append(
                asyncio.create_task(manager.get_search_results(link_set, link_lock, term, PAGE_SEARCH_LIMIT)))
    await asyncio.gather(*task_list)
    for link in link_set:
        print(link.link)
    print("Documenting", len(link_set), "jobs...")
    link_tasks = []
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    NUM_THREADS = 5
    sem = asyncio.Semaphore(NUM_THREADS)
    for link in link_set:
        link_tasks.append(asyncio.create_task(link.scrape(browser, sem, jm)))
    await asyncio.gather(*link_tasks)


asyncio.run(main())

job_list = list(jobs.jobs)
job_list.sort()
for j in job_list:
    print(j.title, "-", j.company + ":", j.rank, j.url)
print("Documenting",len(job_list),"jobs...")
# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(6000)
