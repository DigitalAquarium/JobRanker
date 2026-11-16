import requests
import json
'''SECRETS = {}
fo = open(".secrets","r")
for line in fo:
    x = line.split(",")
    SECRETS[x[0]] = x[1].replace("\n","")
fo.close()

headers = {
    "Authorization": f"Bearer {SECRETS['bright_data']}",
    "Content-Type": "application/json",
}

data = json.dumps({
    "input": [{"location":"London","country":"GB","time_range":"Any time","keyword":"Cyber Security Placement","company":"","location_radius":""}],
    "limit_per_input": 10,
})

response = requests.post(
    "https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lpfll7v5hcqtkxl6l&notify=false&include_errors=true&type=discover_new&discover_by=keyword&limit_per_input=1",
    headers=headers,
    data=data
)
print(response)
print(response.json())'''


response = requests.get("https://www.gradcracker.com/search/technology-it/cyber-security-work-placements-internships?order=deadlines")
print(response)

