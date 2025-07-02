from common import *


def run_otta():
    driver.get("https://app.welcometothejungle.com/")
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(os.getenv("OTTA_PW"), Keys.ENTER)
    time.sleep(3)
    driver.get("https://app.welcometothejungle.com/jobs")
    time.sleep(0.7)
    try:
        driver.find_element(By.CSS_SELECTOR, 'div[data-testid="modal-remove-button"]').click()
    except:
        pass

    while True:
        time.sleep(1)
        try:
            web_title = driver.find_element(By.TAG_NAME, "h1").text
            web_title = web_title.split(", ")
            company = web_title[-1]
            title = ""
            for i in web_title[:-1]:
                title += i + ", "
            title = title[:-2]

            description = driver.find_element(By.XPATH,
                                              '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div/div[1]/div[1]/div').text
            description = description.split("\nSalary benchmarks")[0]
            location = driver.find_element(By.CSS_SELECTOR, "div[data-testid='job-location-tag']").text
        except:
            # There are no more recommendations
            break
        jobs.add(title, description, location=location, company=company, url=driver.current_url, site="Otta")
        actions.key_down(Keys.RIGHT).key_up(Keys.RIGHT).perform()
