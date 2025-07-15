import asyncio
import random

from job import Job
import playwright.async_api
from os import mkdir


async def get_context(browser, site, url) -> tuple[playwright.async_api.BrowserContext, playwright.async_api.Page]:
    context = await browser.new_context(storage_state=".auth/" + site + ".json")
    page = await context.new_page()
    try:
        await page.goto(url)
    except:
        flag = True
        while flag:
            await asyncio.sleep(random.randint(7, 15))
            try:
                await page.goto(url)
                flag = False
            except:
                await asyncio.sleep(random.randint(30, 60))

    return context, page


class JobBoardScraper:
    site_name = "example"
    site_url = "https://www.google.co.uk"
    next_first = False

    def __init__(self):
        self.browser = None

    async def setup(self):
        temp = await playwright.async_api.async_playwright().start()
        self.browser = await temp.chromium.launch(headless=False)

    @classmethod
    async def login_setup(cls):
        temp = await playwright.async_api.async_playwright().start()
        login_browser = await temp.chromium.launch(headless=False)
        context = await login_browser.new_context()
        page = await context.new_page()
        await page.goto(cls.site_url)
        input("Press enter when logged in.\n>>>")
        try:
            _ = await context.storage_state(path=".auth/" + cls.site_name + ".json")
        except FileNotFoundError:
            mkdir(".auth")
            _ = await context.storage_state(path=".auth/" + cls.site_name + ".json")
        await login_browser.close()
        await page.close()
        await temp.stop()
        return

    async def get_context(self) -> tuple[playwright.async_api.BrowserContext, playwright.async_api.Page]:
        if self.browser is None:
            await self.setup()
        try:
            return await get_context(self.browser, self.site_name, self.site_url)
        except FileNotFoundError:
            await self.login_setup()
            return await get_context(self.browser, self.site_name, self.site_url)

    def add_link(self, links, text, href):
        if Job.test_blacklist(text):
            jbl = JobBoardLink(self.site_url + href, self.site_name)
            print(text, jbl in links)
            links.add(jbl)

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set: set,
                                         lock: asyncio.Lock):
        pass

    async def next_page(self, page: playwright.async_api.Page):
        await asyncio.sleep(random.random() * 1.5)
        next_button = self.get_next_button(page)
        if await next_button.is_visible():
            await next_button.click()
            return True
        else:
            return False

    def get_next_button(self, page: playwright.async_api.Page) -> playwright.async_api.Locator:
        raise NotImplementedError

    async def go_to_search(self, page: playwright.async_api.Page, search_term):
        raise NotImplementedError

    async def go_to_recommended(self, page: playwright.async_api.Page):
        raise NotImplementedError

    async def get_recommendations(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, no_pages=0):
        await self.default_runner(link_set, lock, sem, search_term="", no_pages=no_pages)
        return

    async def get_search_results(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, search_term,
                                 no_pages=0):
        await self.default_runner(link_set, lock, sem, search_term, no_pages)
        return

    async def default_runner(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, search_term: str,
                             no_pages: int):
        # await asyncio.sleep(random.random() * 20)
        async with sem:
            await asyncio.sleep(random.random() * 5)
            context, page = await self.get_context()

            if search_term == "":
                await self.go_to_recommended(page)
            else:
                await self.go_to_search(page, search_term)

            if no_pages == 0:
                no_pages = 100000
            if self.next_first:
                for i in range(no_pages):
                    if not await self.next_page(page):
                        break
                await self.process_search_result_page(page, link_set, lock)
            else:
                for i in range(no_pages):
                    await self.process_search_result_page(page, link_set, lock)
                    if not await self.next_page(page):
                        break
            await page.close()
            await context.close()
            return


class JobBoardLink:
    link = ""
    site = ""

    def __init__(self, link, site):
        self.link = link
        self.site = site

    async def scrape(self, browser, semaphore, job_manager):
        num = random.uniform(0.2, 10) * 10
        await asyncio.sleep(num)
        async with semaphore:
            num = random.random() * 2 + 2
            await asyncio.sleep(num)
            context, page = await get_context(browser, self.site, self.link)
            num = random.random() * 2 + 2
            await asyncio.sleep(num)
            try:

                details = await self.get_details(page)

                await job_manager.add(title=details["title"], description=details["description"],
                                      company=details["company"], url=self.link, site=self.site,
                                      location=details["location"])
            except Exception as e:
                print("UH OH!!!", e)

            await page.close()
            await context.close()
            return

    async def get_details(self, page: playwright.async_api.Page):
        # Should return a dictionary with job title, description, company and location.
        raise NotImplementedError

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        return self.link == other.link
