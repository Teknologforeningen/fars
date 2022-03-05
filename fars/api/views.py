from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from booking.models import *
from api.serializers import *
from api.renderers import *
import datetime


class BookingFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')
    before = filters.IsoDateTimeFilter(field_name='start', lookup_expr='lte')
    after = filters.IsoDateTimeFilter(field_name='end', lookup_expr='gte')

    class Meta:
        model = Booking
        fields = ['bookable', 'before', 'after']

class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.all()
    serializer_class = NoMetaBookingSerializer # Exclude metadata to hide doorcode in this API
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter

# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.filter(end__gt=datetime.datetime.now())
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter
    renderer_classes = (GeneriKeyBookingRenderer, )

class TimeslotFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')

    class Meta:
        model = Timeslot
        fields = ['bookable']

class TimeslotsList(viewsets.ViewSetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    # The frontend relies on the sorted order. We sort by end time because a timeslot ending on Monday but starting the previous week should precede a slot starting on Monday.
    queryset = Timeslot.objects.all().order_by('end_weekday', 'end_time');
    serializer_class = TimeslotSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TimeslotFilter