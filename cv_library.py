import random

from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class CVLibraryLink(JobBoardLink):
    async def scrape(self, browser, semaphore, job_manager):
        async with semaphore:
            await asyncio.sleep(random.uniform(2, 6))
            context, page = await get_context(browser, self.site, self.link)
            title = await page.get_by_role("heading", level=1).inner_text()
            location = await page.locator("dd[data-jd-location]").inner_text()
            if await page.locator("span[data-jd-company]").is_visible():
                company = await page.locator("span[data-jd-company]").inner_text()
            else:
                company = await page.locator(".prem-feat-posted a").inner_text()
            if await page.locator(".job__description").is_visible():
                description = await page.locator(".job__description").inner_text()
            else:
                description = await page.locator(".premium-description").inner_text()

            await job_manager.add(title, description, company=company, url=self.link, site="CV Library",
                                  location=location)
            await page.close()
            await context.close()
            return


class CVLibrary(JobBoardScraper):
    site_url = "https://www.cv-library.co.uk"
    site_name = "CVLibrary"

    async def get_recommendations(self, link_set, lock):
        context, page = await self.get_context()
        recs = await page.locator(".hp-job-matches-slide li").all()
        for rec in recs:
            atag = rec.locator("a")
            text = await atag.inner_text()
            href = await atag.get_attribute("href")
            async with lock:
                if Job.test_blacklist(text):
                    link_set.add(CVLibraryLink(self.site_url + href, self.site_name))
        await page.close()
        await context.close()
        return

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(5)
        articles = await page.locator("li article").filter(has=page.locator("h2")).all()
        for article in articles:
            # print(await heading.locator(".job__title a").inner_text())
            heading = article.locator(".job__title a")
            text = await heading.inner_text()
            company = await article.locator(".job__company-link").inner_text()
            href = await heading.get_attribute("href")
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(CVLibraryLink(self.site_url + href, self.site_name))

    async def next_page(self, page):
        next_button = page.locator("css=.pagination__next")
        if await next_button.is_visible():
            await next_button.click()
            return True
        else:
            return False

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        context, page = await self.get_context()
        if not no_pages:
            no_pages = 100000
        await page.get_by_placeholder("Keywords / Job Title / Job Ref").fill(search_term)
        await page.get_by_placeholder("Location").fill("Shepherds Bush, Greater London")
        await page.get_by_role("button", name="Find jobs").click()
        for i in range(no_pages):
            await self.process_search_result_page(page, link_set, lock)
            if not await self.next_page(page):
                break

        await page.close()
        await context.close()
        return
