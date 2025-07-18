import asyncio
import random

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink



#MONSTER IS REALLY GOOD AT DETECTING BOTS, this don't be working

class MonsterLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-14nrdsm").first.inner_text()
        location = await page.locator(".job-ad-display-14nrdsm").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Monster(JobBoardScraper):
    site_url = "https://www.monster.co.uk"
    site_name = "Monster"
    next_first = True

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

    async def go_to_recommended(self, page):
        await asyncio.sleep(4)
        await page.get_by_test_id("profile-navigation-item-profileRecommendedJobs").click()
        return

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(0.7 + random.random() * 2)
        for article in await page.get_by_role("article").locator(".res-aa3b6p").all():
            title = await article.locator(".res-ewgtgq").first.inner_text()
            href = await article.get_by_role("link").get_attribute("href")
            company = await article.locator(".res-14nrdsm").first.inner_text()
            if Job.test_blacklist(title, company=company):
                async with lock:
                    link_set.add(MilkroundLink(href, self.site_name))
        for i in range(random.randint(2, 10)):
            await page.mouse.wheel(random.randint(-5, 5), random.randint(100, 500))
            await asyncio.sleep(random.random())
        return

    async def process_recommended_page(self, page: playwright.async_api.Page, link_set: set,
                                              lock: asyncio.Lock):
        for card in await page.get_by_test_id("JobCard").all():
            title = card.locator("h3 > a")
            text = await title.inner_text()
            href = await title.get_attribute("href")
            company = await card.get_by_test_id("company").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(MonsterLink(href, self.site_name))

    async def next_page(self, page: playwright.async_api.Page):
        for i in range(random.randint(7, 10)):
            await page.mouse.wheel(0, random.randint(299, 405))
            await asyncio.sleep(random.uniform(0.2, 0.7))
        await page.mouse.wheel(0, -random.randint(740, 799))
        await asyncio.sleep(1+random.random()*3)
        if await page.get_by_test_id("svx-no-more-results-disabled-button").is_visible():
            return False
        else:
            return True