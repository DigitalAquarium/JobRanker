import json
import random
import urllib
from urllib.error import HTTPError

import requests

from job_board import JobBoardScraper, JobBoardLink, get_context
from common import *
from linkedin import LinkedinLink
from eFinancialCareers import EFinancialCareersLink
from reed import ReedLink
from cv_library import CVLibraryLink
from glassdoor import GlassdoorLink
from milkround import MilkroundLink, TotalJobsLink, CWJobsLink
from targetjobs import TargetJobsLink

API_UID = os.getenv("ADZUNA_UID")
API_KEY = os.getenv("ADZUNA_API_KEY")


class Adzuna_Api(JobBoardScraper):
    async def get_recommendations(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, no_pages=0):
        return

    async def get_search_results(self, link_set: set, lock: asyncio.Lock, sem: asyncio.Semaphore, search_term,
                                 no_pages=0):
        if no_pages == 0:
            no_pages = 100
        async with sem:
            print("Calling Adzuna API")
            for i in range(no_pages):
                api_call = f"https://api.adzuna.com/v1/api/jobs/gb/search/{i+1}" \
                           f"?app_id={API_UID}" \
                           f"&app_key={API_KEY}" \
                           f"&results_per_page=50" \
                           f"&what_or={search_term.replace(' ', '%20')}" \
                           f"&what_exclude=Senior" \
                           f"&salary_include_unknown=1"
                # It'll only ever send max 50 per page.
                await asyncio.sleep(random.uniform(1, 3))
                response = requests.get(api_call)
                response = json.loads(response.content)
                for job in response["results"]:
                    if Job.test_blacklist(job["title"], job["company"]['display_name']) and not any(
                            [word in job["description"] for word in Job.term_blacklist]):
                        async with lock:
                            link_set.add(
                                AdzunaLink(job["redirect_url"], "Adzuna", job["title"], job["description"],
                                           job["company"]["display_name"], job["location"]["area"][-1])
                            )
                if i + 1 * 50 > response["count"]:
                    break
            print("Adzuna API Documented for:",search_term)
            return


class AdzunaLink(JobBoardLink):
    flag_403 = False

    def __init__(self, link, site, title, short_description, company, location):
        super().__init__(link, site)
        self.short_description = short_description
        self.company = company
        self.location = location
        self.title = title

    @staticmethod
    async def get_first_url_from_page(url):
        await asyncio.sleep(random.uniform(0.2, 1))
        req = urllib.request.Request(url)
        req.add_header('User-Agent',
                       'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0')
        req.add_header('Accept',
                       'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8')
        req.add_header('Accept-Language', 'en-US,en;q=0.5')
        try:
            webpage = urllib.request.urlopen(req).read().decode('utf-8')
            webpage = webpage.split("</script>")[0]
            out = webpage[webpage.find("https://"):].split("\"")[0]
            if "zunastatic" in out:
                # for some reason they're redirecting to their own site. :Cinema:
                jobid = url.split('?')[0][38:]
                return f"https://www.adzuna.co.uk/jobs/details/{jobid}"
            if out == "\n":
                out = webpage[webpage.find("http://"):].split("\"")[0]
            return out
        except HTTPError:
            return None

    async def scrape(self, browser, semaphore, job_manager):
        # Since we're already going to claim the
        # semaphore, we don't really need to worry about calling new funcs that require it, hence the dummy
        dummy_semaphore = asyncio.Semaphore(10)
        async with semaphore:
            print(self.location)
            if self.link[30:37] == "details":
                # This is an internal adzuna link, do things normally
                await super().scrape(browser, dummy_semaphore, job_manager)
                pass
            else:
                if not AdzunaLink.flag_403:
                    redirect_location = await self.get_first_url_from_page(self.link)
                    if redirect_location is None:
                        AdzunaLink.flag_403 = True
                    elif redirect_location[8:24] == 'click.appcast.io':
                        click_appcast = await self.get_first_url_from_page(redirect_location)

                        if click_appcast is None:
                            AdzunaLink.flag_403 = True
                        else:
                            actual_url = click_appcast
                    else:
                        actual_url = redirect_location

                if AdzunaLink.flag_403:
                    async with JobBoardLink.load_lock:
                        context, page = await get_context(browser, self.site, self.link)
                    while "adzuna.co.uk/jobs/land/" in page.url or 'click.appcast.io' in page.url:
                        await asyncio.sleep(random.uniform(5, 5.2))
                    actual_url = page.url
                    await context.close()
                    await page.close()

                domain = actual_url.split("/")[2]
                print(domain)
                if "linkedin" in domain:
                    actual_link_obj = LinkedinLink(actual_url, "LinkedIn")
                elif "efinancialcareers" in domain:
                    actual_link_obj = EFinancialCareersLink(actual_url, "eFinancialCareers")
                elif "adzuna" in domain:
                    actual_link_obj = AdzunaLink(actual_url, "Adzuna", self.title, self.short_description, self.company,
                                                 self.location)
                elif "reed" in domain:
                    actual_link_obj = ReedLink(actual_url, "Reed")
                elif "cv-library" in domain:
                    actual_link_obj = CVLibraryLink(actual_url, "CVLibrary")
                elif "glassdoor" in domain:
                    actual_link_obj = GlassdoorLink(actual_url, "Glassdoor")
                elif "milkround" in domain:
                    actual_link_obj = MilkroundLink(actual_url, "Milkround")
                elif "totaljobs" in domain:
                    actual_link_obj = TotalJobsLink(actual_url, "Total Jobs")
                elif "cwjobs" in domain:
                    actual_link_obj = CWJobsLink(actual_url, "CWJobs")
                elif "nijobs" in domain:
                    actual_link_obj = NIJobsLink(actual_url, "NIJobs")
                elif "targetjobs" in domain:
                    actual_link_obj = TargetJobsLink(actual_url, "TargetJobs")
                elif "ivyexec" in domain:
                    #this is a job board for senior positions
                    return
                # TODO:  Prospects.ac.uk
                else:
                    async with JobBoardLink.load_lock:
                        await asyncio.sleep(random.uniform(1, 3))
                        context, page = await get_context(browser, self.site, actual_url)
                    await asyncio.sleep(random.uniform(3, 4))
                    html = (await page.content()).lower()
                    if any([term in html for term in Job.term_whitelist]):
                        await job_manager.add(self.title,
                                              "🚱 " + self.short_description + "\n We were unable to recover further info about this (Hopefully graduate) job description!",
                                              site="🚱 Unknown Site via Adzuna",
                                              url=actual_url,
                                              company=self.company,
                                              location=self.location
                                              )
                    await context.close()
                    await page.close()
                    return

                await actual_link_obj.scrape(browser, dummy_semaphore, job_manager)
                return

    async def get_details(self, page):
        full_description = await page.locator("xpath=/html/body/div[1]/div/div/section[1]/div[1]/section").inner_text()
        if "Role Overview" in full_description:
            full_description = full_description.split("Role Overview")[1]
        return {"title": self.title, "description": full_description, "company": self.company,
                "location": self.location}

class NIJobsLink(JobBoardLink):
    async def get_details(self, page):
        try:
            await page.get_by_role("button", name="Cookie Settings").click()
            await page.get_by_role("button", name="Save and Exit").click()
        except:
            pass
        title = await page.get_by_role("heading", level=1).inner_text()
        company = await page.locator(".job-ad-display-du9bhi").first.inner_text()
        location = await page.locator(".job-ad-display-du9bhi").nth(1).inner_text()
        description = await page.locator(".at-section-text-jobDescription-content").inner_text()
        return {"title": title, "description": description, "company": company, "location": location}