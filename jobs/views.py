#from django.shortcuts import render
import datetime

from django.db.models import Model
from django.shortcuts import render, redirect

from JobRanker import llm_manager
from jobs import manager
from jobs.models import *
from jobs.models import Company, Location
from jobs.processors.adzuna import Adzuna
from jobs.processors.reed import Reed
from jobs.processors.scraper import Scraper


# Create your views here.
def test_view(request):
    manager.evaluate()
    return "hello :)"

def rank_view(request,pk=0):
    if pk:
        job = Job.objects.get(pk=pk)
        init_rank = job.rank
        while job.deadline and job.deadline < date.today():
            job.status = "X"
            job.save()
            job = Job.objects.filter(status="E",rank__lte=init_rank).order_by("-rank")[0]
    else:
        job = Job.objects.filter(status="E").order_by("-rank")[0]
        while job.deadline and job.deadline < date.today():
            job.status = "X"
            job.save()
            job = Job.objects.filter(status="E").order_by("-rank")[0]

    next_job = Job.objects.filter(status="E",rank__lt=job.rank).order_by("-rank")[0]
    while next_job.deadline and next_job.deadline < date.today():
        next_job.status = "X"
        next_job.save()
        job = Job.objects.filter(status="E", rank__lt=job.rank).order_by("-rank")[0]

    data = {
        "id":job.id,
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
        "has_posted":job.posted != Job.DATE_DEFAULT,
        "has_deadline": job.deadline != Job.DATE_DEFAULT,
        "next":next_job.id,
    }


    return render(request,"job.html", data)

def intend_apply_view(_,job_id):
    job = Job.objects.get(pk=job_id)
    job.status = "I"
    job.save()
    return redirect("rank")

def ignore_view(_,job_id):
    job = Job.objects.get(pk=job_id)
    job.status = "M"
    job.save()
    return redirect("rank")