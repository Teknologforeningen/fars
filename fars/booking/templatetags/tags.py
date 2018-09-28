from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def modulo(num, val):
    return num % val

@register.filter
def is_bookableadmin(user, bookable):
    groupname = "{}_admin".format(bookable.id_str)
    groupmembers = User.objects.filter(groups__name=groupname)

    if user in groupmembers or user.is_superuser:
        return True
    return False
