import asyncio
import random
import re

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class GlassdoorLink(JobBoardLink):
    async def get_details(self, page):
        await asyncio.sleep(random.random()+0.5)
        await page.locator("[data-test=\"show-more-cta\"]").click()
        title = await page.locator("[data-test=\"job-details-header\"]").get_by_role("heading", level=1).inner_text()
        company = await page.locator("[data-test=\"job-details-header\"]").get_by_role("heading", level=4).inner_text()
        location = await page.locator("div[data-test=\"location\"]").inner_text()
        description = await page.locator("div[class^=JobDetails_jobDescription]").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Glassdoor(JobBoardScraper):
    site_url = "https://www.glassdoor.co.uk"
    site_name = "Glassdoor"
    next_first = True
    browser_name = "Firefox"

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(random.random()*3+3)
        for listing in await page.locator("li[class^=JobsList_jobListItem]").all():
            title = listing.locator("[id^='job-title-']")
            text = await title.inner_text()
            href = await title.get_attribute("href")
            company = await listing.locator("[id^='job-employer-']").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(GlassdoorLink(href, self.site_name))

    def get_next_button(self, page):
        return page.locator("[data-test=\"load-more\"]")

    async def next_page(self, page: playwright.async_api.Page):
        await asyncio.sleep(random.random() * 0.2)
        await page.mouse.move(random.randint(10, 20), random.randint(-10, 15))
        await asyncio.sleep(random.random() * 0.2)
        try:
            await page.locator("[data-test=\"authModalContainerV2-content\"]").get_by_role("button").filter(
                has_text=re.compile(r"^$")).click(timeout=2539)
        except:
            pass
        return await super().next_page(page)

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(random.randint(1, 3) + random.random())
        await page.locator("[data-test=\"site-header-jobs\"]").get_by_text("Jobs", exact=True).click()
        await asyncio.sleep(random.random() * 0.2)
        await page.locator("[data-test=\"site-header-jobs\"] [data-test=\"start-using-glassdoor-btn\"]").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("button").filter(has_text=re.compile(r"^$")).click()
        await asyncio.sleep(random.random() * 0.2)
        await page.locator("[data-test=\"site-header-jobs\"]").get_by_text("Jobs", exact=True).click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("button", name="Select Cookies").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("button", name="Strictly Necessary Cookies").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("button", name="Confirm My Choices").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.locator("[data-test=\"site-header-community\"]").get_by_text("Community").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.locator("[data-test=\"site-header-jobs\"]").get_by_text("Jobs", exact=True).click()
        await asyncio.sleep(random.random() * 0.2)
        await page.goto("https://www.glassdoor.co.uk/Job/index.htm")
        await asyncio.sleep(1+random.random() * 4)
        await page.get_by_role("combobox", name="Find your perfect job").click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("combobox", name="Find your perfect job").fill(search_term)
        await asyncio.sleep(1+random.random() * 0.2)
        await page.locator("#searchBar-jobTitle-search-suggestions > li").first.click()
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("combobox", name="Find your perfect job").press("Tab")
        await asyncio.sleep(random.random() * 0.2)
        await page.locator("[data-test=\"clear-input\"]").press("Tab")
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("combobox", name="City, state, zipcode or \"").fill("London, ")
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("combobox", name="City, state, zipcode or \"").press("ArrowDown")
        await asyncio.sleep(random.random() * 0.2)
        await page.get_by_role("combobox", name="City, state, zipcode or \"").press("Enter")
        await asyncio.sleep(1+random.random() * 0.2)
        await page.get_by_role("button", name="Open filter menu").click()
        await asyncio.sleep(random.random() * 0.4)
        try:
            await page.locator("[data-test=\"min-salary\"]").click(timeout=1000)
            await asyncio.sleep(random.random() * 0.4)
            await page.locator("[data-test=\"min-salary\"]").press("Home")
            await asyncio.sleep(random.random() * 0.4)
            await page.locator("[data-test=\"min-salary\"]").fill("25")
            await asyncio.sleep(random.random() * 0.4)
            await page.locator("[data-test=\"apply-search-filters\"]").click()
            await asyncio.sleep(1 + random.random() * 0.2)
        except:
            pass
        await asyncio.sleep(1 + random.random() * 0.2 + 0.7 + random.random() * 2)
        try:
            await page.locator("[data-test=\"authModalContainerV2-content\"]").get_by_role("button").filter(
                has_text=re.compile(r"^$")).click(timeout=1537)
        except:
            pass
        return

    async def get_recommendations(self, link_set, lock, sem, no_pages=0):
            return
