from common import *
import playwright.async_api


async def run_otta():
    x = await playwright.async_api.async_playwright().start()
    browser = await x.chromium.launch(headless=False)
    context = await browser.new_context()

    page = await context.new_page()
    await page.goto("https://app.welcometothejungle.com/")
    print(await page.title())
    await page.get_by_label("email").fill(email)
    await page.get_by_label("password").fill(os.getenv("OTTA_PW"))
    await page.get_by_role("button").get_by_text("Sign in").click()

    await asyncio.sleep(1000000000000)


async def run_otta_old():
    driver = webdriver.Chrome()
    actions = ActionChains(driver)
    driver.get("https://app.welcometothejungle.com/")
    driver.find_element(By.ID, "email").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(os.getenv("OTTA_PW"), Keys.ENTER)
    await asyncio.sleep(3)
    driver.get("https://app.welcometothejungle.com/jobs")
    await asyncio.sleep(0.7)
    try:
        driver.find_element(By.CSS_SELECTOR, 'div[data-testid="modal-remove-button"]').click()
    except:
        pass

    while True:
        await asyncio.sleep(1)
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
        await jobs.add(title, description, location=location, company=company, url=driver.current_url, site="Otta")
        actions.key_down(Keys.RIGHT).key_up(Keys.RIGHT).perform()


#asyncio.run(run_otta())
