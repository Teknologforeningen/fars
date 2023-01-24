from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import HttpResponse, JsonResponse
from booking.models import Booking, Bookable
from booking.forms import RepeatingBookingForm
from booking.metadata_forms import get_form_class
from django.utils.translation import gettext as _
from django.db import transaction
from django.views import View
from datetime import datetime, timedelta
import time, json, dateutil.parser
from django.utils import timezone

class HomeView(View):

    template = 'base.html'

    def get(self, request):
        bookables = Bookable.objects.filter(hidden=False)
        context = {
            'bookables': bookables,
            'user': request.user,
        }
        return render(request, self.template, context)


class ProfileView(View):
    template = 'profile.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path_info))

        all_bookings_by_user = Booking.objects.filter(user=request.user)
        context = {}
        stats = {}
        context['statistics'] = stats

        stats[_('Bookings')] = all_bookings_by_user.count()
        stats[_('Bookables used')] = f'{all_bookings_by_user.values("bookable").distinct().count()}/{Bookable.objects.count()}'

        starts = [x.start for x in all_bookings_by_user]
        ends = [x.end for x in all_bookings_by_user]
        timebooked = timedelta(
            seconds=sum([(y-x).total_seconds() for x, y in zip(starts, ends)])
        )
        timebooked_hours, reminder = divmod(timebooked.seconds, 3600)
        stats[_('Total time booked')] = _('{hours} hours {minutes} minutes').format(hours=timebooked_hours + 24*timebooked.days, minutes=int(reminder/60))

        future_bookings = all_bookings_by_user.filter(start__gt=timezone.now())
        ongoing_bookings = all_bookings_by_user.filter(start__lt=timezone.now(), end__gt=timezone.now())
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
            'date': timezone.make_aware(datetime(year, month, day, 0, 0, 0, 0)).isoformat(),
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
        booking.start = dateutil.parser.parse(request.GET['st']) if 'st' in request.GET else timezone.now()
        # Remove the seconds and microseconds if they are present
        booking.start = booking.start.replace(second=0, microsecond=0)
        booking.end = dateutil.parser.parse(request.GET['et']) if 'et' in request.GET else booking.start + timedelta(hours=1)
        booking.bookable = self.context['bookable']

        booking.user = request.user
        form = get_form_class(booking.bookable.metadata_form)(instance=booking)
        self.context['form'] = form

        if _is_admin(request.user, booking.bookable):
            self.context['repeatform'] = RepeatingBookingForm()

        return render(request, self.template, context=self.context)


    def post(self, request, bookable):
        booking = Booking()
        booking.user = self.context['user']
        booking.bookable = self.context['bookable']
        form = get_form_class(booking.bookable.metadata_form)(request.POST, instance=booking)
        self.context['form'] = form

        if not form.is_valid():
            return render(request, self.template, context=self.context, status=400)

        booking = form.instance
        booking.metadata = json.dumps(form.get_cleaned_metadata())

        # Add the emails from the form to the Booking instance so that the pre_save signal can get them
        booking.emails = form.get_cleaned_emails()

        # Handle recurring events
        if request.POST.get('repeat') and _is_admin(request.user, booking.bookable):
            repeatdata = {
                'frequency': request.POST.get('frequency'),
                'repeat_until': request.POST.get('repeat_until')
            }

            # Add recurrance data to model instance so that is can be used when creating Google Calendar events
            booking.recurrence = repeatdata

            repeat_form = RepeatingBookingForm(repeatdata)
            if not repeat_form.is_valid():
                return render(request, self.template, context=self.context, status=400)

            # Creates repeating bookings as specified, adding all created bookings to group
            # No need to save this form on its own
            skipped_bookings = repeat_form.save_repeating_booking_group(booking)
            # XXX: Button says "Boka" (probably "Submit" in English), which is wrong
            return JsonResponse({'skipped_bookings': skipped_bookings})

        form.save()
        booking.bookable.notify_external_services()

        return HttpResponse()


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


    def delete(self, request, booking_id):
        booking = self.context['booking']
        is_admin = _is_admin(request.user, booking.bookable)
        if is_admin or self.context['unbookable']:
            now = timezone.now()
            removal_level = int(request.GET.get('repeat') or 0)
            if is_admin and booking.repeatgroup and removal_level >= 1:
                # Removal of a repeating booking. There are 3 different levels of removal
                # of a repeating booking:
                # 0 : Delete only this booking
                # 1 : Delete this booking and bookings after this one
                # 2 : Delete all bookings from this series of booking (past and future)
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
            self.context['booking'].bookable.notify_external_services()
            return HttpResponse()

        return render(request, self.template, self.context)


    def get(self, request, booking_id):
        booking = self.context['booking']
        user = self.context['user']
        gcal = booking.bookable.gcal

        if not gcal or not _is_creator(user, booking):
            return render(request, self.template, self.context)

        self.context['gevent_show_row'] = True

        # 0 = Booking has no event
        # 1 = Event status unknown, need to fetch to find out
        # 2 = Event exists
        # 3 = Event is cancelled
        # 4 = Event not found (removed or other error)
        self.context['gevent_status'] = 1 if booking.google_calendar_event_id else 0
        self.context['gevent_link'] = None

        fetch_event = request.GET.get('gevent_fetch') != None
        if fetch_event:
            event = gcal.try_get_event(booking)
            if not event:
                # Could also choose to remove the event id from the Booking instance here
                # But failing to fetch the event does not necessarily mean that the event does not exits...
                self.context['gevent_status'] = 4
            elif event['status'] == 'cancelled':
                #...and cancelled/deleted events can still be restored for 30 days
                self.context['gevent_status'] = 3
            else:
                self.context['gevent_status'] = 2
                self.context['gevent_link'] = event['htmlLink']

        return render(request, self.template, self.context)


    def _is_unbookable(self, user, booking):
        if booking.end < timezone.now():
            return False, _('Bookings in the past may not be unbooked')
        if _is_admin(user, booking.bookable):
            return True, ''
        if user != booking.user and booking.booking_group not in user.groups.all():
            return False, _('Only the user or group that made the booking may unbook it')
        return True, ''

# Returns whether user is admin for given bookable
def _is_admin(user, bookable):
    return user.is_superuser or user.groups.filter(id__in=bookable.admin_groups.all()).exists()

# Returns whether a user is the creator of a booking
def _is_creator(user, booking):
    return user.is_superuser or booking.user.id == user.id
