import random

from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink


class ReedLink(JobBoardLink):
    async def get_details(self, page):
        try:
            description = await page.locator("css=div[class^='job-details_jobDescription']").inner_text()
            if await page.locator("css=div[data-qa='job-posted-by'] :not([name*='Shortlist'])").is_visible():
                company = await page.locator(
                    "css=div[data-qa='job-posted-by'] :not([name*='Shortlist'])").inner_text()
            elif await page.locator(
                    'xpath=//*[@id="__next"]/div[4]/div/div/div[2]/div[1]/div[2]/div[1]/div[1]/div').is_visible():
                company = await page.locator(
                    'xpath=//*[@id="__next"]/div[4]/div/div/div[2]/div[1]/div[2]/div[1]/div[1]/div').inner_text()
            else:
                company = await page.locator(
                    'xpath=//*[@id="__next"]/div[4]/div/div/div[2]/div[1]/div[2]/div[2]/div[1]/div').inner_text()

            # Company post comes in the format "<date> by <company name>" this formats it.
            if " by " in company:
                company_text_split = company.split(" by ")[1:]
                company = ""
                for i in company_text_split:
                    company += i
                    # in case the company name contains " by " for some reason, add it back in
                    if i != company_text_split[-1]:
                        company += " by "
            title = await page.get_by_role("heading", level=1).inner_text()
            location = await page.locator(
                "xpath=//*[@id='__next']/div[4]/div/div/div[2]/div[1]/div[2]/ul/li[2]").inner_text()

            return {"title": title, "description": description, "company": company, "location": location}
        except:
            err = page.get_by_text("An error has occurred.")
            if await err.is_visible():
                return
            else:
                raise Exception("REED DID AN OOPSIE")



class Reed(JobBoardScraper):
    site_url = "https://www.reed.co.uk"
    site_name = "Reed"

    async def get_recommendations(self, link_set, lock,no_pages=0):
        # playwright doesn't like logging in to reed (I blame cloudflare) so we're falling back on selinium for
        # portions where we need to be logged in (boring)
        driver = webdriver.Firefox()
        driver.get("https://secure.reed.co.uk/login")

        textbox = driver.find_element(By.ID, "signin_email")
        textbox.click()
        textbox.send_keys(email)
        textbox.send_keys(Keys.ENTER)
        textbox = driver.find_element(By.ID, "signin_password")
        textbox.click()
        textbox.send_keys(os.getenv("REED_PW"))
        textbox.send_keys(Keys.ENTER)
        driver.find_element(By.ID, "signin_button").click()
        # remove cookie banner
        while True:
            try:
                driver.find_element(By.ID, "onetrust-reject-all-handler").click()
                break
            except:
                await asyncio.sleep(1)
        await asyncio.sleep(random.random())
        recommendations = driver.find_elements(By.CLASS_NAME, "new-recommended-job-block")
        next_button = driver.find_element(By.CLASS_NAME, "swiper-button-next")
        flag_more_recs = True
        while flag_more_recs:
            for rec in recommendations:
                if rec.text:
                    title = rec.find_element(By.TAG_NAME, "h3")
                    if Job.test_blacklist(title.text):
                        href = title.find_element(By.TAG_NAME, "a").get_attribute("href")
                        href = href.split("?")[0]
                        link_set.add(ReedLink(href, self.site_name))
            try:
                next_button.click()
                await asyncio.sleep(0.2)
                next_button.click()
            except:
                flag_more_recs = False
        driver.close()
        return

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set, lock):
        await asyncio.sleep(random.randint(2, 4))
        job_divs = await page.locator("css=[data-qa='job-card']").all()
        for job in job_divs:
            title = job.locator("h2")
            text = await title.inner_text()
            href = await title.locator("a").get_attribute("href")
            href = href.split("?")[0]
            company = await job.locator("css=[data-element='recruiter']").inner_text()
            if Job.test_blacklist(text, company=company):
                async with lock:
                    link_set.add(ReedLink(self.site_url + href, self.site_name))

    async def next_page(self, page: playwright.async_api.Page):
        next_button = page.get_by_role("link", name="Next page")
        await page.goto(self.site_url + await next_button.get_attribute("href"))
        await asyncio.sleep(0.5)
        err = page.get_by_text("An error has occurred.")
        if await err.is_visible():
            return False
        else:
            return True

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        context, page = await self.get_context()
        if not no_pages:
            no_pages = 100000
        await page.locator("#main-keywords").fill(search_term)
        await page.get_by_role("button", name="Search jobs").click()
        for i in range(no_pages):
            await self.process_search_result_page(page, link_set, lock)
            if not await self.next_page(page):
                break

        await page.close()
        await context.close()
        return


'''async def main():
    x = Reed()
    s = set()
    l = asyncio.Lock()
    jm = JobManager()
    soft = asyncio.create_task(x.get_search_results(s, l, "graduate software engineer", 0))
    # cyber = asyncio.create_task(x.get_search_results(s, l, "graduate cyber security", 0))
    await asyncio.gather(soft)#x.get_recommendations(s, l))#, soft, cyber)
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


asyncio.run(main())'''
