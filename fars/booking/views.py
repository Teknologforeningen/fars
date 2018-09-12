from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, Http404
from booking.models import Booking, Bookable
from booking.forms import BookingForm
from datetime import datetime, timedelta


def home(request):
    bookables = Bookable.objects.all()
    context = {
        'bookables': bookables,
        'user': request.user,
    }
    return render(request, 'base.html', context)


def bookings_month(request, bookable):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    if not bookable_obj.public and not request.user.is_authenticated:
        return render(request, 'modals/forbidden.html')
    else:
        context = {
            'bookable': bookable_obj,
            'user': request.user
        }
        return render(request, 'month.html', context)


def bookings_day(request, bookable, year, month, day):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    if not bookable_obj.public and not request.user.is_authenticated:
        return render(request, 'modals/forbidden.html')
    else:
        context = {
            'date': "{y}-{m:02d}-{d:02d}".format(y=year, m=month, d=day),
            'bookable': bookable_obj,
            'user': request.user
        }
        return render(request, 'day.html', context)


def book(request, bookable):
    if not request.user.is_authenticated:
        return render(request, 'modals/forbidden.html')
    booking = Booking()
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    context = {
        'url': request.path,
        'bookable': bookable_obj,
        'user': request.user,
    }

    if request.method == 'GET':
        start = datetime.strptime(request.GET['t'], '%Y-%m-%dT%H:%M:%S') \
            if 't' in request.GET else datetime.now()
        booking.bookable = bookable_obj
        booking.user = request.user
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
    # Check if unbooking is allowed
    now = datetime.now(booking.start.tzinfo) # TODO: Do we want to deal with timezones? should we use UTC?
    unbookable = True
    warning = None
    if request.user.is_staff:
        # Admin may unbook anything
        pass
    elif booking.end < now:
        unbookable = False
        warning = "Bookings in the past may not be unbooked"
    # TODO: is this the proper way to check if users are the same?''
    elif request.user.username != booking.user.username:
        unbookable = False
        warning = "Only the user that made the booking may unbook it"

    if request.method == 'POST' and unbookable:
        if booking.start < now and booking.end > now:
            # Booking is ongoing, end it now
            booking.end = now
            booking.save()
        else:
            booking.delete()
        return HttpResponse()

    context = {
        'url': request.path,
        'booking': booking,
        'user': request.user,
        'unbookable': unbookable,
        'warning': warning,
    }
    return render(request, 'unbook.html', context)
