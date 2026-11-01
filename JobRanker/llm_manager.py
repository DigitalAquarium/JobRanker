#from os import environ
from openai import OpenAI
from JobRanker.settings import SECRETS
from time import time, sleep

GEMINI_KEY = SECRETS["gemini"]

gemini_endpoint = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/",timeout=60)
groq_endpoint = OpenAI(api_key=SECRETS["groq"], base_url="https://api.groq.com/openai/v1")

models = [{"name":"openai/gpt-oss-120b","endpoint":groq_endpoint,"rate_limit":30},
          {"name":"gemini-2.5-flash-lite","endpoint":gemini_endpoint,"rate_limit":15},
          {"name":"gemini-3.5-flash-lite","endpoint":gemini_endpoint,"rate_limit":15},
          {"name":"gemini-3.1-flash-lite","endpoint":gemini_endpoint,"rate_limit":15},
          {"name":"gemini-2.5-flash","endpoint":gemini_endpoint,"rate_limit":15},
          {"name":"openai/gpt-oss-20b","endpoint":groq_endpoint,"rate_limit":30},
          {"name":"qwen/qwen3.8-27b","endpoint":groq_endpoint,"rate_limit":30},
          {"name":"gemini-3.6-flash","endpoint":gemini_endpoint,"rate_limit":5},
          {"name":"gemini-3.8-flash","endpoint":gemini_endpoint,"rate_limit":5},
]

last_polled = time()
model = models.pop(0)

def prompt(content, prompt_type="company", arg_prompt=""):
    global model
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
                         "town/city (or county if not possible) this place is in to reduce out the total number of possible locations to simplify " \
                         "storage. If it cannot be narrowed down as there's not enough info, a simple county name or " \
                         "'United Kingdom' is ok. In some rare cases, the place may be outside the uk, in that case simply output the country.\n For london specifically you MUST specify either 'north london', " \
                         "'south london', 'east london', 'west london' or 'central london'.\n In cases where multiple locations are listed, pick the one closest to london.\n Examples of how this works are as follows:\n 'morden' should output 'south london', " \
                         "'selly oak' should output 'birmingham', 'London, England, United Kingdom' should output"\
                         "'central london', and 'oldham, manchester' should output 'manchester'"
        case "custom":
            dev_prompt = arg_prompt
        case _:
            dev_prompt = ""

    while len(models) > 0:
        retrys = 2
        complete = False
        while retrys > 0:
            print("Asking",model["name"],"About:", content)
            interval = last_polled - time()
            grace = (model["rate_limit"] / 60) - interval
            if grace > -0.2:
                sleep(grace + 0.5)
            try:
                response = model["endpoint"].chat.completions.create(
                    model=model["name"],
                    reasoning_effort="low",
                    messages=[
                        {"role": "developer", "content": dev_prompt},
                        {"role": "user", "content": content}
                    ]
                )
                complete=True
                break
            except:
                retrys -= 1
        if complete:
            break
        else:
            model = models.pop(0)

    print("Got Answer")
    return response.choices[0].message.content.replace("\n", "")
