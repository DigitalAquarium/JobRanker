from common import *

reed_pw = os.getenv("REED_PW")

driver = webdriver.Chrome()
actions = ActionChains(driver)


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
