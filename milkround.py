import random

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class MilkroundLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-14nrdsm").first.inner_text()
        location = await page.locator(".job-ad-display-14nrdsm").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class TotalJobsLink(JobBoardLink):
    async def get_details(self, page):
        await page.get_by_role("button", name="Cookie Settings").click()
        await page.get_by_role("button", name="Save and Exit").click()
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-du9bhi").first.inner_text()
        location = await page.locator(".job-ad-display-du9bhi").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Milkround(JobBoardScraper):
    site_url = "https://www.milkround.com/"
    site_name = "milkround"

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(3+random.random() * 2)
        for article in await page.get_by_role("article").locator(".res-aa3b6p").all():
            title = await article.locator(".res-ewgtgq").first.inner_text()
            href = await article.get_by_role("link").get_attribute("href")
            company = await article.locator(".res-14nrdsm").first.inner_text()
            if Job.test_blacklist(title, company=company):
                async with lock:
                    link_set.add(MilkroundLink(href, self.site_name))
        for i in range(random.randint(2,10)):
            await page.mouse.wheel(random.randint(100,500))
            await asyncio.sleep(random.random())
        return

    def get_next_button(self, page):
        return page.get_by_role("link", name="Next", exact=True)

    #

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(random.randint(1,3)+random.random())
        try:
            await page.get_by_role("combobox", name="Job title, skill or company").click()
            await asyncio.sleep(1 + random.random() * 4)
            await page.get_by_role("combobox", name="Job title, skill or company").fill(search_term)
            await asyncio.sleep(1 + random.random() * 4)
            await page.get_by_role("combobox", name="Job title, skill or company").press("Enter")
            await asyncio.sleep(1 + random.random() * 4)
        except:
            print("Milkround IP Ban D:")
        return

    async def get_recommendations(self, link_set, lock, sem, no_pages=0):
        if no_pages == 0:
            no_pages = 1000
        async with sem:
            context, page = await self.get_context()
            await asyncio.sleep(random.random() * 2 + 1)
            for i in range(no_pages):
                for button in await page.get_by_test_id("see-more").all():
                    await button.click()
                    await asyncio.sleep(random.random() * 1.5)
            for article in await page.get_by_role("article").locator(".members-area-host-xygfxa").all():
                title = await article.locator(".members-area-host-ctv6po").first.inner_text()
                href = await article.get_by_role("link").get_attribute("href")
                company = await article.locator(".members-area-host-at01ei").first.inner_text()
                if Job.test_blacklist(title, company=company):
                    async with lock:
                        if "milkround" in href:
                            link_set.add(MilkroundLink(href, self.site_name))
                        elif "totaljobs" in href:
                            link_set.add(TotalJobsLink(href, "Total Jobs"))
                        else:
                            raise ValueError("Unknown link: " + href)
            await page.close()
            await context.close()
            return
