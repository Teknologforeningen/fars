from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib.auth.models import User
from booking.models import Booking, Bookable
from booking.forms import BookingForm, RepeatingBookingForm, CustomLoginForm
from datetime import datetime, timedelta
import dateutil.parser
from django.utils.translation import gettext as _
from django.db import transaction
from django.forms import ValidationError
from django.views import View
import pytz
from fars.settings import TIME_ZONE
from django.contrib.auth import authenticate

class HomeView(View):

    template = 'base.html'

    def get(self, request):
        bookables = Bookable.objects.all()
        context = {
            'bookables': bookables,
            'user': request.user,
        }
        return render(request, self.template, context)


class ProfileView(View):

    template = 'profile.html'

    def get(self, request):
        all_bookings_by_user = Booking.objects.filter(user=request.user)
        context = {}
        stats = {}
        context['statistics'] = stats

        starts = [x.start for x in all_bookings_by_user]
        ends = [x.end for x in all_bookings_by_user]
        timebooked = timedelta(
            seconds=sum([(y-x).total_seconds() for x, y in zip(starts, ends)])
        )
        stats[_('Total time booked')] = timebooked

        future_bookings = all_bookings_by_user.filter(start__gt=datetime.now())
        ongoing_bookings = all_bookings_by_user.filter(start__lt=datetime.now(), end__gt=datetime.now())
        context['future_bookings'] = future_bookings
        context['ongoing_bookings'] = ongoing_bookings
        return render(request, self.template, context)


class MonthView(View):

    template = 'month.html'

    def get(self, request, bookable):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)
        if not bookable_obj.public and not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path_info))
        context = {
            'bookable': bookable_obj,
            'user': request.user
        }
        return render(request, self.template, context)


class DayView(View):

    template = 'day.html'

    def get(self, request, bookable, year, month, day):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)
        if not bookable_obj.public and not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path_info))
        context = {
            'date': "{y}-{m:02d}-{d:02d}".format(y=year, m=month, d=day),
            'bookable': bookable_obj,
            'user': request.user
        }
        return render(request, self.template, context)


class BookView(View):

    template = 'book.html'
    context = {}

    def dispatch(self, request, bookable):
        if not request.user.is_authenticated:
            return render(request, 'modals/forbidden.html', status=403)

        self.context['url'] = request.path
        self.context['bookable'] = get_object_or_404(Bookable, id_str=bookable)
        self.context['user'] = request.user

        return super().dispatch(request, bookable)


    def get(self, request, bookable):
        booking = Booking()
        booking.start = dateutil.parser.parse(request.GET['st']) if 'st' in request.GET else datetime.now()
        booking.end = dateutil.parser.parse(request.GET['et']) if 'et' in request.GET else booking.start + timedelta(hours=1)
        booking.bookable = self.context['bookable']
        booking.user = request.user
        self.context['form'] = BookingForm(instance=booking)

        if _is_admin(request.user, self.context['bookable']):
            self.context['repeatform'] = RepeatingBookingForm()

        return render(request, self.template, context=self.context)


    def post(self, request, bookable):
        form = BookingForm(request.POST, instance=Booking())
        if form.is_valid():
            if request.POST.get('repeat') and _is_admin(request.user, self.context['bookable']):
                repeatdata = {
                    'frequency': request.POST.get('frequency'),
                    'repeat_until': request.POST.get('repeat_until')
                }
                repeat_form = RepeatingBookingForm(repeatdata)
                if repeat_form.is_valid():
                    # Creates repeating bookings as specified, adding all created bookings to group
                    skipped_bookings = repeat_form.save_repeating_booking_group(form.instance)
                    return JsonResponse({'skipped_bookings': skipped_bookings})
                else:
                    status = 400
            else:
                form.save()
                return HttpResponse()
        else:
            status = 400
        self.context['form'] = form
        return render(request, self.template, context=self.context, status=status)


class BookingView(View):

    template = 'booking.html'
    context = {}


    def dispatch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)
        is_unbookable, warning = self._is_unbookable(request.user, booking)

        self.context['url']        = request.path
        self.context['user']       = request.user
        self.context['booking']    = booking
        self.context['unbookable'] = is_unbookable
        self.context['warning']    = warning

        return super().dispatch(request, booking_id)


    # A POST request to a booking is for unbooking.
    # A DELETE request would make more sense, but we use POST for the repeat parameter
    def post(self, request, booking_id):
        booking = self.context['booking']
        is_admin = _is_admin(request.user, booking.bookable)
        if _is_admin or self.context['unbookable']:
            now = datetime.now(booking.start.tzinfo)
            if is_admin and booking.repeatgroup and int(request.POST.get('repeat')) >= 1:
                # Removal of a repeating booking. There are 3 different levels of removal
                # of a repeating booking:
                # 0 : Delete only this booking
                # 1 : Delete this booking and bookings after this one
                # 2 : Delete all bookings from this series of booking (past and future)
                removal_level = int(request.POST.get('repeat'))
                if removal_level == 1:
                    booking.repeatgroup.delete_from_date_forward(booking.start)
                elif removal_level == 2:
                    booking.repeatgroup.delete()

            elif booking.start < now and booking.end > now:
                # Booking is ongoing, end it now
                booking.end = now
                booking.save()
            else:
                booking.delete()
            return HttpResponse()

        return render(request, self.template, self.context)


    def get(self, request, booking_id):
        return render(request, self.template, self.context)


    def _is_unbookable(self, user, booking):
        if booking.end < datetime.now(booking.start.tzinfo):
            return False, _("Bookings in the past may not be unbooked")
        if _is_admin(user, booking.bookable):
            return True, ''
        if user != booking.user:
            return False, _("Only the user that made the booking may unbook it")
        return True, ''


class TabletView(View):
    template = 'tablet.html'
    context = {}

    def dispatch(self, request, bookable):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)
        if not bookable_obj.public and not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path_info))
        self.context['bookable'] = bookable_obj
        self.context['errors'] = 0
        return super().dispatch(request, bookable)

    def get(self, request, bookable):
        now = pytz.timezone(TIME_ZONE).localize(datetime.now())
        booking = Booking()
        booking.bookable = self.context['bookable']
        self.context['bookform'] = BookingForm(instance=booking)
        return render(request, self.template, context=self.context)


    def post(self, request, bookable):
        username = request.POST.get('username')
        pw = request.POST.get('password')
        user = authenticate(username=username, password=pw)
        postdata = request.POST.copy()
        try:
            postdata['user'] = user.id
        except AttributeError:
            postdata['user'] = -1
            self.context['errors'] = 1
            self.context['credential_error'] = 1
        form = BookingForm(postdata, instance=Booking())
        if form.is_valid():
            form.save()
            return redirect('tablet', bookable=bookable)
        else:
            self.context['errors'] = 1
            status = 400

        self.context['bookform'] = form
        return render(request, self.template, context=self.context, status=status)


# Returns whether user is admin for given bookable
def _is_admin(user, bookable):
    return user.is_superuser or user.groups.filter(name=bookable.admin_group_name).exists()
