from urllib.parse import urlencode
from django.utils import timezone
from django.utils.translation import gettext as _
from fars.settings import FARS_BASE_URL
from booking.models import Booking

def create_gcal_url(booking: Booking):
    user = booking.user
    name = f"{user.first_name} {user.last_name}".strip() or user.username

    details = f"{_('Booking of')} {booking.bookable.name} {_('by')} {name}"
    if booking.booking_group:
        details += f" [{booking.booking_group.name}]"
    if FARS_BASE_URL:
        details += f" {_('at')} {FARS_BASE_URL}/booking/{booking.bookable.id_str}/{booking.start.strftime('%Y-%m-%d')}"

    # Available parameters: https://github.com/InteractionDesignFoundation/add-event-to-calendar-docs/blob/main/services/google.md
    params = {
        "text": f"{booking.comment} ({booking.bookable.name})",
        "dates": f"{booking.start.strftime('%Y%m%dT%H%M%SZ')}/{booking.end.strftime('%Y%m%dT%H%M%SZ')}",
        "ctz": timezone.get_current_timezone(),
        "details": details,
    }

    return f"https://calendar.google.com/calendar/r/eventedit?{urlencode(params)}"
