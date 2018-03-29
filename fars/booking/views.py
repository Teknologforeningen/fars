from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from booking.models import Booking, Bookable
from booking.forms import BookingForm


def home(request):
    bookables = Bookable.objects.all()
    context = {'bookables': bookables}
    return render(request, 'base.html', context)


def bookings_month(request, bookable):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    context = {'bookable': bookable_obj}
    return render(request, 'month.html', context)


def bookings_day(request, bookable, year, month, day):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    context = {
        'date': "{y}-{m:02d}-{d:02d}".format(y=year, m=month, d=day),
        'bookable': bookable_obj,
    }
    return render(request, 'day.html', context)


def book(request, bookable):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    form = BookingForm()
    context = {
        'time': request.GET['t'],
        'bookable': bookable_obj,
        'form': form,
    }
    return render(request, 'book.html', context)
