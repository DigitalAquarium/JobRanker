import random

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class TargetJobsLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).inner_text()
        location = "United Kingdom"
        location_candidates = await page.locator("xpath=//*[@id='main-content']/main/div[2]/div[2]/div/div/div/p[2]").all()
        for location_candidate in location_candidates:
            cand_txt = await location_candidate.inner_text()
            if not any([i in cand_txt for i in "0123456789"]):
                location = cand_txt
        try:
            company = await page.locator("xpath=//*[@id='main-content']/main/div[1]/div/div/div[1]/div[1]/div[2]").inner_text(timeout=5000)
        except:
            company = await page.locator(
                'xpath=//*[@id="main-content"]/main/div[1]/div/div/div[1]/div[1]/div/a').inner_text(timeout=5000)
        description = await page.locator("xpath=//*[@id='main-content']/main/div[2]/div[1]/div[2]").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class TargetJobs(JobBoardScraper):
    site_url = "https://targetjobs.co.uk"
    site_name = "TargetJobs"
    next_first = True

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(random.random() * 3)
        job_list_container = page.locator(".space-y-3 > div")
        for job in await job_list_container.locator("> a").all():
            text = await job.get_by_role("heading", level=3).inner_text()
            href = await job.get_attribute("href")
            company = await job.locator(
                "> div > div.col-span-2.flex.flex-col.justify-center.\!mt-0.col-span-2.gap-y-1 > p").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(TargetJobsLink(self.site_url + href, self.site_name))
        return

    def get_next_button(self, page):
        return page.get_by_role("button", name="Load More")

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(1+random.random()*3)
        await page.goto("https://targetjobs.co.uk/search/jobs?force=true")

        await page.get_by_role("textbox", name="Search Jobs & opportunities").click()
        await page.get_by_role("textbox", name="Search Jobs & opportunities").fill(search_term)
        await page.get_by_role("textbox", name="Search Jobs & opportunities").press("Enter")
        return

    async def get_recommendations(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, no_pages=0):
        return
