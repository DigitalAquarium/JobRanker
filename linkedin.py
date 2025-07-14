import random

from playwright.async_api import expect

from common import *

from job_board import JobBoardScraper, JobBoardLink


class LinkedinLink(JobBoardLink):
    async def get_details(self, page):
        await page.get_by_role("button", name="Click to see more description").click()

        title = await page.get_by_role("heading", level=1).inner_text()
        location = await page.locator("xpath=/html/body/div[7]/div[3]/div[2]/div/div/main/div[2]/div[1]/div/div[1]/div/div/div/div[3]/div/span/span[1]").inner_text()
        company = await page.locator(".job-details-jobs-unified-top-card__company-name").inner_text()
        description = await page.locator(".mt4 > p").first.inner_text()
        return {"title": title, "description": description, "company": company, "location": location}


class Linkedin(JobBoardScraper):
    site_url = "https://www.linkedin.com"
    site_name = "Linkedin"

    async def get_recommendations(self, link_set, lock, no_pages=0):
        await asyncio.sleep(random.random() * 10)
        context, page = await self.get_context()
        await asyncio.sleep(0.5+random.random()*5)
        await page.goto("https://www.linkedin.com/jobs/")
        await asyncio.sleep(0.5+random.random()*5)
        recommendation_button = page.get_by_role("link", name="Show all Top job picks for you")
        await expect(recommendation_button).to_be_in_viewport(timeout=60000)
        await recommendation_button.click()
        if no_pages == 0:
            no_pages = 100000
        for i in range(no_pages):
            await self.process_search_result_page(page, link_set, lock)
            if not await self.next_page(page):
                break
        await page.close()
        await context.close()
        return

    async def process_search_result_page(self, page, link_set, lock):
        await asyncio.sleep(3)
        job_list_container = page.locator("xpath=//*[@id='main']/div/div[2]/div[1]/div/ul")
        job_list_bounds = await job_list_container.bounding_box()
        await page.mouse.move(x=job_list_bounds["x"] + job_list_bounds["width"] / 2, y=job_list_bounds["y"] + 100)
        SCROLL_TIMES = 7
        for i in range(100, int(job_list_bounds["height"]), int(job_list_bounds["height"] / SCROLL_TIMES)):
            await page.mouse.wheel(0, int(job_list_bounds["height"] / SCROLL_TIMES))
            await asyncio.sleep(0.5)
        job_list_container = page.locator("xpath=//*[@id='main']/div/div[2]/div[1]/div/ul")
        for job in await job_list_container.locator(">li").all():
            title = job.locator("strong").first
            text = await title.inner_text()
            href = await job.get_by_role("link").get_attribute("href")
            href = href.split("?")[0]
            company = await job.locator(".artdeco-entity-lockup__subtitle").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(LinkedinLink(self.site_url + href, self.site_name))
        return

    async def next_page(self, page):
        next_button = page.get_by_role("button", name="View next page")
        if await next_button.is_visible():
            await next_button.click()
            return True
        else:
            return False

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        await asyncio.sleep(random.random() * 10)
        context, page = await self.get_context()
        await asyncio.sleep(0.5+random.random()*5)
        await page.goto("https://www.linkedin.com/jobs/")
        await asyncio.sleep(0.5+random.random()*5)
        search_box = page.locator("#jobs-search-box-keyword-id-ember30")
        await expect(search_box).to_be_in_viewport(timeout=60000)
        await search_box.type(search_term)
        await page.keyboard.press("Enter")
        if no_pages == 0:
            no_pages = 100000
        for i in range(no_pages):
            await self.process_search_result_page(page, link_set, lock)
            if not await self.next_page(page):
                break
        await page.close()
        await context.close()
        return


'''async def main():
    x = Linkedin()
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