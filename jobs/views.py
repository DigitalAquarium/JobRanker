#from django.shortcuts import render
from jobs.models import *
from jobs.processors.reed import Reed

# Create your views here.
def test_view(request):
    Reed.discover("cyber security")
    jobs = []
    for j in Job.objects.all():
        Reed.evaluate(j)
        jobs.append(j)
    Job.objects.bulk_update(jobs,["title","description","description_html","rank","status","salary","deadline","posted","location","company"])
    print("discovery ended")
    #for j in Job.objects.all():

    return None