import asyncio
import random

from job import Job
import playwright.async_api
from os import mkdir


async def login_setup(site, url):
    temp = await playwright.async_api.async_playwright().start()
    login_browser = await temp.chromium.launch(headless=False)
    context = await login_browser.new_context()
    page = await context.new_page()
    await page.goto(url)
    input("Press enter when logged in.\n>>>")
    try:
        _ = await context.storage_state(path=".auth/" + site + ".json")
    except FileNotFoundError:
        mkdir(".auth")
        _ = await context.storage_state(path=".auth/" + site + ".json")
    await login_browser.close()
    await page.close()
    await temp.stop()
    raise Exception("Thanks! Now restart the program please :D")


async def get_context(browser, site, url) -> tuple[playwright.async_api.BrowserContext, playwright.async_api.Page]:
    try:
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
    except FileNotFoundError:
        await login_setup(site, url)
        return (None, None)


class JobBoardScraper:
    site_name = "example"
    site_url = "https://www.google.co.uk"
    next_first = False
    browser_name = "Chrome"

    def __init__(self):
        self.browser = None

    async def setup(self):
        temp = await playwright.async_api.async_playwright().start()
        if self.browser_name == "Chrome":
            self.browser = await temp.chromium.launch(headless=False)
        else:
            self.browser = await temp.firefox.launch(headless=False)

    async def get_context(self) -> tuple[playwright.async_api.BrowserContext, playwright.async_api.Page]:
        if self.browser is None:
            await self.setup()
        return await get_context(self.browser, self.site_name, self.site_url)

    def add_link(self, links, text, href):
        if Job.test_blacklist(text):
            jbl = JobBoardLink(self.site_url + href, self.site_name)
            print(text, jbl in links)
            links.add(jbl)

    async def process_search_result_page(self, page: playwright.async_api.Page, link_set: set,
                                         lock: asyncio.Lock):
        raise NotImplementedError

    async def process_recommended_page(self, page: playwright.async_api.Page, link_set: set,
                                       lock: asyncio.Lock):
        await self.process_search_result_page(page, link_set, lock)

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
        async with sem:
            await asyncio.sleep(random.random() * 5)
            context, page = await self.get_context()

            if search_term == "":
                await self.go_to_recommended(page)
                process_method = self.process_recommended_page
            else:
                await self.go_to_search(page, search_term)
                process_method = self.process_search_result_page

            if no_pages == 0:
                no_pages = 100000
            if self.next_first:
                for i in range(no_pages):
                    await asyncio.sleep(0.5 + random.random())
                    if not await self.next_page(page):
                        break
                await process_method(page, link_set, lock)
            else:
                for i in range(no_pages):
                    await self.process_search_result_page(page, link_set, lock)
                    await asyncio.sleep(0.5 + random.random() * 3)
                    if not await self.next_page(page):
                        break
            await page.close()
            await context.close()
            return


class JobBoardLink:
    link = ""
    site = ""
    load_lock = asyncio.Lock()

    def __init__(self, link, site):
        self.link = link
        self.site = site

    async def scrape(self, browser, semaphore, job_manager):
        async with semaphore:
            async with JobBoardLink.load_lock:
                # Webpages should not load on top of each other since bot filters are very upset about that
                await asyncio.sleep(random.uniform(0.3, 0.89))
                context, page = await get_context(browser, self.site, self.link)
                await asyncio.sleep(random.uniform(0.1, 0.3))
            num = random.random() * 2 + 2
            await asyncio.sleep(num)

            try:
                details = await self.get_details(page)

                await job_manager.add(title=details["title"], description=details["description"],
                                      company=details["company"], url=self.link, site=self.site,
                                      location=details["location"])
            except Exception as e:
                # raise e
                print("UH OH!!! @ ", self.link, "\n", e)

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
