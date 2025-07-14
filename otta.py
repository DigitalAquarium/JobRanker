from common import *

import playwright.async_api

from job_board import JobBoardScraper, JobBoardLink, get_context


class OttaLink(JobBoardLink):
    async def get_details(self, page):
        await page.get_by_test_id("modal-remove-button").click()
        web_title = await page.get_by_test_id("job-title").inner_text()
        web_title = web_title.split(", ")
        company = web_title[-1]
        title = ""
        for i in web_title[:-1]:
            title += i + ", "
        title = title[:-2]
        description = await page.locator(
            '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div/div[1]/div[1]/div').inner_text()
        location_tags = await page.get_by_test_id("job-location-tag").all()
        location_names = set()
        for loc in location_tags:
            location_names.add((await loc.inner_text()).lower())
        if "london" in location_names:
            location = "central london"
        else:
            location_objs = set()
            for loc_str in location_names:
                loc_obj = Location(loc_str)
                await loc_obj.create()
                location_objs.add(loc_obj)
            location_objs = list(location_objs)
            location = sorted(location_objs, key=lambda l: l.distance_score, reverse=True)[0].name

        return {"title": title, "description": description, "company": company, "location": location}


class Otta(JobBoardScraper):
    site_url = "https://app.welcometothejungle.com"
    site_name = "Otta"

    async def next_page(self, page):
        next_button = page.get_by_test_id("next-button")
        if await next_button.is_visible():
            await next_button.click()
        else:
            return False
        await asyncio.sleep(3)
        if await page.get_by_role("heading", name="You're all caught up!").is_visible():
            return False
        else:
            return True

    async def get_recommendations(self, link_set, lock, no_pages=0):
        context, page = await self.get_context()
        await asyncio.sleep(2)
        if await page.get_by_test_id("ALL_MATCHES").is_visible():
            await page.get_by_test_id("ALL_MATCHES").click()
        else:
            await page.close()
            await context.close()
            return
        await page.get_by_test_id("modal-remove-button").click()
        if await page.locator("xpath=//*[@id='radix-:rp:']/div/div/div/button[2]").is_visible():
            await page.locator("xpath=//*[@id='radix-:rp:']/div/div/div/button[2]").click()
            await asyncio.sleep(1)
        while True:
            web_title = await page.get_by_test_id("job-title").inner_text()
            web_title = web_title.split(", ")
            company = web_title[-1]
            title = ""
            for i in web_title[:-1]:
                title += i + ", "
            title = title[:-2]
            full_description = await page.locator(
                '//*[@id="root"]/div[1]/div/div/div[1]/div/div[2]/div/div[2]/div/div[1]/div[1]/div').inner_text()
            async with lock:
                if Job.test_blacklist(title, company=company, full_description=full_description):
                    link_set.add(OttaLink(page.url, self.site_name))
            if not await self.next_page(page):
                break
        await page.close()
        await context.close()
        return


'''async def main():
    temp = await playwright.async_api.async_playwright().start()
    browser = await temp.chromium.launch(headless=False)
    context, page = await get_context(browser,"Otta","https://app.welcometothejungle.com/jobs/batch-end")
    print (await Otta().next_page(page))


asyncio.run(main())'''
