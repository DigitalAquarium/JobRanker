#from django.shortcuts import render
from jobs.processors import reed

# Create your views here.
def test_view(request):
    reed.discover()
    print("discovery ended")
    return None