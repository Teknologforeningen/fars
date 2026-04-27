from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import View
from booking.models import Booking, Bookable
from booking.forms import RepeatingBookingForm
from booking.metadata_forms import get_form_class
from booking.gcal import create_gcal_url
import dateutil.parser
import json

def redirect_to_login(request):
    return redirect('{}?next={}'.format(reverse('login'), request.path_info))

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html', {
            'bookables': Bookable.get_readable_bookables_for_user(request.user),
            'user': request.user,
        })


class ProfileView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect_to_login(request)

        all_bookings_by_user = Booking.objects.filter(user=request.user)
        stats = {}

        stats[_('Bookings')] = all_bookings_by_user.count()
        stats[_('Bookables used')] = f'{all_bookings_by_user.values("bookable").distinct().count()}/{Bookable.objects.count()}'

        starts = [x.start for x in all_bookings_by_user]
        ends = [x.end for x in all_bookings_by_user]
        timebooked = timezone.timedelta(
            seconds=sum([(y-x).total_seconds() for x, y in zip(starts, ends)])
        )
        timebooked_hours, reminder = divmod(timebooked.seconds, 3600)
        stats[_('Total time booked')] = _('{hours} hours {minutes} minutes').format(hours=timebooked_hours + 24*timebooked.days, minutes=int(reminder/60))

        now = timezone.now()
        future_bookings = all_bookings_by_user.filter(start__gt=now)
        ongoing_bookings = all_bookings_by_user.filter(start__lt=now, end__gt=now)

        return render(request, 'profile.html', {
            'statistics': stats,
            'future_bookings': future_bookings,
            'ongoing_bookings': ongoing_bookings,
        })


class MonthView(View):
    def get(self, request, bookable):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)

        # Users must have read access to the bookable
        if not bookable_obj.is_readable_for_user(request.user):
            if not request.user.is_authenticated:
                return redirect_to_login(request)
            return HttpResponseForbidden()

        return render(request, 'month.html', {
            'bookable': bookable_obj,
            'user': request.user
        })


class DayView(View):
    def get(self, request, bookable, year, month, day):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)

        # Users must have read access to the bookable
        if not bookable_obj.is_readable_for_user(request.user):
            if not request.user.is_authenticated:
                return redirect_to_login(request)
            return HttpResponseForbidden()

        return render(request, 'day.html', {
            'date': timezone.datetime(year, month, day, 0, 0, 0, 0).isoformat(),
            'bookable': bookable_obj,
            'user': request.user
        })


class BookView(View):
    template = 'book.html'
    context = {}

    def dispatch(self, request, bookable):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)

        if not bookable_obj.is_writable_for_user(request.user):
            return render(request, 'modals/forbidden.html' if request.user.is_authenticated else 'modals/forbidden_login.html', status=403)

        self.context['url'] = request.path
        self.context['bookable'] = bookable_obj
        self.context['user'] = request.user
        self.context['is_admin'] = bookable_obj.is_user_admin(request.user)
        self.context['repeatform'] = None
        self.context['repeatform_show'] = False

        return super().dispatch(request, bookable)

    def get(self, request, _):
        booking = Booking()
        booking.start = dateutil.parser.parse(request.GET['st']) if 'st' in request.GET else timezone.now()
        # Remove the seconds and microseconds if they are present
        booking.start = booking.start.replace(second=0, microsecond=0)
        booking.end = dateutil.parser.parse(request.GET['et']) if 'et' in request.GET else booking.start + timezone.timedelta(hours=1)
        booking.bookable = self.context['bookable']

        booking.user = request.user
        form = get_form_class(booking.bookable.metadata_form)(instance=booking)
        self.context['form'] = form

        # Add form for repeating bookings for admins of the bookable object
        if self.context['is_admin']:
            self.context['repeatform'] = RepeatingBookingForm(booking)

        return render(request, self.template, context=self.context)

    def post(self, request, _):
        booking = Booking()
        booking.user = self.context['user']
        booking.bookable = self.context['bookable']
        form = get_form_class(booking.bookable.metadata_form)(request.POST, instance=booking)
        self.context['form'] = form

        if not form.is_valid():
            return render(request, self.template, context=self.context, status=400)

        booking = form.instance
        booking.metadata = json.dumps(form.get_cleaned_metadata())

        # Allow only bookable admins to create repeating bookings
        if request.POST.get('repeat') and self.context['is_admin']:
            self.context['repeatform_show'] = True
            repeat_form = self.context['repeatform'] = RepeatingBookingForm(booking, request.POST)

            if not repeat_form.is_valid():
                return render(request, self.template, context=self.context, status=400)

            # Creates repeating bookings as specified, adding all created bookings to group
            created, skipped = repeat_form.save_repeating_booking_group(booking)
            return JsonResponse({'created_bookings': created, 'skipped_bookings': skipped})

        else:
            form.save()

        booking.bookable.notify_external_services()

        return HttpResponse()


class BookingView(View):
    template = 'booking.html'
    context = {}

    def dispatch(self, request, booking_id):
        booking = get_object_or_404(Booking, id=booking_id)

        if not booking.bookable.is_readable_for_user(request.user):
            # Non-authenticated users can only look at public bookables, otherwise redirect to login
            return render(request, 'modals/forbidden.html' if request.user.is_authenticated else 'modals/forbidden_login.html', status=403)

        is_unbookable, warning = booking.is_unbookable_by_user(request.user)

        self.context['url']        = request.path
        self.context['user']       = request.user
        self.context['is_owner']   = request.user == booking.user
        self.context['is_admin']   = booking.bookable.is_user_admin(request.user)
        self.context['booking']    = booking
        self.context['unbookable'] = is_unbookable
        self.context['is_ongoing'] = booking.is_ongoing()
        self.context['warning']    = warning
        self.context['gcal']       = create_gcal_url(booking)

        return super().dispatch(request, booking_id)

    def delete(self, request, _):
        if not self.context['unbookable']:
            return render(request, self.template, self.context)

        # There are 3 different levels of removal of a repeating booking:
        #  0 : Delete only this booking
        #  1 : Delete this booking and bookings after this one
        #  2 : Delete all bookings from this series of booking (past and future)
        removal_level = int(request.GET.get('repeat') or 0)
        booking = self.context['booking']

        # Only admins can unbook multiple repeating bookings at once
        if removal_level > 0 and booking.repeatgroup and self.context['is_admin']:
            if removal_level == 1:
                booking.repeatgroup.delete_from_date_forward(booking.start)
            elif removal_level == 2:
                booking.repeatgroup.delete_from_date_forward(timezone.now())
        else:
            booking.unbook()

        booking.bookable.notify_external_services()
        return HttpResponse()

    def get(self, request, _):
        return render(request, self.template, self.context)
