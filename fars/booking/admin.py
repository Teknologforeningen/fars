from django.contrib import admin
from django.apps import apps

# Register your models here.

from .models import Bookable, Timeslot

class TimeslotInline(admin.TabularInline):
    model = Timeslot
    fields = ("start_weekday", "start_time", "end_weekday", "end_time",)


class BookableAdmin(admin.ModelAdmin):
    inlines = [
        TimeslotInline,
    ]

admin.site.register(Bookable, BookableAdmin)


models = apps.get_models()
for model in models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
