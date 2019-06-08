from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext as _
from datetime import timedelta
from booking.metadata_forms import METADATA_FORM_OPTIONS, METADATA_FORM_CLASSES

alphanumeric = RegexValidator(r'^[0-9a-zA-Z]*$', _('Only alphanumeric characters are allowed.'))


class Bookable(models.Model):
    # unique ID string used in the URL
    id_str = models.CharField(max_length=32, unique=True, validators=[alphanumeric])
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    icon = models.CharField(max_length=32, default='tf.svg')
    public = models.BooleanField(default=False)
    
    # How far in the future bookings are allowed (zero means no limit)
    forward_limit_days = models.PositiveIntegerField(default = 0)
    
    # How long bookings are allowed to be (zero means no limit)
    length_limit_hours = models.PositiveIntegerField(default = 0)
    metadata_form = models.CharField(max_length=2, null=True, blank=True, default=None, choices=METADATA_FORM_OPTIONS)
    
    # Groups that may be used to make group bookings for this bookable
    allowed_booker_groups = models.ManyToManyField(Group, blank=True, related_name='groupbooking')
    
    # Bookings for this bookable are restricted to members of these groups. 
    # If no groups are defined, any authenticated user may book.
    booking_restriction_groups = models.ManyToManyField(Group, blank=True, related_name='restricted')

    def __str__(self):
        return self.name

    @property
    def admin_group_name(self):
        return '{}_admin'.format(self.id_str)

    def get_metadata_form(self, data=None):
        if self.metadata_form in METADATA_FORM_CLASSES:
            return METADATA_FORM_CLASSES[self.metadata_form](data)
        else:
            return None


@receiver(post_save, sender=Bookable)
def create_bookable_group(sender, instance, **kwargs):
    Group.objects.get_or_create(name=instance.admin_group_name)


@receiver(post_delete, sender=Bookable)
def delete_bookable_group(sender, instance, **kwargs):
    Group.objects.get(name=instance.admin_group_name).delete()


# class TimeSlot(models.Model):
#     start = models.CharField(null=False)
#     end = models.CharField(max_length=8, null=False)
#     bookable = models.ForeignKey(max_length=8, Bookable, on_delete=models.CASCADE)


class RepeatedBookingGroup(models.Model):
    name = models.CharField(max_length=128)

    def delete_from_date_forward(self, date):
        bookings = self.booking_set.filter(start__gte=date)
        bookings.delete()


class Booking(models.Model):
    bookable = models.ForeignKey(Bookable, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateTimeField(_("start"))
    end = models.DateTimeField(_("end"))
    comment = models.CharField(_("comment"), max_length=128)
    repeatgroup = models.ForeignKey(RepeatedBookingGroup, null=True, on_delete=models.CASCADE, default=None)
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

        # Check that booking group is allowed
        if self.booking_group and self.booking_group not in self.get_booker_groups():
            raise ValidationError(_("Group booking is not allowed with the provided user and group"))
