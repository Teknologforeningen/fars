from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from booking.models import Booking

def home(request):
   return render(request, 'home.html')


def bookings_month(request, year, month):
    bookings = Booking.objects.filter(date__year=year).filter(date__month=month)
    events = []
    for b in bookings:
        start = "{}T{}".format(b.date, b.timeslot.start)
        end = "{}T{}".format(b.date, b.timeslot.end)
        events.append({'title': b.name, 'start': start, 'end': end})
    return JsonResponse(events, safe=False)


def bookings_day(request, year, month, day):
    bookings = Booking.objects.filter(date__year=year).filter(date__month=month).filter(date__day=day)
    events = []
    for b in bookings:
        start = "{}T{}".format(b.date, b.timeslot.start)
        end = "{}T{}".format(b.date, b.timeslot.end)
        events.append({'title': b.name, 'start': start, 'end': end})
    return JsonResponse(events, safe=False)
