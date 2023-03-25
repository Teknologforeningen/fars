from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.utils.translation import gettext as _
from datetime import timedelta

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

    @staticmethod
    def get_readable_bookables_for_user(user):
        bookables = Bookable.objects.all()

        # Show all bookables to staff
        if user.is_staff:
            return bookables

        # Only show public bookables if not logged in
        if not user.is_authenticated:
            return bookables.filter(public=True)

        # For authenticated users, show unhidden bookables and those that the user can make bookings on (part of restriction or admin group)
        return bookables.filter(
            Q(hidden=False) |
            Q(booking_restriction_groups__isnull=True) |
            Q(booking_restriction_groups__in=user.groups.all()) |
            Q(admin_groups__in=user.groups.all())
        )

    '''
    Check if this bookable is readable (can see bookings) for a certain user.
    '''
    def is_readable_for_user(self, user):
        # Only show public bookables if not logged in
        if not user.is_authenticated:
            return self.public

        if not self.hidden:
            return True

        return self.is_writable_for_user(user)

    '''
    Check if this bookable is writable (can make bookings) for a certain user.
    '''
    def is_writable_for_user(self, user):
        # Show all bookings to staff
        if user.is_staff:
            return True

        # Non-authenticated users can not make any bookings
        if not user.is_authenticated:
            return False

        # Authenticated users can make bookings on bookables with no restriction groups...
        if not self.booking_restriction_groups.count():
            return True

        # ...and on bookables where the user is part of restriction or admin group
        for group in user.groups.all():
            if group in self.booking_restriction_groups.all() or group in self.admin_groups.all():
                return True

        return False

    def __str__(self):
        return self.name

    # It would be better if this was non-blocking
    def notify_external_services(self):
        from requests_futures.sessions import FuturesSession
        session = FuturesSession(max_workers=4)
        for service in ExternalService.objects.filter(bookable__id=self.id):
            service.notify(session)

    def get_time_slots(self):
        return Timeslot.objects.filter(bookable=self)


def convert_time_to_closest_datetime(timestamp, datetimestamp):
    # timestamp = time struct https://docs.python.org/3/library/time.html#time.struct_time
    # datetimestamp = datetime object https://docs.python.org/3/library/datetime.html#datetime-objects
    # This function returns a datetime object of the timeslot string regarding the received datetime object (dt)
    # The converted datetime object has the same weekday, hour and minute as the time struct
    return (datetimestamp + timedelta(timestamp.tm_wday - datetimestamp.weekday())).replace(hour=timestamp.tm_hour, minute=timestamp.tm_min)

class Timeslot(models.Model):

    def __str__(self):
        return "{} {} - {} {}".format(self.start_weekday, self.start_time, self.end_weekday, self.end_time)

    class Weekdays(models.TextChoices):
        # ISO 8601
        MON = '1', _('Monday')
        TUE = '2', _('Tuesday')
        WED = '3', _('Wednesday')
        THU = '4', _('Thursday')
        FRI = '5', _('Friday')
        SAT = '6', _('Saturday')
        SUN = '7', _('Sunday')
        
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)
    start_time = models.TimeField(auto_now=False, auto_now_add=False)
    start_weekday = models.CharField(
        max_length=1,
        choices=Weekdays.choices,
    )
    end_time = models.TimeField(auto_now=False, auto_now_add=False)
    end_weekday = models.CharField(
        max_length=1,
        choices=Weekdays.choices,
    )


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

    @staticmethod
    def get_readable_bookings_for_user(user):
        bookings = Booking.objects.all()

        # Show all bookings to staff
        if user.is_staff:
            return bookings

        # Only show public bookables if not logged in
        if not user.is_authenticated:
            return bookings.filter(bookable__public=True)

        # For authenticated users, show bookings on unhidden bookables and on those bookables that the user can make bookings on (part of restriction or admin group)
        return bookings.filter(
            Q(bookable__hidden=False) |
            Q(bookable__booking_restriction_groups__isnull=True) |
            Q(bookable__booking_restriction_groups__in=user.groups.all()) |
            Q(bookable__admin_groups__in=user.groups.all())
        )

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

        # Check that the booking's start and end times match a defined booking slot if bookable has slots
        timeslots = self.bookable.get_time_slots()
        if timeslots.count() > 0:
            timeslots = timeslots.filter(end_weekday=self.end.isoweekday(), end_time=self.end.time())
            valid_slot_found = False
            for slot in timeslots:
                # Start time can be later than or equal to slot start time, which accounts for booking slots that have already started.
                if self.start.time() >= slot.start_time:
                    valid_slot_found = True
                    break
            if not valid_slot_found:
                raise ValidationError(_("Booking end time is not according to the predefined booking timeslots."))

        # Check that booking group is allowed
        if self.booking_group and self.booking_group not in self.get_booker_groups():
            raise ValidationError(_("Group booking is not allowed with the provided user and group"))
