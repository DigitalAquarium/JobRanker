import html
from datetime import datetime, timedelta
from typing import Optional, Any

from bs4 import BeautifulSoup

from jobs.models import *
from time import time

class Processor:
    # Interface for different methods of acquiring jobs!
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",

        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/jxl,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",

        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",

        "Cache-Control": "max-age=0",
        "DNT": "1",

        "Priority": "u=0, i",

        "Sec-CH-UA": '"Not:A-Brand";v="8", "Chromium";v="156", "Google Chrome";v="156"',
        "Sec-CH-UA-Mobile": "?0",
        "Sec-CH-UA-Platform": '"Windows"',

        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",

        "Upgrade-Insecure-Requests": "1",
    }

    unevaluated_jobs_cache = {"count": Job.objects.filter(status="N").count(), "last_polled": time(),
                              "remaining_checks": 100}

    @staticmethod
    def check_job_cache():
        timeout = 120
        if Processor.unevaluated_jobs_cache["remaining_checks"] <= 0:
            Processor.unevaluated_jobs_cache = {"count": Job.objects.filter(status="N").count(), "last_polled": time(),
                                                "remaining_checks": 100}
        elif time() - Processor.unevaluated_jobs_cache["last_polled"] > timeout:
            Processor.unevaluated_jobs_cache = {"count": Job.objects.filter(status="N").count(), "last_polled": time(),
                                                "remaining_checks": 100}
        return Processor.unevaluated_jobs_cache["count"]

    @staticmethod
    def discover(search_term: str, limit: int = 200, level: str = "") -> int:
        # Discover should be the main scraping operation:
        # For some search term, look over all job listings (up to limit) for matches to this criteria
        # Save those jobs as complete / incomplete items to the database
        # Return number of jobs added
        pass

    @staticmethod
    def evaluate(job: Job) -> tuple[bool, str]:  #
        # This should be the main operation to finalise all details within a specific job
        # Open up the URL for the job and get the full information, after that save it to the db and return success.
        pass





SUPPORTED_SALARY_CURRENCIES = {
    "GBP", "USD", "EUR", "CAD", "AUD", "CHF", "SGD", "NZD",
    "SEK", "NOK", "DKK", "ISK",
}

CURRENCY_BOUND_SCALE = {
    "SEK": 15,
    "NOK": 15,
    "DKK": 10,
    "ISK": 200,
}

SYMBOL_TO_CURRENCY = {
    "£": "GBP",
    "€": "EUR",
    "US$": "USD",
    "$": "USD",
    "CA$": "CAD",
    "C$": "CAD",
    "AU$": "AUD",
    "A$": "AUD",
    "NZ$": "NZD",
    "S$": "SGD",
}

def clean_str(val: Any) -> Optional[str]:
    """Safely coerces values to a whitespace-normalized string, returning None if empty/invalid."""
    if val is None:
        return None
    if isinstance(val, list):
        return clean_str(val[0]) if val else None
    if isinstance(val, (str, int, float)):
        cleaned = re.sub(r"\s+", " ", str(val)).strip()
        return cleaned if cleaned else None
    return None

def _normalize_api_text(text: Optional[str]) -> Optional[str]:
    """Unescapes HTML entities and strips light markup if an API returns rich text."""
    if not text:
        return None
    unescaped = html.unescape(text)
    if "<" in unescaped and ">" in unescaped:
        unescaped = BeautifulSoup(unescaped, "html.parser").get_text(" ", strip=True)
    return clean_str(unescaped)


def parse_date_safe(val: Any, reference_date: Optional[date] = None) -> Optional[date]:
    """Parses ISO, relative, natural-language, and UK-style (DD/MM/YYYY) numeric dates."""
    text = clean_str(val)
    if not text:
        return None

    ref = reference_date.date() if isinstance(reference_date, datetime) else (reference_date or date.today())
    parsed: Optional[date] = None

    # 1. Year-first numeric format (YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD)
    ymd_match = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", text)
    if ymd_match:
        try:
            parsed = date(int(ymd_match.group(1)), int(ymd_match.group(2)), int(ymd_match.group(3)))
        except ValueError:
            parsed = None

    # 2. UK-first numeric format (DD/MM/YYYY, DD.MM.YYYY, DD-MM-YYYY, DD/MM/YY)
    if parsed is None:
        dmy_match = re.search(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b", text)
        if dmy_match:
            normalized_dmy = f"{dmy_match.group(1)}/{dmy_match.group(2)}/{dmy_match.group(3)}"
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    parsed = datetime.strptime(normalized_dmy, fmt).date()
                    break
                except ValueError:
                    continue

    # 3. Relative dates ("3 days ago", "today", "yesterday")
    if parsed is None:
        lower = text.lower()
        if "today" in lower or "just posted" in lower:
            parsed = ref
        elif "yesterday" in lower:
            parsed = ref - timedelta(days=1)
        else:
            rel_match = re.search(r"\b(\d{1,3})\s+(day|week|month)s?\s+ago\b", lower)
            if rel_match:
                num, unit = int(rel_match.group(1)), rel_match.group(2)
                days = num * {"day": 1, "week": 7, "month": 30}[unit]
                try:
                    parsed = ref - timedelta(days=days)
                except OverflowError:
                    return None

    # 4. Natural dates like "Monday 4th January 2027", "4 Jan 2027", or "January 4, 2027"
    if parsed is None:
        cleaned = re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", r"\1", text)
        for fmt in ("%A %d %B %Y", "%d %B %Y", "%d %b %Y", "%B %d, %Y", "%b %d, %Y"):
            try:
                parsed = datetime.strptime(cleaned.strip(), fmt).date()
                break
            except ValueError:
                continue

    if parsed is None or parsed.year < 2015 or parsed.year > ref.year + 2:
        return None

    return parsed


def _normalize_currency(raw_curr: Optional[str]) -> Optional[str]:
    """Maps a currency symbol or ISO code to a supported 3-letter ISO currency code."""
    cleaned = clean_str(raw_curr)
    if not cleaned:
        return None
    if cleaned in SYMBOL_TO_CURRENCY:
        return SYMBOL_TO_CURRENCY[cleaned]
    upper = cleaned.upper()
    if upper in SYMBOL_TO_CURRENCY:
        return SYMBOL_TO_CURRENCY[upper]
    if upper in SUPPORTED_SALARY_CURRENCIES:
        return upper
    return None


def _normalize_period(raw_period: Optional[str]) -> Optional[str]:
    """Maps JSON-LD unitText or prose qualifiers to Job.set_salary's expected period strings."""
    cleaned = clean_str(raw_period)
    if not cleaned:
        return None
    lower = cleaned.lower().strip(" ./")
    if any(k in lower for k in ("hour", "hr", "tim")):
        return "hourly"
    if any(k in lower for k in ("day", "daily", "dag")):
        return "daily"
    if any(k in lower for k in ("week", "wk", "vecka", "uke", "uge")):
        return "weekly"
    if any(k in lower for k in ("month", "mo", "mån", "md", "måned")):
        return "monthly"
    if any(k in lower for k in ("year", "yr", "annum", "annual", "p.a", "pa", "år")):
        return "yearly"
    return None


def _parse_amount_token(raw_val: Any) -> Optional[int]:
    """Parses numeric salary tokens such as '45,000', '45 000', '45.000', or '45.5k' into int."""
    if isinstance(raw_val, (int, float)):
        if math.isfinite(raw_val) and raw_val > 0:
            return int(round(raw_val))
        return None

    cleaned = clean_str(raw_val)
    if not cleaned:
        return None

    token = cleaned.lower().replace(" ", "")
    is_k = token.endswith("k")
    if is_k:
        token = token[:-1]

    if not is_k and re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token):
        token = token.replace(".", "")
    else:
        token = token.replace(",", "")

    try:
        num = float(token)
    except ValueError:
        return None

    if not math.isfinite(num) or num <= 0:
        return None

    return int(round(num * 1000)) if is_k else int(round(num))


def _validate_salary_payload(
    lb: Optional[int],
    ub: Optional[int],
    currency: Optional[str],
    period: Optional[str],
    min_unanchored_base: int = 500,
) -> Optional[dict[str, Any]]:
    """Validates bounds, currency, and period before returning a Job.set_salary kwargs dict."""
    if lb is None or not currency or currency not in SUPPORTED_SALARY_CURRENCIES:
        return None
    if ub is not None and ub < lb:
        return None

    scale = CURRENCY_BOUND_SCALE.get(currency, 1)
    bounds_by_period = {
        "hourly": (5, 1_000),
        "daily": (40, 5_000),
        "weekly": (150, 25_000),
        "monthly": (500, 100_000),
        "yearly": (8_000, 2_000_000),
        None: (min_unanchored_base, 2_000_000),
    }
    min_ok, max_ok = bounds_by_period.get(period, (min_unanchored_base, 2_000_000))
    min_ok *= scale
    max_ok *= scale

    if not (min_ok <= lb <= max_ok):
        return None
    if ub is not None and not (min_ok <= ub <= max_ok * 1.5):
        return None

    return {
        "lb": lb,
        "ub": ub,
        "currency": currency,
        "period": period,
    }


def _extract_salary(
    text: Optional[str],
    jsonld: dict[str, Any],
    assume_salary: bool = False,
) -> Optional[dict[str, Any]]:
    """
    Extracts structured salary kwargs (lb, ub, currency, period) compatible with Job.set_salary().
    When assume_salary=True, standalone 5-figure+ currency amounts without a 'Salary:' label or
    period unit are also accepted as salaries.
    """
    base_salary = jsonld.get("baseSalary")
    if isinstance(base_salary, list) and base_salary:
        base_salary = base_salary[0]

    if isinstance(base_salary, dict) and base_salary:
        currency = _normalize_currency(base_salary.get("currency"))
        val = base_salary.get("value")
        lb: Optional[int] = None
        ub: Optional[int] = None
        period: Optional[str] = None

        if isinstance(val, dict):
            currency = currency or _normalize_currency(val.get("currency"))
            period = _normalize_period(val.get("unitText") or base_salary.get("unitText"))
            if val.get("minValue") is not None or val.get("maxValue") is not None:
                lb = _parse_amount_token(val.get("minValue"))
                ub = _parse_amount_token(val.get("maxValue"))
                if lb is None and ub is not None:
                    lb, ub = ub, None
            else:
                lb = _parse_amount_token(val.get("value"))
        else:
            lb = _parse_amount_token(val)
            period = _normalize_period(base_salary.get("unitText"))

        validated = _validate_salary_payload(lb, ub, currency, period)
        if validated:
            return validated

    if not text:
        return None

    iso_codes = "|".join(sorted(SUPPORTED_SALARY_CURRENCIES))
    sym_tokens = r"(?:US\$|CA\$|AU\$|NZ\$|C\$|A\$|S\$|[£$€])"
    curr_token = rf"(?:{sym_tokens}|(?:{iso_codes})\b)"
    num_token = r"(?:\d{1,3}(?:[,\s.]\d{3})+|\d+(?:\.\d+)?\s?k|\d{2,7})"
    range_sep = r"\s*(?:[-–—]|to)\s*"
    period_body = (
        r"per\s+(?:year|annum|month|week|day|hour)|"
        r"p\.?a\.?|/\s*(?:yr|year|mo|month|wk|week|day|hr|hour|mån|md)|"
        r"\b(?:annually|yearly|monthly|weekly|daily|hourly)\b"
    )
    label_token = r"(?:salary|compensation|pay|remuneration|base|package|ote|rate|stipend|lön|lønn|løn)"
    non_salary_prefix = r"(?<!budget\s)(?<!revenue\s)(?<!funding\s)(?<!credits\s)(?<!worth\s)"

    anchored_patterns = [
        # 1. Currency before number, anchored by compensation label ("Salary: £45,000 - £55,000")
        re.compile(
            rf"{label_token}\s*(?:range|is|of)?\s*[:\-–]?\s*"
            rf"(?P<curr>{curr_token})\s*(?P<lb>{num_token})"
            rf"(?:{range_sep}(?:{curr_token})?\s*(?P<ub>{num_token}))?"
            rf"(?:\s*(?P<period>{period_body}))?",
            re.IGNORECASE,
        ),
        # 2. Currency before number, anchored by explicit period ("£45,000 - £55,000 per year", "$40/hr")
        re.compile(
            rf"{non_salary_prefix}(?P<curr>{curr_token})\s*(?P<lb>{num_token})"
            rf"(?:{range_sep}(?:{curr_token})?\s*(?P<ub>{num_token}))?"
            rf"\s*(?P<period>{period_body})",
            re.IGNORECASE,
        ),
        # 3. Number before ISO currency code ("45 000 - 55 000 SEK/month", "550 000 NOK per year")
        re.compile(
            rf"{non_salary_prefix}(?P<lb>{num_token})"
            rf"(?:{range_sep}(?P<ub>{num_token}))?\s*"
            rf"(?P<curr>{iso_codes})\b"
            rf"(?:\s*(?P<period>{period_body}))?",
            re.IGNORECASE,
        ),
    ]

    for pattern in anchored_patterns:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groupdict()
        currency = _normalize_currency(groups.get("curr"))
        lb = _parse_amount_token(groups.get("lb"))
        ub = _parse_amount_token(groups.get("ub"))
        period = _normalize_period(groups.get("period"))

        validated = _validate_salary_payload(lb, ub, currency, period)
        if validated:
            return validated

    # 4. Trusted-description fallback: accept standalone 5-figure+ currency amounts/ranges
    if assume_salary:
        non_salary_suffix = (
            r"(?!\s*(?:in\s+)?(?:budget|allowance|bonus|credits|grant|relocation|"
            r"stipend|revenue|funding|series\s+[a-d]|voucher)s?\b)"
        )
        unanchored_patterns = [
            re.compile(
                rf"{non_salary_prefix}(?P<curr>{curr_token})\s*(?P<lb>{num_token})"
                rf"(?:{range_sep}(?:{curr_token})?\s*(?P<ub>{num_token}))?"
                rf"{non_salary_suffix}",
                re.IGNORECASE,
            ),
            re.compile(
                rf"{non_salary_prefix}(?P<lb>{num_token})"
                rf"(?:{range_sep}(?P<ub>{num_token}))?\s*"
                rf"(?P<curr>{iso_codes})\b"
                rf"{non_salary_suffix}",
                re.IGNORECASE,
            ),
        ]
        for pattern in unanchored_patterns:
            for match in pattern.finditer(text):
                groups = match.groupdict()
                currency = _normalize_currency(groups.get("curr"))
                lb = _parse_amount_token(groups.get("lb"))
                ub = _parse_amount_token(groups.get("ub"))
                validated = _validate_salary_payload(
                    lb, ub, currency, period=None, min_unanchored_base=10_000
                )
                if validated:
                    return validated

    return None


def extract_salary(
    text: Optional[str],
    jsonld: Optional[dict[str, Any]] = None,
    assume_salary: bool = False,
) -> Optional[dict[str, Any]]:
    """Public helper for plaintext or HTML-encoded descriptions (e.g., from ATS APIs)."""
    return _extract_salary(_normalize_api_text(text), jsonld or {}, assume_salary=assume_salary)


def extract_deadline(text: Optional[str], reference_date: Optional[date] = None) -> Optional[date]:
    """Extracts explicit closing dates in UK numeric, ISO, day-first, or month-first formats."""
    cleaned = _normalize_api_text(text)
    if not cleaned:
        return None

    weekday = r"(?:(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s*)?"
    day_first = r"\d{1,2}(?:st|nd|rd|th)?\s+[A-Z][a-z]+\s+\d{4}"
    month_first = r"[A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}"
    ymd_date = r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"
    uk_numeric = r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}"

    match = re.search(
        r"(?:close(?:s|d)?(?:\s+for\s+applications)?|closing\s+date|application\s+deadline|deadline|apply\s+(?:by|before))"
        r"(?!\s+(?:clicking|submitting|sending|visiting|email|online))"
        rf"[^.\n!?]{{0,50}}?\b({weekday}(?:{day_first}|{month_first})|{ymd_date}|{uk_numeric})\b",
        cleaned,
        re.IGNORECASE,
    )
    if match:
        return parse_date_safe(match.group(1), reference_date)
    return None