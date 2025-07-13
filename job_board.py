import asyncio
from job import Job
import playwright.async_api
from os import mkdir


async def get_context(browser, site, url):
    context = await browser.new_context(storage_state=".auth/" + site + ".json")
    page = await context.new_page()
    await page.goto(url)
    return context, page


class JobBoardScraper:
    site_name = "example"
    site_url = "https://www.google.co.uk"

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

    async def get_context(self):
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

    async def process_search_result_page(self, page, link_set, lock):
        # returns true if there are more pages, else false.
        return False

    async def next_page(self, page):
        pass

    async def get_recommendations(self, link_set, lock):
        pass

    async def get_search_results(self, link_set, lock, search_term, no_pages):
        pass


class JobBoardLink:
    link = ""
    site = ""

    def __init__(self, link, site):
        self.link = link
        self.site = site

    async def scrape(self, browser, semaphore, job_manager):
        raise NotImplementedError

    def __hash__(self):
        return hash(self.link)

    def __eq__(self, other):
        return self.link == other.link
