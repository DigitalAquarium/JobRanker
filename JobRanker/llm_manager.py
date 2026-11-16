#from os import environ
from datetime import date
from typing import Literal, Optional

from openai import OpenAI, RateLimitError
from JobRanker.settings import SECRETS
from JobRanker.rate_limit_manager import Limiter
from pydantic import BaseModel, Field

GEMINI_KEY = SECRETS["gemini"]

gemini_endpoint = OpenAI(api_key=GEMINI_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/",timeout=60)
groq_endpoint = OpenAI(api_key=SECRETS["groq"], base_url="https://api.groq.com/openai/v1",timeout=60)

models = [{"name":"gemini-3.5-flash-lite","endpoint":gemini_endpoint,"rate_limit":15,"reasoning_effort":"minimal"},
          {"name":"openai/gpt-oss-20b","endpoint":groq_endpoint,"rate_limit":30,"reasoning_effort":"low"},
          {"name":"gemini-3.6-flash","endpoint":gemini_endpoint,"rate_limit":5,"reasoning_effort":"minimal"},
          {"name":"openai/gpt-oss-120b","endpoint":groq_endpoint,"rate_limit":30,"reasoning_effort":"low"},
          {"name":"qwen/qwen3.8-27b","endpoint":groq_endpoint,"rate_limit":30,"reasoning_effort":"none"},
          {"name":"gemini-3.8-flash","endpoint":gemini_endpoint,"rate_limit":5,"reasoning_effort":"low"},
          {"name":"gemini-3.1-flash-lite","endpoint":gemini_endpoint,"rate_limit":15,"reasoning_effort":"minimal"},
          {"name":"gemini-2.5-flash","endpoint":gemini_endpoint,"rate_limit":15,"reasoning_effort":"minimal"},
          {"name": "gemini-2.5-flash-lite", "endpoint": gemini_endpoint, "rate_limit": 15, "reasoning_effort": "none"},
]

model = models.pop(0)
l = Limiter(model["rate_limit"])

class SalarySchema(BaseModel):
    lb:Optional[int] = Field(description="If salary is given in a range, this should be the lower bound, otherwise salary value. default to 35,000 if not found")
    ub: Optional[int] = Field(description="upper bound for salary, None if single value")
    currency:Optional[str] = Field(default="GBP",description="Three-letter uppercase ISO currency code (e.g. GBP, USD, EUR, SEK). Assume GBP if not found")
    period: Optional[Literal["hourly", "daily", "weekly", "monthly", "yearly"]] = Field(description="period of pay, if not found assume a sensible value for a graduate based on the salary number. most likely yearly for UK-based roles")

class JobSchema(BaseModel):
    job_title:Optional[str] = Field(description="Exact role title, or null if not a job posting.")
    job_description:Optional[str] = Field(description="Clean summary/body of the role, or null if missing.")
    salary: Optional[SalarySchema]
    deadline: Optional[date] = Field(description="Application Closing Date posted in YYYY-MM-DD format, or null if not stated.")
    posted: Optional[date] = Field(description="Date posted in YYYY-MM-DD format, or null if not stated.")
    company_name:Optional[str] = Field(description="Hiring employer name, or null if unknown.")
    location_name: Optional[str] = Field(description="job's location. choose 1 closest to london. as precise as possible otherwise City/country or 'Remote'. null if unspecified.")


def prompt(content, prompt_type="company", arg_prompt=""):
    global model
    flag = True
    match prompt_type:
        case "company":
            dev_prompt = "You are an assistant for a user who is currently searching for work. Your role is to take a " \
                         "user-provided organisation (company or civil) name in the IT/Software/Tech sector (should operate in the UK, but may not) and " \
                         "provide a summary of it. The first section should cover the company's main product or " \
                         "service, then separate with a newline (\\n) the second section should be the companies core values and culture."\
                         "DO NOT include markdown, headers or metadata in the response. simply the two statements separated by a newline. After this you " \
                         "MUST include a pipe character (|) followed by the url of the main page of the company's " \
                         "website. Only use the one pipe character to separate the description from the website DO " \
                         "NOT use any others."
        case "location":
            dev_prompt = "Your job is to take a user give place-name or post-code in the united kingdom and convert it into JUST the " \
                         "town/city (or county if not possible) this place is in to reduce out the total number of possible locations to simplify " \
                         "storage. If it cannot be narrowed down as there's not enough info, a simple county name or " \
                         "'united kingdom' should be output. In some rare cases, the place may be outside the uk, in that case simply output the country.\n For london specifically you MUST specify either 'north london', " \
                         "'south london', 'east london', 'west london' or 'central london'.\n In cases where multiple locations are listed, pick the one closest to london.\n Examples of how this works are as follows:\n 'morden' should output 'south london', " \
                         "'selly oak' should output 'birmingham', 'London, England, United Kingdom' should output"\
                         "'central london', and 'oldham, manchester' should output 'manchester'."\
                         "After this, you MUST produce a pipe character (|) followed by a single 'bit' 1/0. The value of this is true if the output is the name of a country, and false otherwise."
        case "custom":
            dev_prompt = arg_prompt
        case "scrape_html":
            dev_prompt = "Your job is to read the text content of a jobs listing webpage and digest the contents into the storable format provided."
            kwargs = {"model":model["name"],
                        "reasoning_effort":model["reasoning_effort"],
                        "temperature":0,
                        "messages":[
                            {"role": "system", "content": dev_prompt},
                            {"role": "user", "content": content}
                        ],
                      "response_format":JobSchema,
                      }
            flag=False
        case _:
            dev_prompt = ""

    while len(models) > 0:
        retrys = 2
        complete = False
        while retrys > 0:
            l.wait()
            print("Asking",model["name"],"About:", content if len(content) < 150 else content[:144])
            try:
                if flag:
                    response = model["endpoint"].chat.completions.create(
                        model=model["name"],
                        reasoning_effort=model["reasoning_effort"],
                        temperature=0,
                        stream=False,
                        messages=[
                            {"role": "system", "content": dev_prompt},
                            {"role": "user", "content": content}
                        ]
                    )
                else:
                    response = model["endpoint"].chat.completions.parse(**kwargs)
                complete=True
                break
            except RateLimitError:
                print("Rate Limit / Quota!")
                break
            except Exception as e:
                print(e)
                retrys -= 1
        if complete:
            break
        else:
            model = models.pop(0)
            l.rpm = model["rate_limit"]

    print("Got Answer")
    return response.choices[0].message.content.replace("\n", "")
