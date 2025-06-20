import os
import time

from job import *
from selenium import webdriver
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.support.select import Select
from selenium.common import NoSuchElementException

from dotenv import load_dotenv

load_dotenv()

linkedin_session = os.getenv("LINKEDIN")
email = os.getenv("EMAIL")
reed_pw = os.getenv("REED_PW")

# Set up Selenium.
jobs = set()
driver = webdriver.Chrome()
actions = ActionChains(driver)


# TODO: Gradcracker, otta?, CV Library, glassdoor, Indeed. GRB??


def reed_process_recommendations():
    time.sleep(4)
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
            time.sleep(0.2)
            next_button.click()
        except:
            flag_more_recs = False

    for link in rec_links:
        driver.get(link)
        time.sleep(2)
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
        new_job = Job(title, description, company=company_text, url=link, site="reed")
        if new_job.is_valid():
            jobs.add(new_job)


def reed_process_page():
    time.sleep(4)
    global jobs
    main_div = driver.find_element(By.TAG_NAME, "main")
    job_divs = main_div.find_elements(By.CSS_SELECTOR, "[data-qa='job-card']")
    for job in job_divs:
        title = job.find_element(By.TAG_NAME, "h2").text
        if Job.test_blacklist(title):
            actions.move_to_element(job).click().perform()
            time.sleep(2)
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
            new_job = Job(title, description, company=company_text, url=url, site="reed")
            if new_job.is_valid():
                jobs.add(new_job)

            driver.find_element(By.CSS_SELECTOR, "div[class^='header_closeIcon']").click()
            time.sleep(0.2)
    if "pageno=" in driver.current_url:
        num = int(driver.current_url[-2:].replace("=", ""))
        num = str(num + 1)
        driver.get(driver.current_url[:-len(num)] + num)
    else:
        if "?" in driver.current_url:
            driver.get(driver.current_url + "&pageno=2")
        else:
            driver.get(driver.current_url + "?pageno=2")


def run_reed():
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
            time.sleep(1)

    reed_process_recommendations()
    textbox = driver.find_element(By.NAME, "keywords")
    textbox.click()
    textbox.send_keys("graduate software engineer")
    textbox.send_keys(Keys.ENTER)

    for i in range(3):
        h1 = driver.find_element(By.TAG_NAME, "h1")
        if "An error has occurred." in h1.text:
            break
        else:
            reed_process_page()


def set_up_linkedin():
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({"name": "li_at", "value": linkedin_session})
    driver.get("https://www.linkedin.com/jobs/")
    time.sleep(4)
    actions = ActionChains(driver)
    searchbox = driver.find_element(By.ID, "jobs-search-box-keyword-id-ember30")
    searchbox.send_keys(Keys.CONTROL + Keys.SUBTRACT)
    searchbox.send_keys("graduate software engineer")
    searchbox.send_keys(Keys.ENTER)
    time.sleep(4)
    return driver, actions


def linkedin_scroll(jobs_list_ul, yscroll=50):
    actions.move_to_element_with_offset(jobs_list_ul, jobs_list_ul.size["width"] / 2 + 5, 0).click_and_hold()
    flag = True
    while flag:
        try:
            actions.click_and_hold().move_by_offset(0, yscroll).perform()
        except:
            flag = False
    actions.release()


# TODO: Ensure that the description is actually loaded.
def linkedin_process_page():
    global jobs
    jobs_list_ul = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[1]/div/ul')
    linkedin_scroll(jobs_list_ul, 50)
    linkedin_scroll(jobs_list_ul, -100)

    jobs_list = jobs_list_ul.find_elements(By.CLASS_NAME, "job-card-container--clickable")
    for element in jobs_list:
        time.sleep(1)
        element.click()
        company = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name")
        title = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title")
        description = driver.find_element(By.ID, "job-details")
        # scaffold-skeleton-container - not loaded
        new = Job(title.text, description.text, company=company.text, site="LinkedIn", url=driver.current_url)
        if new.is_valid():
            jobs.add(new)

    linkedin_scroll(jobs_list_ul, 50)
    driver.find_element(By.CLASS_NAME, "artdeco-button--icon-right").click()
    time.sleep(4)
    driver.refresh()


driver.get("https://www.cv-library.co.uk/candidate/login")
while True:
    try:
        driver.find_element(By.CSS_SELECTOR, "div[class=cf_modal_container]").shadow_root.find_element(By.ID,
                                                                                                       "cf_consent-buttons__reject-all").click()
        break
    except:
        time.sleep(1)
time.sleep(1)
driver.find_element(By.ID, "cand_email").send_keys(email)
driver.find_element(By.ID, "cand_password").send_keys(os.getenv("CV_LIB_PW"))
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
time.sleep(2)
links = []
for job in driver.find_elements(By.CLASS_NAME, "job-match"):
    if Job.test_blacklist(job.find_element(By.TAG_NAME, "h3").text):
        links.append(job.find_element(By.CLASS_NAME, "cvl-btn--blue").get_attribute("href"))

driver.find_element(By.ID, "header-search-keywords").send_keys("graduate software developer")
driver.find_element(By.ID, "header-search-location").send_keys("Shepherds Bush, Greater London" + Keys.ENTER)

flag = True
while flag:
    time.sleep(2)
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
    time.sleep(1)
    title = driver.find_element(By.TAG_NAME, "h1").text
    try:
        company = driver.find_element(By.CSS_SELECTOR, "span[data-jd-company]").text
    except:
        company = driver.find_element(By.CLASS_NAME, "prem-feat-posted").find_element(By.TAG_NAME, "a").text
    try:
        description = driver.find_element(By.CLASS_NAME, "job__description").text
    except:
        description = driver.find_element(By.CLASS_NAME, "premium-description").text
    nj = Job(title, description, company=company, url=link, site="CV Library")
    if nj.is_valid():
        jobs.add(nj)

# run_reed()
job_list = list(jobs)
job_list.sort()

for j in job_list:
    print(j.title, "-", j.company + ":", j.rank)

# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(600)
