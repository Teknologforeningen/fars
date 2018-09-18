from django import forms
from booking.models import Booking
from django.contrib.auth.forms import AuthenticationForm
from django.forms.widgets import PasswordInput, TextInput
from datetime import datetime, timedelta


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

    class Meta:
        model = Booking
        fields = '__all__'
        widgets = {
            'bookable': forms.HiddenInput(),
            'user': forms.HiddenInput(),
        }

    def clean_start(self):
        start = self.cleaned_data['start']
        # If start is in the past, make it "now"
        return datetime.now() if start < datetime.now() else start

    def clean_end(self):
        end = self.cleaned_data['end']
        # Check that booking is not in the past
        if end <= datetime.now():
            raise forms.ValidationError("Booking may not be in the past")
        return end

    def clean(self):
        cleaned_data = super().clean()
        bookable = cleaned_data.get("bookable")
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")

        if bookable and start and end:
            # Check that end is not earlier than start
            if end <= start:
                raise forms.ValidationError("Booking cannot end before it begins")

            # Check that booking does not violate bookable limits
            if bookable.forward_limit_days > 0 and datetime.now() + timedelta(days=bookable.forward_limit_days) < end:
                raise forms.ValidationError(
                    "{} may not be booked more than {} days in advance".format(
                        bookable.name, bookable.forward_limit_days
                    )
                )

            booking_length = (end - start)
            booking_length_hours = booking_length.days * 24 + booking_length.seconds / 3600
            if bookable.length_limit_hours > 0 and booking_length_hours > bookable.length_limit_hours:
                raise forms.ValidationError(
                    "{} may not be booked for longer than {} hours".format(bookable.name, bookable.length_limit_hours)
                )

            # Check that booking does not overlap with previous bookings
            overlapping = Booking.objects.filter(
                bookable=bookable, start__lt=end, end__gt=start)
            if overlapping:
                warning = "Error: Requested booking is overlapping with the following bookings:"
                errors = [forms.ValidationError(warning)]
                for booking in overlapping:
                    errors.append(forms.ValidationError('• ' + str(booking)))
                raise forms.ValidationError(errors)


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=TextInput(attrs={'class':'validate offset-2 col-8','placeholder': 'Username'}))
    password = forms.CharField(widget=PasswordInput(attrs={'class':'offset-2 col-8','placeholder':'Password'}))
