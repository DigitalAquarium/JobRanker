from cv_library import *
from gradcracker import *
from linkedin import *
from reed import *
from otta import *
from eFinancialCareers import *


# TODO: glassdoor, Indeed. GRB??

#run_otta,run_cv_library,
async def main():
    tasks = []
    for func in [run_e_financial_careers,  run_reed,  run_gradcracker, run_linkedin]:
        tasks.append(asyncio.create_task(func()))
    for task in tasks:
        await task


asyncio.run(main())

job_list = list(jobs.jobs)
job_list.sort()

for j in job_list:
    print(j.title, "-", j.company + ":", j.rank, j.url)

# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(6000)
