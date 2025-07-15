import playwright.async_api

from common import *
from job_board import JobBoardScraper, JobBoardLink


class EFinancialCareersLink(JobBoardLink):
    async def get_details(self, page):
        title = page.get_by_role("heading", level=1).first
        if await title.inner_text() == "The Personal Information Protection Law (PIPL) came into force on November 1st.":
            # Oops! I think we may have annoyed them slightly! (403)
            return {"title": "Senior", "description": "description", "company": "", "location": ""}
        try:
            location = await title.locator("xpath=../span[2]").inner_text(timeout=5000)
            company = await title.locator("xpath=../span[1]").inner_text(timeout=5000)
        except:
            location = await title.locator("xpath=../span").inner_text()
            company = await title.locator("xpath=../a").inner_text()
        title = await title.inner_text()
        description = await page.locator("efc-job-description").inner_text()
        description = description.split("Job ID  ")[0]
        return {"title": title, "description": description, "company": company, "location": location}


class EFinancialCareers(JobBoardScraper):
    site_url = "https://www.efinancialcareers.co.uk"
    site_name = "eFinancialCareers"
    next_first = True

    async def process_search_result_page(self, page, link_set, lock):
        for job in await page.locator("efc-job-card").all():
            title = job.locator(".title")
            text = await title.inner_text()
            href = await title.locator("> a").get_attribute("href")
            href = href.split("?")[0]
            try:
                company = await job.locator(".company").inner_text(timeout=5000)
            except playwright.async_api.TimeoutError:
                company = "eFinancialCareers: Non-Disclosed Client"

            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(EFinancialCareersLink(href, self.site_name))
        return

    def get_next_button(self, page: playwright.async_api.Page) -> playwright.async_api.Locator:
        return page.get_by_text("Show more")

    async def get_recommendations(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, no_pages=0):
        return

    async def go_to_search(self, page, search_term):
        await asyncio.sleep(2)
        await page.get_by_placeholder("Job title").type(search_term)
        await page.keyboard.press("Enter")
        await asyncio.sleep(4)
        return
