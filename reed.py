import random
from common import *


async def reed_process_recommendations():
    await asyncio.sleep(4)
    recommendations = driver.find_elements(By.CLASS_NAME, "new-recommended-job-block")
    next_button = driver.find_element(By.CLASS_NAME, "swiper-button-next")
    flag_more_recs = True
    rec_links = []
    while flag_more_recs:
        for rec in recommendations:
            if rec.text:
                title = rec.find_element(By.TAG_NAME, "h3")
                if Job.test_blacklist(title.text):
                    href = title.find_element(By.TAG_NAME, "a").get_attribute("href")
                    if href not in rec_links:
                        rec_links.append(href)
        try:
            next_button.click()
            await asyncio.sleep(0.2)
            next_button.click()
        except:
            flag_more_recs = False

    for link in rec_links:
        driver = webdriver.Chrome()
        actions = ActionChains(driver)
        driver.get(link)
        await asyncio.sleep(2)
        description = driver.find_element(By.CSS_SELECTOR, "div[class^='job-details_jobDescription']").text
        company = driver.find_element(By.CSS_SELECTOR, "div[class^='job-title-block_postedBy']")

        # Company post comes in the format "<date> by <company name>" this formats it.
        company_text_split = company.text.split(" by ")[1:]
        company_text = ""
        for i in company_text_split:
            company_text += i
            # in case the company name contains " by " for some reason, add it back in
            if i != company_text_split[-1]:
                company_text += " by "
        title = driver.find_element(By.TAG_NAME, "h1").text
        location = driver.find_element(By.CSS_SELECTOR, "li[data-qa='job-location']").text
        await jobs.add(title, description, company=company_text, url=link, site="Reed", location=location)


async def reed_process_page():
    await asyncio.sleep(4)
    global jobs
    main_div = driver.find_element(By.TAG_NAME, "main")
    job_divs = main_div.find_elements(By.CSS_SELECTOR, "[data-qa='job-card']")
    for job in job_divs:
        title = job.find_element(By.TAG_NAME, "h2").text
        if Job.test_blacklist(title):
            actions.move_to_element(job).click().perform()
            await asyncio.sleep(2)
            description = driver.find_element(By.CSS_SELECTOR, "div[class^='job-details-drawer-modal_jobSection']").text
            company = driver.find_element(By.CSS_SELECTOR, "div[class^='job-title-block_postedBy']")

            # Company post comes in the format "<date> by <company name> this formats it.
            company_text_split = company.text.split(" by ")[1:]
            company_text = ""
            for i in company_text_split:
                company_text += i
                # in case the company name contains " by " for some reason, add it back in
                if i != company_text_split[-1]:
                    company_text += " by "
            url = driver.find_element(By.CSS_SELECTOR, "div[class^='header_newTabIcon_wrapper']").find_element(
                By.TAG_NAME, "a").get_attribute("href")
            location = driver.find_element(By.CSS_SELECTOR, "li[data-qa='job-location']").text
            await jobs.add(title, description, company=company_text, url=url, site="Reed", location=location)

            driver.find_element(By.CSS_SELECTOR, "div[class^='header_closeIcon']").click()
            await asyncio.sleep(0.2)
    if "pageno=" in driver.current_url:
        num = int(driver.current_url[-2:].replace("=", ""))
        num = str(num + 1)
        driver.get(driver.current_url[:-len(num)] + num)
    else:
        if "?" in driver.current_url:
            driver.get(driver.current_url + "&pageno=2")
        else:
            driver.get(driver.current_url + "?pageno=2")


async def run_reed():
    global jobs
    driver.get("https://secure.reed.co.uk/login")

    textbox = driver.find_element(By.ID, "signin_email")
    textbox.click()
    textbox.send_keys(email)
    textbox.send_keys(Keys.ENTER)
    textbox = driver.find_element(By.ID, "signin_password")
    textbox.click()
    textbox.send_keys(reed_pw)
    textbox.send_keys(Keys.ENTER)
    driver.find_element(By.ID, "signin_button").click()
    # remove cookie banner
    while True:
        try:
            driver.find_element(By.ID, "onetrust-reject-all-handler").click()
            break
        except:
            await asyncio.sleep(1)

    await reed_process_recommendations()
    textbox = driver.find_element(By.NAME, "keywords")
    textbox.click()
    textbox.send_keys("graduate software engineer")
    textbox.send_keys(Keys.ENTER)

    for i in range(10):
        h1 = driver.find_element(By.TAG_NAME, "h1")
        if "An error has occurred." in h1.text:
            break
        else:
            await reed_process_page()





from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class ReedLink(JobBoardLink):
    async def scrape(self, browser, semaphore, job_manager):
        async with semaphore:
            context, page = await get_context(browser, self.site, self.link)
            description = await page.locator("css=div[class^='job-details_jobDescription']").inner_text()
            company = await page.locator("css=div[class^='job-title-block_postedBy']").filter(has_not_text="Shortlist").inner_text()

            # Company post comes in the format "<date> by <company name>" this formats it.
            company_text_split = company.text.split(" by ")[1:]
            company_text = ""
            for i in company_text_split:
                company_text += i
                # in case the company name contains " by " for some reason, add it back in
                if i != company_text_split[-1]:
                    company_text += " by "
            title = await page.get_by_role("heading", level=1).inner_text()
            location = await page.locator("li[data-qa='job-location']").inner_text()
            await job_manager.add(title, description, company=company, url=self.link, site="CV Library",
                                  location=location)
            await page.close()
            await context.close()
            return


class Reed(JobBoardScraper):
    site_url = "https://www.reed.co.uk"
    site_name = "Reed"

    async def get_recommendations(self, link_set, lock):
        #playwright doesn't like logging in to reed (I blame cloudflare) so we're falling back on selinium for portions where we need to be logged in (boring)
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
        await asyncio.sleep(4)
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
                        link_set.add(ReedLink(href,self.site_name))
            try:
                next_button.click()
                await asyncio.sleep(0.2)
                next_button.click()
            except:
                flag_more_recs = False
        driver.close()
        return

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set, lock):
        await asyncio.sleep(random.randint(2,7))
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

    async def next_page(self, page:playwright.async_api.Page):
        next_button = page.get_by_role("link",name="Next page")
        await page.goto(self.site_url+await next_button.get_attribute("href"))
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