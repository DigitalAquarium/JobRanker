from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink


class CVLibrary(JobBoardScraper):
    site_url = "https://www.cv-library.co.uk"
    site_name = "CVLibrary"

    async def get_recommendations(self, link_set, lock):
        context, page = await self.get_context()
        recs = await page.locator(".hp-job-matches-slide li").all()
        for rec in recs:
            atag = rec.locator("a")
            async with lock:
                self.add_link(link_set, await atag.text_content(), await atag.get_attribute("href"))

    async def process_search_result_page(self, page, link_set, lock):
        # returns true if there are more pages, else false.
        return False

    async def next_page(self, page):
        next_button = page.locator("css=.pagination__next")
        await next_button.click()

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        pass


async def run_cv_library():
    x = await playwright.async_api.async_playwright().start()
    browser = await x.chromium.launch(headless=False)
    context = await browser.new_context()

    page = await context.new_page()
    await page.goto("https://www.cv-library.co.uk/candidate/login")
    await page.get_by_text("Reject All").click()
    await page.get_by_label("email").fill(email)
    await page.get_by_label("password").fill(os.getenv("CV_LIB_PW"))
    await page.get_by_role("button").get_by_text("Login as jobseeker").click()
    links = []
    await asyncio.sleep(1)
    headings = await page.locator("css=.jobs-title").all()
    for heading in headings:
        links.append("https://www.cv-library.co.uk" + await heading.get_attribute("href"))

    await page.locator("css=#header-search-keywords").fill("graduate software developer")
    await page.locator("css=#header-search-location").fill("Shepherds Bush, Greater London")
    await page.get_by_role("button", name="Find jobs").click()
    flag = True
    while flag:
        await asyncio.sleep(1)
        headings = await page.locator("css=h2 a").all()
        for heading in headings:
            if Job.test_blacklist(await heading.text_content()):
                links.append("https://www.cv-library.co.uk" + await heading.get_attribute("href"))
        next_button = page.locator("css=.pagination__next")
        if await next_button.is_visible():
            await next_button.click()
        else:
            flag = False

    for link in links:
        page = await context.new_page()
        await page.goto(link)

    await asyncio.sleep(1000000000000)


async def old_run_cv_library():
    driver = webdriver.Chrome()
    actions = ActionChains(driver)
    driver.get("https://www.cv-library.co.uk/candidate/login")
    while True:
        try:
            driver.find_element(By.CSS_SELECTOR, "div[class=cf_modal_container]").shadow_root.find_element(By.ID,
                                                                                                           "cf_consent-buttons__reject-all").click()
            break
        except:
            await asyncio.sleep(1)
    await asyncio.sleep(1)
    driver.find_element(By.ID, "cand_email").send_keys(email)
    driver.find_element(By.ID, "cand_password").send_keys(os.getenv("CV_LIB_PW"))
    driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
    await asyncio.sleep(1.2)
    links = []
    for job in driver.find_elements(By.CLASS_NAME, "job-match"):
        if Job.test_blacklist(job.find_element(By.TAG_NAME, "h3").text):
            links.append(job.find_element(By.CLASS_NAME, "cvl-btn--blue").get_attribute("href"))

    driver.find_element(By.ID, "header-search-keywords").send_keys("graduate software developer")
    driver.find_element(By.ID, "header-search-location").send_keys("Shepherds Bush, Greater London" + Keys.ENTER)

    flag = True
    while flag:
        await asyncio.sleep(2)
        for job in driver.find_elements(By.CLASS_NAME, "results__item"):
            header = job.find_element(By.TAG_NAME, "h2")
            if Job.test_blacklist(header.text):
                link = header.find_element(By.TAG_NAME, "a").get_attribute("href")
                links.append(link)
        try:
            next = driver.find_element(By.CLASS_NAME, "pagination__next")
            actions.move_to_element(next).click().perform()
        except:
            flag = False

    for link in links:
        driver.get(link)
        await asyncio.sleep(1)
        title = driver.find_element(By.TAG_NAME, "h1").text
        location = driver.find_element(By.CSS_SELECTOR, "dd[data-jd-location]").text
        try:
            company = driver.find_element(By.CSS_SELECTOR, "span[data-jd-company]").text
        except:
            company = driver.find_element(By.CLASS_NAME, "prem-feat-posted").find_element(By.TAG_NAME, "a").text
        try:
            description = driver.find_element(By.CLASS_NAME, "job__description").text
        except:
            description = driver.find_element(By.CLASS_NAME, "premium-description").text
        await jobs.add(title, description, company=company, url=link, site="CV Library", location=location)


x = CVLibrary()

asyncio.run(x.get_recommendations(set(), asyncio.Lock()))
