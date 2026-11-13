#from django.shortcuts import render
import datetime

from django.db.models import Model
from django.shortcuts import render

from jobs import manager
from jobs.models import *
from jobs.models import Company, Location
from jobs.processors.adzuna import Adzuna
from jobs.processors.reed import Reed

# Create your views here.
def test_view(request):
    #manager.discover()
    manager.evaluate()
    print("discovery ended")
    #for j in Job.objects.all():

    return None

def rank_view(request,pk=0):
    if pk:
        job = Job.objects.get(pk=0)
    else:
        job = Job.objects.filter(status="E").order_by("-rank")[0]
        while job.deadline and job.deadline < date.today():
            job.status = "X"
            job.save()
            job = Job.objects.filter(status="E").order_by("-rank")[0]


    data = {
        "title":job.title,
        "description":job.description_html if job.description_html != "" else job.description.replace("\n", "<br>"),
        "url": job.url,
        "company": job.company,
        "company_summary":job.company.summary.replace("\n", "<br>"),
        "company_url":job.company.url,
        "precise_location":job.location.name,
        "location":job.location.location.name,
        "posted":job.posted,
        "deadline":job.deadline,
        "salary":job.salary,
    }


    return render(request,"job.html", data)