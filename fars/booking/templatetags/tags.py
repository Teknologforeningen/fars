from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def modulo(num, val):
    return num % val

@register.filter
def is_bookablestaff(user, bookable):
    groupname = "{}_admin".format(bookable.id_str)
    groupmembers = User.objects.filter(groups__name=groupname)
    
    if user in groupmembers:
        return True
    else:
        return user.is_superuser
