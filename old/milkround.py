import asyncio
import random

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class MilkroundLink(JobBoardLink):
    slow_baby_slow = asyncio.Lock()

    async def get_details(self, page):
        async with MilkroundLink.slow_baby_slow:
            await page.mouse.move(random.randint(10, 20), random.randint(-10, 15))
            await asyncio.sleep(2 + random.random() * 5)
            await page.mouse.move(random.randint(10, 20), random.randint(-10, 15))
        title = await page.get_by_role("heading", level=1).first.inner_text()
        company = await page.locator(".job-ad-display-14nrdsm").first.inner_text()
        location = await page.locator(".job-ad-display-14nrdsm").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class TotalJobsLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-du9bhi").first.inner_text()
        location = await page.locator(".job-ad-display-du9bhi").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class CWJobsLink(JobBoardLink):
    async def get_details(self, page):
        await page.get_by_role("button", name="Cookie Settings").click()
        await page.get_by_role("button", name="Save and Exit").click()
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-14nrdsm").first.inner_text()
        location = await page.locator(".job-ad-display-14nrdsm").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Milkround(JobBoardScraper):
    site_url = "https://www.milkround.com"
    site_name = "milkround"

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(0.7 + random.random() * 2)

        async def nav_visible(page):
            try:
                await expect(self.get_next_button(page)).to_be_in_viewport(timeout=50)
                return True
            except:
                return False

        i = 0
        while not await nav_visible(page):
            await page.mouse.wheel(random.randint(-5, 5), random.randint(450, 500))
            await asyncio.sleep(random.random() / 2)
            if i >= 100:
                break
            i += 1
        for article in await page.get_by_test_id("job-card-content").all():
            title = article.get_by_role("heading", level=2)
            text = await title.first.inner_text()
            href = await title.get_by_role("link").get_attribute("href")
            company = await article.locator(".res-14nrdsm").first.inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(MilkroundLink(self.site_url + href, self.site_name))
        return

    def get_next_button(self, page):
        return page.get_by_role("link", name="Next", exact=True)

    #

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(random.randint(1, 3) + random.random())
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
                    try:
                        await button.click()
                    except:
                        pass
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
                        elif "cwjobs" in href:
                            link_set.add(CWJobsLink(href, "CWJobs"))
                        else:
                            raise ValueError("Unknown link: " + href)
            await page.close()
            await context.close()
            return
