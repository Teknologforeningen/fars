from django import forms
from booking.models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'
        widgets = {
            'bookable': forms.HiddenInput(),
            'start': forms.SplitDateTimeWidget(
                date_attrs={'type': 'date'}, time_attrs={'type': 'time'}),
            'end': forms.SplitDateTimeWidget(
                date_attrs={'type': 'date'}, time_attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        bookable = cleaned_data.get("bookable")
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")

        if bookable and start and end:
            overlapping = Booking.objects.filter(
                bookable=bookable, start__lt=end, end__gt=start)
            if overlapping:
                warning = "Error: Requested booking is overlapping with following bookings: "
                for booking in overlapping:
                    warning = warning + str(booking)
                raise forms.ValidationError(warning)
