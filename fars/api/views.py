from rest_framework import viewsets, generics
from django_filters import rest_framework as filters
from django.db.models import Q
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

    serializer_class = NoMetaBookingSerializer # Exclude metadata to hide doorcode in this API
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter

    def get_queryset(self):
        queryset = Booking.objects.all()
        user = self.request.user

        # Only show bookings for public bookables if not logged in
        if not user.is_authenticated:
            queryset = queryset.filter(bookable__public=True)
        # Only show bookings on unhidden bookables to superusers and admins of the bookable
        if not user.is_superuser:
            q = Q(bookable__hidden=False)
            for group in user.groups.all():
                q |= Q(bookable__admin_groups__contains=group)
            queryset = queryset.filter(q)

        return queryset

class BookablesList(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = BookableSerializer

    def get_queryset(self):
        queryset = Bookable.objects.all()
        user = self.request.user

        # Only show public bookables if not logged in
        if not user.is_authenticated:
            queryset = queryset.filter(public=True)
        # Only show unhidden bookables to superusers and admins of the bookable
        if not user.is_superuser:
            q = Q(hidden=False)
            for group in user.groups.all():
                q |= Q(admin_groups__contains=group)
            queryset = queryset.filter(q)

        return queryset

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
    serializer_class = TimeslotSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TimeslotFilter

    def get_queryset(self):
        queryset = Timeslot.objects.all()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(bookable__public=True)
        
        return queryset
