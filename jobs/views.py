#from django.shortcuts import render
from jobs.models import *
from jobs.processors.reed import Reed

# Create your views here.
def test_view(request):
    #Reed.discover("cyber security")
    for j in Job.objects.all():
        Reed.evaluate(j)
    print("discovery ended")
    #for j in Job.objects.all():

    return None