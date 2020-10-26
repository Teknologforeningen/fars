from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _
from datetime import timedelta, datetime
import time

import logging

# These are the choices used in the bookable model.
# Adding your metadata form here will make it available for bookables.
# The codes here must correspond to codes in METADATA_FORM_CLASSES defined in metadata_form.py
METADATA_FORM_OPTIONS = (
    (None, 'No metadata'),
    ('PI', 'Pi sauna'),
    ('HB', 'Humpsbadet'),
)

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', _('Only alphanumeric characters are allowed.'))
logger = logging.getLogger(__name__)


class Bookable(models.Model):
    # unique ID string used in the URL
    id_str = models.CharField(max_length=32, unique=True, validators=[alphanumeric], help_text=_('Unique ID string used in the URL'))
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    icon = models.CharField(max_length=32, default='tf.svg')
    public = models.BooleanField(default=False)

    # Hides the bookable in the home view
    hidden = models.BooleanField(default=False, help_text=_('Hides the bookable in the home view'))
    
    # How far in the future bookings are allowed (zero means no limit)
    forward_limit_days = models.PositiveIntegerField(default = 0, help_text=_('How far in the future bookings are allowed (zero means no limit)'))
    
    # How long bookings are allowed to be (zero means no limit)
    length_limit_hours = models.PositiveIntegerField(default = 0, help_text=_('How long bookings are allowed to be (zero means no limit)'))
    metadata_form = models.CharField(max_length=2, null=True, blank=True, default=None, choices=METADATA_FORM_OPTIONS)
    
    # Groups that may be used to make group bookings for this bookable
    allowed_booker_groups = models.ManyToManyField(Group, blank=True, related_name='groupbooking', help_text=_('Groups that may be used to make group bookings for this bookable.'))
    
    # Bookings for this bookable are restricted to members of these groups. 
    # If no groups are defined, any authenticated user may book.
    booking_restriction_groups = models.ManyToManyField(Group, blank=True, related_name='restricted', help_text=_('Bookings for this bookable are restricted to members of these groups. If no groups are defined, any authenticated user may book.'))

    # Groups that have admin rights to this bookable
    admin_groups = models.ManyToManyField(Group, blank=True, related_name='admin', help_text=_('Groups that have admin rights to this bookable.'))

    # BILL device ID if BILL check is needed. If null no BILL check will be performed
    bill_device_id = models.PositiveIntegerField(null=True, blank=True, default=None, help_text=_('BILL device ID if BILL check is needed. If empty no BILL check will be performed'))

    def __str__(self):
        return self.name

    # It would be better if this was non-blocking
    def notify_external_services(self):
        from requests_futures.sessions import FuturesSession
        session = FuturesSession(max_workers=4)
        for service in ExternalService.objects.filter(bookable__id=self.id):
            service.notify(session)

    def has_bookable_timeslots(self):
        if Timeslot.objects.filter(bookable=self).count() > 0: return True
        return False

    def get_start_slots(self, query=None):
        if query is None:
            timeslots = Timeslot.objects.filter(bookable=self)
        else:
            timeslots = query
        return [ts.get_start() for ts in timeslots]

    def get_end_slots(self, query=None):
        if query is None:
            timeslots = Timeslot.objects.filter(bookable=self)
        else:
            timeslots = query
        return [ts.get_end() for ts in timeslots]

    def get_bookable_timeslots_by_start_and_end_time(self):
        timeslot_query = Timeslot.objects.filter(bookable=self)
        return [self.get_start_slots(query=timeslot_query), self.get_end_slots(query=timeslot_query)]

    def get_closest_start_datetime(self, dt, query=None):
        if query is None:
            timeslot_query = Timeslot.objects.filter(bookable=self)
        else:
            timeslot_query = query
        timestamps = [ts.get_closest_start_datetime(dt) for ts in timeslot_query]

        valid_start_timestamps = list(map(lambda ts: ts + timedelta(days=7) if ts <= datetime.now(dt.tzinfo) else ts, timestamps))
        # Calculate the timedelta to dt timestamp for each datetime object
        start_timedeltas = list(map(lambda ts: (ts - dt).total_seconds(), valid_start_timestamps))
        # Find the closest valid match and return the timestamp that matches that index
        closest_index = start_timedeltas.index(min(start_timedeltas, key=abs))
        return valid_start_timestamps[closest_index]

    def get_closest_end_datetime(self, dt, booking_start_dt, query=None):
        if query is None:
            timeslot_query = Timeslot.objects.filter(bookable=self)
        else:
            timeslot_query = query
        timestamps = [ts.get_closest_end_datetime(dt) for ts in timeslot_query]

        valid_end_timestamps = list(map(lambda ts: ts + timedelta(days=7) if ts <= booking_start_dt else ts, timestamps))
        # Calculate the timedelta to dt timestamp for each datetime object
        end_timedeltas = list(map(lambda ts: (ts - dt).total_seconds(), valid_end_timestamps))
        # Find the closest valid match and return the timestamp that matches that index
        closest_index = end_timedeltas.index(min(end_timedeltas, key=abs))
        return valid_end_timestamps[closest_index]

    def get_closest_start_and_end_datetime(self, start_dt, end_dt):
        timeslot_query = Timeslot.objects.filter(bookable=self)
        closest_start_datetime = self.get_closest_start_datetime(start_dt, timeslot_query)
        closest_end_datetime = self.get_closest_end_datetime(end_dt, closest_start_datetime, timeslot_query)
        return ( closest_start_datetime, closest_end_datetime, )


def convert_time_to_closest_datetime(timestamp, datetimestamp):
    # timestamp = time struct https://docs.python.org/3/library/time.html#time.struct_time
    # datetimestamp = datetime object https://docs.python.org/3/library/datetime.html#datetime-objects
    # This function returns a datetime object of the timeslot string regarding the received datetime object (dt)
    # The converted datetime object has the same weekday, hour and minute as the time struct
    return (datetimestamp + timedelta(timestamp.tm_wday - datetimestamp.weekday())).replace(hour=timestamp.tm_hour, minute=timestamp.tm_min)

class Timeslot(models.Model):
    class Weekdays(models.TextChoices):
        MON = 'Mon', _('Monday')
        TUE = 'Tue', _('Tuesday')
        WED = 'Wed', _('Wednesday')
        THU = 'Thu', _('Thursday')
        FRI = 'Fri', _('Friday')
        SAT = 'Sat', _('Saturday')
        SUN = 'Sun', _('Sunday')
        
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)
    start_time = models.TimeField(auto_now=False, auto_now_add=False)
    start_weekday = models.CharField(
        max_length=3,
        choices=Weekdays.choices,
    )
    end_time = models.TimeField(auto_now=False, auto_now_add=False)
    end_weekday = models.CharField(
        max_length=3,
        choices=Weekdays.choices,
    )

    def get_start(self):
        return f"{self.start_weekday} {self.start_time.strftime('%H:%M')}"

    def get_start_t(self):
        # Returns start time as a python time struct
        # https://docs.python.org/3/library/time.html#time.struct_time
        return time.strptime(self.get_start(), "%a %H:%M")

    def get_end(self):
        return f"{self.end_weekday} {self.end_time.strftime('%H:%M')}"

    def get_end_t(self):
        # Returns end time as a python time struct
        # https://docs.python.org/3/library/time.html#time.struct_time
        return time.strptime(self.get_end(), "%a %H:%M")

    def get_closest_start_datetime(self, dt):
        return convert_time_to_closest_datetime(self.get_start_t(), dt)

    def get_closest_end_datetime(self, dt):
        return convert_time_to_closest_datetime(self.get_end_t(), dt)


class ExternalService(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)
    callback_url = models.CharField(max_length=256, null=False, blank=False)

    def __str__(self):
        return self.name

    def notify(self, session):
        try:
            session.get(str(self.callback_url))
        except Exception as e:
            # Avoid crashes from this
            logger.error('Error notifying external service "{}" with URL {}: {}'.format(self.name, self.callback_url, str(e)))


class RepeatedBookingGroup(models.Model):
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

    def delete_from_date_forward(self, date):
        bookings = self.booking_set.filter(start__gte=date)
        bookings.delete()


class Booking(models.Model):
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateTimeField(_("start"))
    end = models.DateTimeField(_("end"))
    comment = models.CharField(_("comment"), max_length=128)
    repeatgroup = models.ForeignKey(RepeatedBookingGroup, blank=True, null=True, on_delete=models.CASCADE, default=None)
    metadata = models.CharField(max_length=256, blank=True, null=True, default=None)
    booking_group = models.ForeignKey(Group, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _("Booking")
        verbose_name_plural = _("Bookings")
        ordering = ["start"]

    def __str__(self):
        return "{}, {}".format(self.comment, self.start.strftime("%Y-%m-%d %H:%M"))

    def get_booker_groups(self):
        allowed_groups = []
        if self.bookable_id is not None:
            allowed_groups = self.bookable.allowed_booker_groups.all()
            if self.user_id is not None:
               allowed_groups = allowed_groups.filter(id__in=self.user.groups.all()) 

        return allowed_groups

    def get_overlapping_bookings(self):
        overlapping = Booking.objects.filter(
            bookable=self.bookable,
            start__lt=self.end,
            end__gt=self.start
            )
        return list(overlapping)

    def clean(self):
        # Check that end is not earlier than start
        if self.end <= self.start:
            raise ValidationError(_("Booking cannot end before it begins"))

        # Check that the booking's start and end times are on the defined booking slots, if the bookable has such defined
        if self.bookable.has_bookable_timeslots():
            start_times, end_times = self.bookable.get_bookable_timeslots_by_start_and_end_time()
            if self.start.strftime("%a %H:%M") not in start_times:
                raise ValidationError(_("Booking start time is not according to the predefined booking timeslots."))
            if self.end.strftime("%a %H:%M") not in end_times:
                raise ValidationError(_("Booking end time is not according to the predefined booking timeslots."))

        # Check that booking group is allowed
        if self.booking_group and self.booking_group not in self.get_booker_groups():
            raise ValidationError(_("Group booking is not allowed with the provided user and group"))
