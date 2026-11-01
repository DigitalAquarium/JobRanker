#Created With Heavy Help From ChatGPT

import json
from bs4 import BeautifulSoup
import requests
url = "https://www.adzuna.co.uk/jobs/land/ad/5944221475?se=Ju6x7aDV8RGGCOFuy44SDg&utm_medium=api&utm_source=1ef98434&v=DCD5237510CE7CF6038BEA6A95C5E446D7D8CF33"
url = url.split("?")
job_id = url[0].split("/")
job_id = job_id[-1]
url = "https://www.adzuna.co.uk/jobs/details/"+job_id

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


def fetch_adzuna_page(url):

    with requests.Session() as session:

        session.headers.update(headers)

        response = session.get(
            url,
            timeout=(10, 30),
            allow_redirects=True
        )

        print("Status:", response.status_code)
        print("Final URL:", response.url)
        print("Content-Type:", response.headers.get("Content-Type"))
        print("Response length:", len(response.content))
        print("Redirects:", len(response.history))

        response.raise_for_status()

        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    details = None

    # Find the embedded az_details JavaScript object
    for script in soup.find_all("script"):

        js = script.string or script.get_text()

        marker = 'window["az_details"]'
        position = js.find(marker)

        if position == -1:
            continue

        equals = js.find("=", position)

        if equals == -1:
            continue

        # Extract the JSON object following the equals sign
        raw = js[equals + 1:].lstrip()

        try:
            details, _ = json.JSONDecoder().raw_decode(raw)
            break
        except json.JSONDecodeError:
            continue

    if not details:
        raise ValueError("Could not locate Adzuna job details")

    # Convert HTML description into readable text
    description_html = details.get("description", "")

    description_text = BeautifulSoup(
        description_html,
        "html.parser"
    ).get_text("\n", strip=True)

    return {
        "id": details.get("id"),
        "title": details.get("title"),
        "company": details.get("company"),
        "salary": details.get("salary"),
        "description_html": description_html,
        "description": description_text,
        "location": details.get("location_raw"),
        "category": details.get("category_name"),
        "source_id": details.get("source_id")
    }


print(fetch_adzuna_page(url)["description"])
