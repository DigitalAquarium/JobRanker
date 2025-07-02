from cv_library import *
from gradcracker import *
from linkedin import *
from reed import *
from otta import *

# TODO: Welcome to the Jungle? glassdoor, Indeed. GRB??

run_otta()
run_reed()
run_cv_library()
run_gradcracker()
run_linkedin()

job_list = list(jobs.jobs)
job_list.sort()

for j in job_list:
    print(j.title, "-", j.company + ":", j.rank, j.url)

# ScrollOrigin
while True:
    print("Script Ended")
    time.sleep(6000)
