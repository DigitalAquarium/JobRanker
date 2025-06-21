from common import *


def run_cv_library():
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
