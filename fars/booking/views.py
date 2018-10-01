from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.models import User
from booking.models import Booking, Bookable
from booking.forms import BookingForm
from datetime import datetime, timedelta
import dateutil.parser
from django.utils.translation import gettext as _

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

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
        return redirect('{}?next={}'.format(reverse('login'), request.path_info))
    context = {
        'bookable': bookable_obj,
        'user': request.user
    }
    return render(request, 'month.html', context)


def bookings_day(request, bookable, year, month, day):
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    if not bookable_obj.public and not request.user.is_authenticated:
        return redirect('{}?next={}'.format(reverse('login'), request.path_info))
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
        booking.start = dateutil.parser.parse(request.GET['st']) if 'st' in request.GET else datetime.now()
        booking.end = dateutil.parser.parse(request.GET['et']) if 'et' in request.GET else start + timedelta(hours=1)
        booking.bookable = bookable_obj
        booking.user = request.user
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
    groupname = "{}_admin".format(booking.bookable.id_str)
    groupmembers = User.objects.filter(groups__name=groupname)

    if request.user.is_superuser or request.user in groupmembers:
        # Admin may unbook anything
        pass
    elif booking.end < now:
        unbookable = False
        warning = _("Bookings in the past may not be unbooked")
    # TODO: is this the proper way to check if users are the same?''
    elif request.user.username != booking.user.username:
        unbookable = False
        warning = _("Only the user that made the booking may unbook it")

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
