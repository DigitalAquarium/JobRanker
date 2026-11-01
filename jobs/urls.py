from django.urls import path

from . import views
from django.contrib.sitemaps.views import sitemap
from jobs.models import *

urlpatterns = [
    path('', views.test_view, name='index')
    ]