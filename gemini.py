import asyncio
from os import environ
from openai import OpenAI
from time import time

OPENAI_KEY = environ["GEMINI_API_KEY"]

client = OpenAI(api_key=OPENAI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

last_polled = time()

timing_lock = asyncio.Lock()


async def prompt(content, prompt_type="company"):
    global last_polled
    async with timing_lock:
        if time() - last_polled < 4:
            await asyncio.sleep((time() - last_polled) + 0.1)
        last_polled = time()
    match prompt_type:
        case "company":
            dev_prompt = "You are an assistant for a user who is currently searching for work. Your role is to take a " \
                         "user-provided company name in the IT/Software/Tech sector (that operates in the UK) and " \
                         "provide a summary of it. The first section should cover the company's main product or " \
                         "service, the second section should be the companies core values and culture. After this you " \
                         "MUST include a pipe character (|) followed by the url of the main page of the company's " \
                         "website. Only use the one pipe character to separate the description from the website DO " \
                         "NOT use any others"
        case "location":
            dev_prompt = "Your job is to take a user give place-name in the united kingdom and convert it into JUST the " \
                         "town/city this place is in to reduce out the total number of possible locations to simplify " \
                         "storage. If it cannot be narrowed down as there's not enough info, a simple county name or " \
                         "'United Kingdom' is ok. In some rare cases, the place may be outside the uk, in that case simply output the country.\n For london specifically you MUST specify either 'north london', " \
                         "'south london', 'east london', 'west london' or 'central london'.\n In cases where multiple location sare listed, pick the one closest to london.\n Examples of how this works are as follows:\n 'morden' should output 'south london', " \
                         "'selly oak' should output 'birmingham', 'London, England, United Kingdom' should output"\
                         "'central london', and 'oldham, manchester' should output 'manchester'"
        case _:
            dev_prompt = ""

    response = client.chat.completions.create(
        model="gemini-2.0-flash-lite",
        messages=[
            {"role": "developer", "content": dev_prompt},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content.replace("\n", "")
