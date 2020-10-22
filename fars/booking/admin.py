from django.contrib import admin
from django.apps import apps

# Register your models here.

from .models import Bookable
from .forms import BookableForm

class BookableAdmin(admin.ModelAdmin):
    form = BookableForm

admin.site.register(Bookable, BookableAdmin)


models = apps.get_models()
for model in models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
