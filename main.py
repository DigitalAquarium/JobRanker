from cv_library import CVLibrary
from gradcracker import GradCracker
#from linkedin import *
from reed import Reed
from otta import Otta
#from eFinancialCareers import *
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
    site_managers = [CVLibrary, Otta,GradCracker,Reed]
    search_terms = ["graduate software engineer", "junior software developer", "graduate cyber security"]
    task_list = []
    PAGE_SEARCH_LIMIT = 3
    for manager in site_managers:
        manager = manager()
        task_list.append(asyncio.create_task(manager.get_recommendations(link_set, link_lock)))
        for term in search_terms:
            task_list.append(asyncio.create_task(manager.get_search_results(link_set, link_lock, term, PAGE_SEARCH_LIMIT)))
    await asyncio.gather(*task_list)
    for link in link_set:
        print(link.link)
    l = []
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    NUM_THREADS = 5
    sem = asyncio.Semaphore(NUM_THREADS)
    for x in link_set:
        l.append(asyncio.create_task(x.scrape(browser, sem, jm)))
    await asyncio.gather(*l)  # x.scrape(jm) for x in s


asyncio.run(main())

job_list = list(jobs.jobs)
job_list.sort()

for j in job_list:
    print(j.title, "-", j.company + ":", j.rank, j.url)

# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(6000)
