from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class CVLibraryLink(JobBoardLink):
    async def scrape(self, browser, semaphore, job_manager):
        async with semaphore:
            context, page = await get_context(browser, self.site, self.link)
            title = await page.get_by_role("heading", level=1).inner_text()
            location = await page.locator("dd[data-jd-location]").inner_text()
            try:
                company = await page.locator("span[data-jd-company]").inner_text()
            except:
                company = await page.locator(".prem-feat-posted a").inner_text()
            try:
                description = await page.locator(".job__description").inner_text()
            except:
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
        await asyncio.sleep(2)
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

        for link in link_set:
            print(link.link)

        await page.close()
        await context.close()
        return


async def main():
    x = CVLibrary()
    s = set()
    l = asyncio.Lock()
    jm = JobManager()
    soft = asyncio.create_task(x.get_search_results(s, l, "graduate software engineer", 0))
    cyber = asyncio.create_task(x.get_search_results(s, l, "graduate cyber security", 0))
    await asyncio.gather(x.get_recommendations(s, l), soft, cyber)
    for link in s:
        print(link.link)
    l = []
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    NUM_THREADS = 5
    sem = asyncio.Semaphore(NUM_THREADS)
    for x in s:
        l.append(asyncio.create_task(x.scrape(browser, sem, jm)))
    await asyncio.gather(*l)  # x.scrape(jm) for x in s


asyncio.run(main())
