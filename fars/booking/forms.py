from django import forms
from booking.models import Booking, RepeatedBookingGroup, Bookable
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput, NumberInput, DateInput
from datetime import datetime, timedelta, date
from django.utils.translation import gettext as _
from django.db import transaction


class DateTimeWidget(forms.widgets.MultiWidget):
    def __init__(self, attrs=None):
        widgets = [forms.TextInput(attrs={'type': 'date'}),
                   forms.TextInput(attrs={'type': 'time'})]
        super(DateTimeWidget, self).__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return [value.date(), value.time()]
        else:
            return ['', '']


class DateTimeField(forms.fields.MultiValueField):
    widget = DateTimeWidget

    def __init__(self, *args, **kwargs):
        list_fields = [forms.fields.DateField(),
                       forms.fields.TimeField()]
        super(DateTimeField, self).__init__(list_fields, *args, **kwargs)

    def compress(self, values):
        return datetime.strptime("{}T{}".format(*values), "%Y-%m-%dT%H:%M:%S")


class BookingForm(forms.ModelForm):
    start = DateTimeField()
    end = DateTimeField()

    def __init__(self, *args, **kwargs):
        super(BookingForm, self).__init__(*args, **kwargs)
        allowed_booker_groups = self.instance.get_booker_groups()
        self.fields['booking_group'].choices = \
            [(None, _('Private booking'))] + [(group.id, group.name) for group in allowed_booker_groups]

    class Meta:
        model = Booking
        fields = '__all__'
        exclude = ['repeatgroup']
        widgets = {
            'bookable': forms.HiddenInput(),
            'user': forms.HiddenInput(),
            'comment': forms.TextInput(attrs={'autocomplete': 'off'})
        }

    def clean_start(self):
        start = self.cleaned_data['start']
        # If start is in the past, make it "now"
        return datetime.now() if start < datetime.now() else start

    def clean(self):
        cleaned_data = super().clean()
        bookable = cleaned_data.get("bookable")
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        user = cleaned_data.get('user')
        group = cleaned_data.get('booking_group')

        # Check that user has permissions to book bookable
        restriction_groups = bookable.booking_restriction_groups.all()
        if not user.is_superuser and restriction_groups and not user.groups.filter(id__in=restriction_groups).exists():
            raise forms.ValidationError(_("You do not have permissions to book this bookable"))

        if bookable and start and end:
            # Check that booking does not violate bookable forward limit
            if bookable.forward_limit_days > 0 and datetime.now() + timedelta(days=bookable.forward_limit_days) < end:
                raise forms.ValidationError(
                    _("{} may not be booked more than {} days in advance").format(bookable.name, bookable.forward_limit_days)
                )

            # Check that booking does not violate bookable length limit
            booking_length = (end - start)
            booking_length_hours = booking_length.days * 24 + booking_length.seconds / 3600
            if bookable.length_limit_hours > 0 and booking_length_hours > bookable.length_limit_hours:
                raise forms.ValidationError(
                    _("{} may not be booked for longer than {} hours").format(bookable.name, bookable.length_limit_hours)
                )

            # Check that booking does not overlap with previous bookings
            overlapping = Booking.objects.filter(bookable=bookable, start__lt=end, end__gt=start)
            if overlapping:
                warning = _("Error: Requested booking is overlapping with the following bookings:")
                errors = [forms.ValidationError(warning)]
                for booking in overlapping:
                    errors.append(forms.ValidationError('• ' + str(booking)))
                raise forms.ValidationError(errors)

        return cleaned_data

    def get_metadata_field_names(self):
        return []

    def metadata_fields(self):
        return [self[k] for k in self.get_metadata_field_names()]

    def get_cleaned_metadata(self):
        metadata_field_names = self.get_metadata_field_names()
        return None if not metadata_field_names else {k: self.cleaned_data[k] for k in metadata_field_names}


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'class':'validate offset-2 col-8','placeholder': 'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'class':'offset-2 col-8','placeholder':'Password'}))


class RepeatingBookingForm(forms.Form):
    frequency = forms.IntegerField(label=_('Frequency of repetitions (in days)'), initial=7)
    repeat_until = forms.DateField(initial=date.today() + timedelta(days=365), widget=DateInput(attrs={'type': 'date'}))

    # creates all bookings in a repeated booking
    def save_repeating_booking_group(self, booking):
        data = self.cleaned_data
        group = RepeatedBookingGroup.objects.create(name=booking.comment)
        group.save()
        booking.repeatgroup = group
        skipped_bookings = []
        frequency = data.get('frequency')
        repeat_until = data.get('repeat_until')

        # Copy booking for every repetition
        while(booking.start.date() <= repeat_until):
            overlapping = booking.get_overlapping_bookings()
            if overlapping:
                skipped_bookings.append(str(booking))
            else:
                booking.save()
            booking.pk = None
            booking.start += timedelta(days=frequency)
            booking.end += timedelta(days=frequency)

        return skipped_bookings

