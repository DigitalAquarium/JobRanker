from playwright.async_api import expect

from common import *
import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink


class EFinancialCareersLink(JobBoardLink):
    async def get_details(self, page):
        title = page.get_by_role("heading", level=1)
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

    async def process_search_result_page(self, page, link_set, lock):
        for job in await page.locator("efc-job-card").all():
            title = job.locator(".title")
            text = await title.inner_text()
            href = await title.locator("> a").get_attribute("href")
            href = href.split("?")[0]
            company = await job.locator(".company").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(EFinancialCareersLink(href, self.site_name))
        return

    async def next_page(self, page):
        next_button = page.get_by_text("Show more")
        if await next_button.is_visible():
            await next_button.click()
            return True
        else:
            return False

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        context, page = await self.get_context()
        await asyncio.sleep(2)
        await page.get_by_placeholder("Job title").type(search_term)
        await page.keyboard.press("Enter")
        await asyncio.sleep(4)
        if no_pages == 0:
            no_pages = 100000
        for i in range(no_pages):
            await asyncio.sleep(2)
            if not await self.next_page(page):
                break
        print("a")
        await self.process_search_result_page(page, link_set, lock)
        print("b")
        await page.close()
        await context.close()
        return


'''async def main():
    x = EFinancialCareers()
    s = set()
    l = asyncio.Lock()
    jm = JobManager()
    soft = asyncio.create_task(x.get_search_results(s, l, "graduate software engineer", 5))
    #await asyncio.gather(x.get_recommendations(s, l, 1))
    await asyncio.gather(soft)
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
'''