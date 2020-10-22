from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import time
import json

WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

def validate_booking_slot(value):
    if value == "": return
    try:
        time.strptime(value, "%a %H:%M")
    except ValueError:
        raise ValidationError(_("Invalid timestamp given for timeslot!"))

def validate_booking_slots(value):
    booking_slots = json.loads(value.replace("'",'"'))
    for slot in booking_slots:
        try:
            start, end = slot
        except:
            raise ValidationError(_("Invalid values given to booking slot!"))

        if start == end:
            raise ValidationError(_("Booking slot start and end cannot be the same."))
        validate_booking_slot(start)
        validate_booking_slot(end)