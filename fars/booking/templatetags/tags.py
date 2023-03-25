from django import template
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def modulo(num, val):
    return num % val
