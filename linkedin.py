import random

import playwright.async_api
from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class LinkedinLink(JobBoardLink):
    async def get_details(self, page):
        await page.get_by_role("button", name="Click to see more description").click()
        title = await page.get_by_role("heading", level=1).inner_text()
        try:
            location = await page.locator(
                "xpath=/html/body/div[7]/div[3]/div[2]/div/div/main/div[2]/div[1]/div/div[1]/div/div/div/div["
                "3]/div/span/span[1]").inner_text()
        except playwright.async_api.TimeoutError:
            try:
                location = await page.locator(
                    "xpath=/html/body/div[6]/div[3]/div[2]/div/div/main/div[2]/div[1]/div/div[1]/div/div/div/div["
                    "3]/div/span/span[1]").inner_text()
            except:
                await page.reload()
                try:
                    location = await page.locator(
                        "xpath=/html/body/div[7]/div[3]/div[2]/div/div/main/div[2]/div[1]/div/div[1]/div/div/div/div["
                        "3]/div/span/span[1]").inner_text()
                except playwright.async_api.TimeoutError:
                    location = await page.locator(
                            "xpath=/html/body/div[6]/div[3]/div[2]/div/div/main/div[2]/div[1]/div/div["
                            "1]/div/div/div/div["
                            "3]/div/span/span[1]").inner_text()

        company = await page.locator(".job-details-jobs-unified-top-card__company-name").inner_text()
        description = await page.locator(".mt4 > p").first.inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Linkedin(JobBoardScraper):
    site_url = "https://www.linkedin.com/jobs/"
    site_name = "Linkedin"

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(random.random() * 3)
        xpath = "//*[@id='main']/div/div[2]/div[1]/div/ul"
        job_list_container = page.locator(f"xpath={xpath}")
        if not await job_list_container.is_visible():
            xpath = "//*[@id='main']/div/div[2]/div[1]/ul"
            job_list_container = page.locator(f"xpath={xpath}")
        job_list_bounds = await job_list_container.bounding_box()
        await asyncio.sleep(1)
        await page.mouse.move(x=job_list_bounds["x"] + job_list_bounds["width"] / 2, y=job_list_bounds["y"] + 100)
        for i in range(10):
            await page.mouse.wheel(0, 327)
            await asyncio.sleep(0.2 + random.random() / 2)
        job_list_container = page.locator(f"xpath={xpath}")
        for job in await job_list_container.locator(">li").all():
            title = job.locator("strong").first
            text = await title.inner_text()
            href = await job.get_by_role("link").get_attribute("href")

            if "linkedin.com/jobs/search-results/" in href:
                href = href.split("?")[1].split("&")
                job_id = 0
                for get_var in href:
                    if get_var[:13] == "currentJobId=":
                        job_id = get_var[13:]
                        break
                href = self.site_url + 'view/' + job_id + "/"
            else:
                href = self.site_url[:-6] + href.split("?")[0]

            company = await job.locator(".artdeco-entity-lockup__subtitle").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(LinkedinLink(href, self.site_name))
        return

    def get_next_button(self, page):
        return page.get_by_role("button", name="View next page")

    async def go_to_recommended(self, page):
        await asyncio.sleep(3 + random.random() * 5)
        recommendation_button = page.get_by_role("link", name="Show all Top job picks for you")
        await expect(recommendation_button).to_be_in_viewport(timeout=60000)
        await recommendation_button.click()
        await asyncio.sleep(1 + random.random() * 2)
        return

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(0.5 + random.random() * 5)
        search_box = page.get_by_label("Search by title, skill, or company").first
        await expect(search_box).to_be_in_viewport(timeout=60000)
        await asyncio.sleep(1 + random.random())
        await search_box.type(search_term)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1 + random.random() * 2)
        return