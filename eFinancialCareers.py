import re

from common import *

driver = webdriver.Chrome()
actions = ActionChains(driver)


async def run_e_financial_careers():
    driver.get(
        "https://www.efinancialcareers.co.uk/jobs/graduate-software-engineer?q=graduate+software+engineer&countryCode"
        "=GB&radius=40&radiusUnit=km&pageSize=15&currencyCode=GBP&language=en&includeUnspecifiedSalary=true")
    await asyncio.sleep(5)
    driver.find_element(By.ID, "cmpbntnotxt").click()
    show_more = driver.find_element(By.TAG_NAME, "efc-show-more")
    for i in range(10):
        actions.scroll_by_amount(0, 5000).pause(0.5).move_to_element(show_more).click().perform()
        await asyncio.sleep(1)
    actions.scroll_by_amount(0, 5000).perform()
    await asyncio.sleep(1)
    job_container = driver.find_element(By.XPATH,
                                        '/html/body/efc-shell-root/efc-job-search-page/div['
                                        '2]/div/div/div/div/efc-job-search-results/div/div[3]')
    urls = []
    for entry in job_container.find_elements(By.TAG_NAME, "efc-job-card"):
        title = entry.find_element(By.TAG_NAME, "h3")
        url = title.find_element(By.XPATH, '..').get_attribute("href")
        title = title.text
        if Job.test_blacklist(title):
            urls.append(url)
    for url in urls:
        driver.get(url)
        await asyncio.sleep(1)
        title = driver.find_element(By.TAG_NAME, "h1")
        try:
            location = title.find_element(By.XPATH, "../span[2]").text
            company = title.find_element(By.XPATH, "../span[1]").text
        except NoSuchElementException:
            location = title.find_element(By.XPATH, "../span").text
            company = title.find_element(By.XPATH, "../a").text
        title = title.text
        description = driver.find_element(By.TAG_NAME, "efc-job-description").text
        description = description[:-10]
        await jobs.add(title, description, company=company, url=url, location=location, site="eFinancialCareers")