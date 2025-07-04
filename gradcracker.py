from common import *

driver = webdriver.Chrome()
actions = ActionChains(driver)


async def run_gradcracker():
    driver.get("https://www.gradcracker.com/search/computing-technology/computer-science-graduate-jobs")
    links = []
    more_jobs_flag = True
    while more_jobs_flag:
        await asyncio.sleep(5)
        for title_a in driver.find_elements(By.CSS_SELECTOR, "a[title^='Apply for ']"):
            if Job.test_blacklist(title_a.text):
                links.append(title_a.get_attribute("href"))
        try:
            next_page_button = driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
            actions.move_to_element(next_page_button).click().perform()
        except:
            more_jobs_flag = False

    for link in links:
        driver.get(link)
        await asyncio.sleep(3)
        title = driver.find_element(By.TAG_NAME, "h1").text
        company = driver.find_element(By.XPATH, "/html/body/div[4]/div/div[3]/ul/li[2]/a").text[:-4]
        description = driver.find_element(By.CLASS_NAME, "job-description").text
        sidebar = driver.find_element(By.XPATH, "/html/body/div[4]/div/div[5]/div[2]/div[1]/div[1]/ul")
        location = ""
        for li in sidebar.find_elements(By.TAG_NAME, "li"):
            if "Location" in li.text:
                location = li.text.replace("Location\n", "")
        await jobs.add(title, description, company=company, url=link, location=location, site="Gradcracker")
