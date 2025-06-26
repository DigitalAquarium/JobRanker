from common import *

linkedin_session = os.getenv("LINKEDIN")


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
        time.sleep(2)
        try:
            element.click()
        except:
            # Sometimes jobs don't line up and selenium can't find the next one, in this case we're just going to skip
            break
        company = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name")
        title = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title")
        description = driver.find_element(By.ID, "job-details").text
        if description[:14] == "About the job\n":
            description = description[14:]

        location = driver.find_element(By.XPATH,'//*[@id="main"]/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span/span[1]').text
        jobs.add(title.text, description, company=company.text, site="LinkedIn", url=driver.current_url,location=location)

    linkedin_scroll(jobs_list_ul, 50)
    time.sleep(4)
    driver.find_element(By.CLASS_NAME, "artdeco-button--icon-right").click()
    time.sleep(4)
    # driver.refresh()


def run_linkedin():
    set_up_linkedin()
    for i in range(10):
        linkedin_process_page()
