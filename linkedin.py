from common import *

linkedin_session = os.getenv("LINKEDIN")

driver = webdriver.Chrome()
actions = ActionChains(driver)


async def set_up_linkedin():
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({"name": "li_at", "value": linkedin_session})
    driver.get("https://www.linkedin.com/jobs/")
    await asyncio.sleep(4)

    recommended = driver.find_element(By.CLASS_NAME,'discovery-templates-jobs-home-vertical-list__footer')
    actions.move_to_element(recommended).click().perform()
    await asyncio.sleep(4)
    await linkedin_process_page()

    driver.get("https://www.linkedin.com/jobs/search/?distance=25&geoId=101165590&keywords=graduate%20software%20engineer")
    await asyncio.sleep(10)
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
async def linkedin_process_page():
    global jobs
    jobs_list_ul = driver.find_element(By.XPATH, '//*[@id="main"]/div/div[2]/div[1]/div/ul')
    linkedin_scroll(jobs_list_ul, 50)
    linkedin_scroll(jobs_list_ul, -100)

    jobs_list = jobs_list_ul.find_elements(By.CLASS_NAME, "job-card-container--clickable")
    for element in jobs_list:
        await asyncio.sleep(2)
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
        location = None
        try:
            location = driver.find_element(By.CSS_SELECTOR,'div[class="job-details-jobs-unified-top-card__primary-description-container"] div span span:nth-child(1)').text
        except:
            await asyncio.sleep(2)
            try:
                location = driver.find_element(By.CSS_SELECTOR,
                                               'div[class="job-details-jobs-unified-top-card__primary-description-container"] div span span:nth-child(1)').text
            except:
                location = driver.find_element(By.XPATH,'/html/body/div[6]/div[3]/div[4]/div/div/main/div/div[2]/div[2]/div/div[2]/div/div[2]/div[1]/div/div[1]/div/div[1]/div/div[3]/div/span/span[1]').text

        await jobs.add(title.text, description, company=company.text, site="LinkedIn", url=driver.current_url,location=location)

    linkedin_scroll(jobs_list_ul, 50)
    await asyncio.sleep(1)
    try:
        driver.find_element(By.CLASS_NAME, "artdeco-button--icon-right").click()
    except:
        pass
    await asyncio.sleep(4)
    # driver.refresh()


async def run_linkedin():
    await set_up_linkedin()
    for i in range(10):
        await linkedin_process_page()
