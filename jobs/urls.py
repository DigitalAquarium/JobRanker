from django.urls import path

from . import views
from django.contrib.sitemaps.views import sitemap
from jobs.models import *

urlpatterns = [
    path('', views.rank_view, name='rank'),
    path('<int:pk>', views.rank_view, name='rank_with_id'),
    path('crawl', views.test_view, name='crawl'),
    path('apply/<int:job_id>', views.intend_apply_view, name='intend_apply'),
    path('ignore/<int:job_id>', views.ignore_view, name='ignore'),
    ]