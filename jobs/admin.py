from django.contrib import admin

from jobs.models import *


# Register your models here.
@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    search_fields = ['title']
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    search_fields = ['name']
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(PreciseLocation)
class PreciseLocationAdmin(admin.ModelAdmin):
    search_fields = ['name']


