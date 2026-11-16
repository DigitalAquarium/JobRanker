#Scraping Services:
# https://scrapfly.io/ * 1000
# https://www.firecrawl.dev/ * 1000
# https://geonode.com/products/scraper-api * 1500
# https://brightdata.com/products/web-scraper * 5000
# https://finedata.ai/blog/free-scraper-api-finedata-tier/ * 1000
from JobRanker import llm_manager, settings
from jobs.models import *
import html
import json
import math
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Tag
from ddgs import DDGS
import requests
from firecrawl import Firecrawl

from jobs.processors.processor import Processor, extract_deadline, extract_salary
from jobs.processors.processor import clean_str as _clean_str
from jobs.processors.processor import parse_date_safe as _parse_date_safe

total_remaining=0

JOB_BOARDS = {
    "linkedin", "indeed", "glassdoor", "monster", "reed", "totaljobs",
    "cwjobs", "ziprecruiter", "greenhouse", "lever", "workday",
    "ashby", "smartrecruiters", "icims", "taleo", "breezy", "recruitee",
    "workable", "flexa", "otta", "wellfound", "angel", "successfactors",
    "jobvite", "teamtailor", "personio", "pinpointhq", "rippling", "bamboohr",
}

NON_COMPANY_NAMES = JOB_BOARDS | {
    "careers", "jobs", "join us", "work with us", "hiring", "talent",
    "recruitment", "recruiting", "home", "welcome", "official site",
    "apply", "apply now", "confidential", "unknown", "n/a", "none",
    "cloudflare", "amazonaws", "herokuapp", "netlify", "vercel",
    "wixsite", "github", "gitlab",
}

NON_JOB_TITLES = {
    "linkedin", "indeed", "glassdoor", "sign in", "log in", "login",
    "just a moment...", "access denied", "403 forbidden", "404 not found",
    "page not found", "security verification", "careers", "jobs",
    "job details", "career opportunities", "open positions", "current openings",
    "search jobs", "job search", "apply now", "home", "welcome",
}

SUBDOMAIN_ATS_DOMAINS = (
    "myworkdayjobs.com", "breezy.hr", "recruitee.com", "bamboohr.com",
    "teamtailor.com", "pinpointhq.com", "rippling.com",
)

PATH_ATS_DOMAINS = (
    "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com",
    "workable.com", "jobvite.com",
)

GENERIC_SLUGS = {
    "www", "jobs", "careers", "apply", "boards", "job-boards",
    "en", "en-us", "en-gb", "uk", "us", "eu", "emea", "global", "hr", "talent",
}

BLOCK_PAGE_MARKERS = (
    "just a moment...",
    "enable javascript and cookies to continue",
    "cf-browser-verification",
    "checking your browser before accessing",
    "access denied",
    "403 forbidden",
    "404 not found",
    "page not found",
    "too many requests",
    "unusual traffic from your computer",
    "please verify you are a human",
    "security verification",
)

CLOSED_JOB_MARKERS = (
    "this job is no longer available",
    "no longer accepting applications",
    "position has been filled",
    "role has been filled",
    "posting has expired",
    "job has expired",
    "this requisition is closed",
)

JOB_DESCRIPTION_CUES = (
    "responsibilities", "requirements", "qualifications", "experience",
    "skills", "benefits", "about the role", "about you", "what you'll do",
    "what you will do", "who you are", "role", "candidate", "apply",
    "salary", "compensation", "degree", "team", "position", "opportunity",
    "working", "duties", "knowledge", "ability",
)

MIN_DESCRIPTION_CHARS = 250
MAX_DESCRIPTION_CHARS = 35_000


def _clean_multiline(val: Any) -> Optional[str]:
    """Preserves intentional line breaks while collapsing horizontal whitespace."""
    if not isinstance(val, str):
        return _clean_str(val)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in val.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned if cleaned else None


def _is_blocked_or_closed_page(raw_html: str, visible_text: str, has_jsonld: bool) -> bool:
    """Detects WAF blocks, HTTP error pages, or short closed-job stubs."""
    stripped = raw_html.lstrip()
    if stripped.startswith(("{", "[")):
        return True

    lower_text = visible_text.lower()
    if not has_jsonld and len(visible_text) < 2000:
        if any(marker in lower_text for marker in BLOCK_PAGE_MARKERS):
            return True

    if len(visible_text) < 900:
        if any(marker in lower_text for marker in CLOSED_JOB_MARKERS):
            return True

    return False


def _looks_like_job_description(text: Optional[str]) -> bool:
    """Checks that generic extracted text resembles an actual job posting rather than boilerplate."""
    if not text:
        return False
    length = len(text)
    if length < MIN_DESCRIPTION_CHARS or length > MAX_DESCRIPTION_CHARS:
        return False
    lower = text.lower()
    cue_hits = sum(1 for cue in JOB_DESCRIPTION_CUES if re.search(rf"\b{re.escape(cue)}\b", lower))
    return cue_hits >= 2


def _validate_company_name(name: Optional[str]) -> Optional[str]:
    """Rejects generic labels, job boards, URLs, and implausible company strings."""
    cleaned = _clean_str(name)
    if not cleaned:
        return None
    cleaned = re.sub(r"\s+(?:careers|jobs|recruitment|talent)$", "", cleaned, flags=re.IGNORECASE).strip()
    if not cleaned or len(cleaned) < 2 or len(cleaned) > 80:
        return None
    if cleaned.lower() in NON_COMPANY_NAMES:
        return None
    if re.search(r"(https?://|www\.|@)", cleaned, re.IGNORECASE):
        return None
    return cleaned


def _validate_job_title(title: Optional[str], company_name: Optional[str] = None) -> Optional[str]:
    """Cleans common ATS title wrappers and rejects non-job headings."""
    cleaned = _clean_str(title)
    if not cleaned:
        return None

    app_match = re.match(r"^job\s+application\s+for\s+(.+?)(?:\s+at\s+.+)?$", cleaned, re.IGNORECASE)
    if app_match:
        cleaned = app_match.group(1).strip()

    cleaned = re.sub(
        r"\s*[\|\-–—]\s*(?:apply\s+now|careers|jobs|job\s+details|open\s+positions)\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()
    if company_name:
        cleaned = re.sub(
            rf"\s*[\|\-–—]\s*{re.escape(company_name)}\s*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

    if not cleaned or len(cleaned) < 3 or len(cleaned) > 140:
        return None

    lower = cleaned.lower()
    if lower in NON_JOB_TITLES:
        return None
    if company_name and lower == company_name.lower():
        return None
    if re.match(
        r"^(?:careers|jobs|join\s+us|work\s+(?:at|with)\s+us|search\s+jobs|current\s+openings|"
        r"open\s+positions|apply\s+(?:now|for)|403\b|404\b|500\b|error\b)",
        lower,
    ):
        return None

    return cleaned


def _validate_location(loc: Optional[str]) -> Optional[str]:
    """Rejects UI filter labels, boilerplate prompts, and oversized location dumps."""
    cleaned = _clean_str(loc)
    if not cleaned or len(cleaned) < 2 or len(cleaned) > 85:
        return None

    lower = cleaned.lower().rstrip(":")
    if lower in {"location", "locations", "where", "office", "offices", "country", "region", "n/a", "tbd"}:
        return None
    if any(
        bad in lower
        for bad in ("select ", "choose ", "filter ", "search ", "view all", "relocation", "cookie", "sign in", "apply")
    ):
        return None
    if cleaned.count(",") > 5:
        return None

    return cleaned


def _find_job_posting_jsonld(soup: BeautifulSoup) -> dict[str, Any]:
    """Recursively locates the richest schema.org JobPosting object in any ld+json script."""
    candidates: list[dict[str, Any]] = []

    def search(node: Any) -> None:
        if isinstance(node, dict):
            node_type = node.get("@type")
            if node_type == "JobPosting" or (
                isinstance(node_type, list) and "JobPosting" in node_type
            ):
                candidates.append(node)
            for val in node.values():
                search(val)
        elif isinstance(node, list):
            for item in node:
                search(item)

    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        for attempt in (raw.strip(), html.unescape(raw.strip())):
            try:
                data = json.loads(attempt)
                search(data)
                break
            except (json.JSONDecodeError, RecursionError):
                continue

    if not candidates:
        return {}
    return max(candidates, key=lambda d: len(d))


def _extract_meta(soup: BeautifulSoup) -> dict[str, str]:
    """Extracts meta tags regardless of whether 'name' or 'property' is used."""
    meta: dict[str, str] = {}
    for tag in soup.find_all("meta"):
        key = _clean_str(tag.get("property") or tag.get("name"))
        content = _clean_str(tag.get("content"))
        if key and content:
            meta[key.lower()] = content
    return meta

def _extract_deadline_from_text(text: Optional[str], reference_date: Optional[date] = None) -> Optional[date]:
    """Internal alias delegating to extract_deadline."""
    return extract_deadline(text, reference_date)


def _sanitize_fragment(fragment: Tag | BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    """Removes forms, scripts, and non-href attributes, returning (plain_text, clean_html)."""
    clean_soup = BeautifulSoup(str(fragment), "html.parser")
    for junk in clean_soup(["script", "style", "form", "input", "select", "textarea", "button", "svg"]):
        junk.decompose()

    for tag in clean_soup.find_all(True):
        allowed = {"href"} if tag.name == "a" else set()
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed}

    plain = _clean_multiline(clean_soup.get_text("\n", strip=True))
    raw_clean = _clean_str(str(clean_soup))
    if not plain or not raw_clean:
        return None, None
    return plain, raw_clean


def _find_dom_description(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str], bool]:
    """
    Finds the main description container in rendered HTML.
    Returns (plain_text, clean_html, matched_specific_selector).
    """
    specific_selectors = [
        '[data-automation-id="jobPostingDescription"]',
        "#job-description",
        ".job-desc",
        ".job-description",
        '[data-qa="job-description"]',
        '[itemprop="description"]',
        '[class*="job-description"]',
        '[class*="jobDescription"]',
    ]
    for sel in specific_selectors:
        found = soup.select_one(sel)
        if found and len(found.get_text(strip=True)) >= MIN_DESCRIPTION_CHARS:
            plain, raw_clean = _sanitize_fragment(found)
            if plain and raw_clean and MIN_DESCRIPTION_CHARS <= len(plain) <= MAX_DESCRIPTION_CHARS:
                return plain, raw_clean, True

    if not soup.body:
        return None, None, False

    body_clone = BeautifulSoup(str(soup.body), "html.parser")
    for noise in body_clone(["script", "style", "nav", "header", "footer", "aside", "form"]):
        noise.decompose()
    for hidden in body_clone.select(
        '[aria-hidden="true"], [hidden], .p-popup-notification, '
        '[id*="cookie"], [class*="cookie"], [id*="consent"], [class*="consent"], '
        '[role="dialog"], [aria-modal="true"]'
    ):
        hidden.decompose()

    for sel in ("article", "main"):
        found = body_clone.select_one(sel)
        if found and len(found.get_text(strip=True)) >= MIN_DESCRIPTION_CHARS:
            plain, raw_clean = _sanitize_fragment(found)
            if plain and raw_clean and _looks_like_job_description(plain):
                return plain, raw_clean, False

    best_score = 0.0
    candidate: Optional[Tag] = None
    for div in body_clone.find_all(["div", "section"]):
        text_len = len(div.get_text(" ", strip=True))
        if text_len < MIN_DESCRIPTION_CHARS or text_len > MAX_DESCRIPTION_CHARS:
            continue
        link_len = sum(len(a.get_text(strip=True)) for a in div.find_all("a"))
        bullet_bonus = len(div.find_all("li")) * 40
        link_ratio = link_len / max(text_len, 1)
        if link_ratio > 0.25:
            continue
        score = (text_len + bullet_bonus) * (1.0 - link_ratio) / (
            1.0 + len(div.find_all("div")) * 0.15
        )
        if score > best_score:
            best_score = score
            candidate = div

    if not candidate:
        return None, None, False

    plain, raw_clean = _sanitize_fragment(candidate)
    if plain and raw_clean and _looks_like_job_description(plain):
        return plain, raw_clean, False

    return None, None, False


def _extract_dom_description(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    """Finds the main description container in rendered HTML and returns (plain_text, clean_html)."""
    plain, raw_clean, _ = _find_dom_description(soup)
    return plain, raw_clean


def _company_from_url(raw_url: Optional[str]) -> Optional[str]:
    """Extracts a validated company name from ATS URLs or direct corporate career domains."""
    if not raw_url:
        return None
    try:
        parsed = urlparse(raw_url)
        host = (parsed.hostname or "").lower()
        path_parts = [p for p in parsed.path.split("/") if p]
    except ValueError:
        return None

    if not host:
        return None

    if any(host.endswith(domain) for domain in SUBDOMAIN_ATS_DOMAINS):
        tenant = host.split(".")[0]
        if tenant and tenant not in GENERIC_SLUGS:
            return _validate_company_name(tenant.replace("-", " ").title())
        return None

    if any(host.endswith(domain) for domain in PATH_ATS_DOMAINS):
        for seg in path_parts:
            if seg.lower() not in GENERIC_SLUGS:
                return _validate_company_name(seg.replace("-", " ").title())
        return None

    parts = [p for p in host.split(".") if p not in {"www", "careers", "jobs", "apply"}]
    if len(parts) >= 2:
        brand = parts[-2]
        if brand not in NON_COMPANY_NAMES and brand not in {"co", "com", "org", "net", "gov", "ac"}:
            return _validate_company_name(brand.replace("-", " ").title())

    return None


def _extract_location(soup: BeautifulSoup, jsonld: dict[str, Any]) -> Optional[str]:
    """Extracts validated location from JSON-LD (including TELECOMMUTE) or scoped DOM."""
    locations: list[str] = []
    raw_loc = jsonld.get("jobLocation")
    loc_items = raw_loc if isinstance(raw_loc, list) else ([raw_loc] if raw_loc else [])

    for loc in loc_items:
        if isinstance(loc, str):
            cleaned = _validate_location(loc)
            if cleaned:
                locations.append(cleaned)
        elif isinstance(loc, dict):
            addr = loc.get("address")
            if isinstance(addr, str):
                cleaned = _validate_location(addr)
                if cleaned:
                    locations.append(cleaned)
            elif isinstance(addr, dict):
                parts = [
                    _clean_str(addr.get("addressLocality")),
                    _clean_str(addr.get("addressRegion")),
                    _clean_str(addr.get("addressCountry")),
                ]
                joined = _validate_location(", ".join(p for p in parts if p))
                if joined:
                    locations.append(joined)

    unique_locs = list(dict.fromkeys(locations))
    if unique_locs:
        if len(unique_locs) <= 3:
            return "; ".join(unique_locs)
        return f"{'; '.join(unique_locs[:3])} (+{len(unique_locs) - 3} more)"

    is_remote = (_clean_str(jsonld.get("jobLocationType")) or "").upper() == "TELECOMMUTE"

    main_area = soup.find("main") or soup.body
    if main_area:
        loc_el = main_area.select_one(
            '[data-automation-id="locations"], #details .p-muted-heading, [class*="job-location"], [class*="location"]'
        )
        if loc_el and not loc_el.find_parent(["header", "nav", "footer"]):
            candidate_loc = _validate_location(loc_el.get_text(" ", strip=True))
            if candidate_loc:
                return candidate_loc

    if is_remote:
        reqs = jsonld.get("applicantLocationRequirements")
        req_items = reqs if isinstance(reqs, list) else ([reqs] if reqs else [])
        countries = [
            _clean_str(r.get("name")) if isinstance(r, dict) else _clean_str(r)
            for r in req_items
        ]
        countries = [c for c in countries if c and len(c) <= 40]
        if 1 <= len(countries) <= 3:
            return f"Remote ({', '.join(countries)})"
        return "Remote"

    return None


def scrape_job_html(
    raw_html: str,
    url: Optional[str] = None,
    assume_salary: bool = False,
) -> dict[str, Any]:
    """
    Safely parses job posting HTML into a dictionary.
    Missing, ambiguous, or low-confidence fields return None rather than garbage values.
    'salary' returns None or {'lb': int, 'ub': Optional[int], 'currency': str, 'period': Optional[str]}.
    """
    file_mtime = date.today()
    empty_result: dict[str, Any] = {
        "job_title": None,
        "job_description": None,
        "job_description_html": None,
        "salary": None,
        "deadline": None,
        "posted": None,
        "company_name": None,
        "job_location": None,
    }

    if not isinstance(raw_html, str) or not raw_html.strip():
        return empty_result

    # Plain-text / Markdown fallback when non-HTML text is supplied
    if not re.search(r"<(html|body|div|p|h1|script|meta)\b", raw_html, re.IGNORECASE):
        if _is_blocked_or_closed_page(raw_html, raw_html, has_jsonld=False):
            return empty_result
        plain_body = _clean_multiline(raw_html)
        if not _looks_like_job_description(plain_body):
            return empty_result
        lines = [line.strip() for line in raw_html.splitlines() if line.strip()]
        raw_title = re.sub(r"^#+\s*", "", lines[0]) if lines else None
        company_name = _company_from_url(url)
        return {
            **empty_result,
            "job_title": _validate_job_title(raw_title, company_name),
            "job_description": plain_body,
            "job_description_html": f"<div><p>{html.escape(plain_body)}</p></div>" if plain_body else None,
            "company_name": company_name,
            "salary": extract_salary(plain_body, {}, assume_salary=assume_salary),
            "deadline": _extract_deadline_from_text(plain_body, file_mtime),
        }

    soup = BeautifulSoup(raw_html, "html.parser")
    jsonld = _find_job_posting_jsonld(soup)
    visible_text = soup.get_text(" ", strip=True)

    if _is_blocked_or_closed_page(raw_html, visible_text, has_jsonld=bool(jsonld)):
        return empty_result

    meta = _extract_meta(soup)
    canonical = soup.find("link", rel="canonical")
    canonical_href = _clean_str(canonical.get("href")) if canonical else None
    resolved_url = canonical_href or meta.get("og:url") or url

    # 1. Company Name
    org = jsonld.get("hiringOrganization")
    raw_company = _clean_str(org.get("name")) if isinstance(org, dict) else _clean_str(org)
    company_name = _validate_company_name(raw_company)

    if not company_name:
        company_name = _validate_company_name(meta.get("og:site_name"))

    if not company_name:
        company_name = _company_from_url(resolved_url) or _company_from_url(url)

    # 2. Job Title (ignore <h1> tags sitting inside site header/nav)
    h1: Optional[Tag] = None
    for candidate_h1 in (soup.find("main") or soup).find_all("h1"):
        if not candidate_h1.find_parent(["header", "nav", "footer"]):
            h1 = candidate_h1
            break

    raw_title = (
        _clean_str(jsonld.get("title"))
        or _clean_str(h1.get_text(" ", strip=True) if h1 else None)
        or _clean_str(meta.get("og:title"))
        or _clean_str(meta.get("title"))
        or _clean_str(soup.title.get_text(" ", strip=True) if soup.title else None)
    )
    job_title = _validate_job_title(raw_title, company_name)

    # 3. Description (JSON-LD -> Specific DOM -> Validated Generic DOM; never short meta blurbs)
    job_description: Optional[str] = None
    job_description_html: Optional[str] = None

    raw_jsonld_desc = _clean_str(jsonld.get("description"))
    jsonld_desc = html.unescape(raw_jsonld_desc).strip() if raw_jsonld_desc else None
    jsonld_text: Optional[str] = None
    jsonld_html: Optional[str] = None

    if jsonld_desc:
        if re.search(r"<(p|ul|li|div|br|strong|h[1-6])\b", jsonld_desc, re.IGNORECASE):
            jsonld_text, jsonld_html = _sanitize_fragment(BeautifulSoup(jsonld_desc, "html.parser"))
        else:
            jsonld_text = _clean_multiline(jsonld_desc)
            jsonld_html = f"<div><p>{html.escape(jsonld_text)}</p></div>" if jsonld_text else None

    if jsonld_text and (len(jsonld_text) < MIN_DESCRIPTION_CHARS or len(jsonld_text) > MAX_DESCRIPTION_CHARS):
        jsonld_text, jsonld_html = None, None

    dom_text, dom_html, is_specific_dom = _find_dom_description(soup)

    if jsonld_text and jsonld_html:
        if is_specific_dom and dom_text and dom_html and len(dom_text) > len(jsonld_text) * 1.5:
            job_description, job_description_html = dom_text, dom_html
        else:
            job_description, job_description_html = jsonld_text, jsonld_html
    elif dom_text and dom_html:
        job_description, job_description_html = dom_text, dom_html

    # 4. Job Location
    job_location = _extract_location(soup, jsonld)

    # 5. Dates (Posted & Deadline)
    posted = _parse_date_safe(jsonld.get("datePosted"), file_mtime)
    deadline = (
        _parse_date_safe(jsonld.get("validThrough"), file_mtime)
        or _extract_deadline_from_text(job_description, file_mtime)
    )
    if posted and deadline and deadline < posted:
        deadline = None

    # 6. Salary
    salary = extract_salary(job_description, jsonld, assume_salary=assume_salary)

    return {
        "job_title": job_title,
        "job_description": job_description,
        "job_description_html": job_description_html,
        "salary": salary,
        "deadline": deadline,
        "posted": posted,
        "company_name": company_name,
        "location_name": job_location,
    }
#me do hmm yes
def _manual_search(url):
    with (requests.Session() as session):
        session.headers.update(Processor.headers)
        response = session.get(
            url,
            timeout=30,
            allow_redirects=True
        )
        if response.status_code == 200:
            return response.text
        else:
            return ""

def _soup_response(raw_webpage):
    data = scrape_job_html(raw_webpage)
    required_fields = ("job_title", "company_name", "location_name", "job_description")
    missing = [k for k in required_fields if not data.get(k)]

    desc = data.get("job_description") or ""
    if "job_description" not in missing and len(desc) < 250:
        missing.append("job_description_too_short")
    return data if not missing else None


class Scraper(Processor):
    # Generic Web Scraper.
    ducky = DDGS(timeout=15)
    fc = Firecrawl(settings.SECRETS["firecrawl"])

    @staticmethod
    def discover(search_term:str,limit=200) -> int:
        # Discover should be the main scraping operation:
        # For some search term, look over all job listings (up to limit) for matches to this criteria
        # Save those jobs as complete / incomplete items to the database
        pass

    @staticmethod
    def evaluate(job):
        url = job.url
        def save_from_soup(data):
            job.description = data["job_description"]
            job.title = data["job_title"]
            if data["salary"]:
                job.set_salary(**data["salary"])
            else:
                job.set_salary(35000)
            job.deadline = data["deadline"] or date(3000,1,1)
            job.posted = data["posted"] or date(3000,1,1)
            job.company = Company.fetch(data["company_name"])
            job.location = PreciseLocation.fetch(data["location_name"])
            if "job_description_html" in data:
                job.description_html = data["job_description_html"]
            job.evaluate()
            return True,""

        data = _soup_response(_manual_search(url))
        if data is not None:
            return save_from_soup(data)

        try:
            data = _soup_response(Scraper.ducky.extract(url,"text")["content"])
            if data is not None:
                return save_from_soup(data)
        except Exception as e:
            print(e)
            pass

        try:
            doc = Scraper.fc.scrape(
                url,
                only_main_content=False,
                max_age=172800000,
                formats=["rawHtml"],
            )
        except Exception as e:
            print("Job could not be saved", e)
            job.status= "X"
            return
        raw_html = getattr(doc, "raw_html", None) or getattr(doc, "html", None)
        data = _soup_response(raw_html)
        if data is not None:
            return save_from_soup(data)

        fo = open("C:/JONATHAN/careers/hmm.html","r")
        j = fo.readlines()
        fo.close()
        txt = "".join(j)
        soup = BeautifulSoup(txt, "html.parser")
        for junk in soup(["head", "script", "style", "svg", "nav", "header", "footer", "aside", "form", "noscript"]):
            junk.decompose()
        clean_txt = _clean_str(soup.get_text())
        data = llm_manager.prompt(clean_txt,"scrape_html")
        data = json.loads(data)
        return save_from_soup(data)
