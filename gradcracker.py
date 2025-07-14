import random

from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class GradCrackerLink(JobBoardLink):
    async def get_details(self, page):
        title = await page.get_by_role("heading", level=1).filter(has_not_text="2024/25").inner_text()
        company = await page.locator("xpath=/html/body/div[4]/div/div[3]/ul/li[2]/a").inner_text()
        company = company[:-4]
        description = await page.locator(".job-description").inner_text()
        sidebar = page.locator("xpath=/html/body/div[4]/div/div[5]/div[2]/div[1]/div[1]/ul")
        location = ""
        for li in await sidebar.get_by_role("listitem").all():
            text = await li.inner_text()
            if "Location" in text:
                location = text.replace("Location\n", "")
        return {"title": title, "description": description, "company": company, "location": location}


class GradCracker(JobBoardScraper):
    site_url = "https://www.gradcracker.com"
    site_name = "Gradcracker"
    run_flag = False

    async def get_recommendations(self, link_set, lock,no_pages=0):
        return

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set, lock):
        links = await page.get_by_title("Apply For").all()
        for head in links:
            text = await head.text_content()
            if Job.test_blacklist(text):
                async with lock:
                    link_set.add(GradCrackerLink(await head.get_attribute("href"), self.site_name))

    async def next_page(self, page):
        next_button = page.locator("css=a[rel='next']")
        if await next_button.is_visible():
            await next_button.click()
            return True
        else:
            return False

    async def get_search_results(self, link_set, lock, search_term, no_pages):

        # Gradcracker works a little differently, so instead of searching for a term, you'd search by discipline.
        # Doing this means we're actually going to discard the search term and check against the flag for whether
        # we've done a search or not.
        async with lock:
            if not GradCracker.run_flag:
                context, page = await self.get_context()
                await page.goto("https://www.gradcracker.com/search/computing-technology/graduate-jobs")
                GradCracker.run_flag = True
            else:
                return

        # We're going to check everything and throw out the no_pages variable too, what a shame!
        while True:
            await self.process_search_result_page(page, link_set, lock)
            if not await self.next_page(page):
                break
        await page.close()
        await context.close()
        return


'''async def main():
    x = GradCracker()
    s = set()
    l = asyncio.Lock()
    jm = JobManager()
    soft = asyncio.create_task(x.get_search_results(s, l, "graduate software engineer", 0))
    # cyber = asyncio.create_task(x.get_search_results(s, l, "graduate cyber security", 0))
    await asyncio.gather(soft)  # x.get_recommendations(s, l), soft, cyber)
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