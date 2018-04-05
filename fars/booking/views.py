from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse, Http404
from booking.models import Booking, Bookable
from booking.forms import BookingForm
from datetime import datetime, timedelta


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
    booking = Booking()
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    context = {'url': request.path}
    if request.method == 'GET':
        start = datetime.strptime(request.GET['t'], '%Y-%m-%dT%H:%M:%S') \
            if 't' in request.GET else datetime.now()
        booking.bookable = bookable_obj
        booking.start = start
        booking.end = start + timedelta(hours=1)
        form = BookingForm(instance=booking)
        status = 200
    elif request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return HttpResponse()
        else:
            status = 400
    else:
        raise Http404
    context['form'] = form
    return render(request, 'book.html', context=context, status=status)


def unbook(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.delete()
        return HttpResponse()
    context = {'url': request.path}
    return render(request, 'unbook.html', context)
