from rest_framework import viewsets, generics, pagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q
from booking.models import *
from api.serializers import *
from api.renderers import *
import datetime


class BookingFilter(filters.FilterSet):
    # Custom filter fields
    before = filters.IsoDateTimeFilter(field_name='start', lookup_expr='lte')
    after = filters.IsoDateTimeFilter(field_name='end', lookup_expr='gte')
    # Fields where the defualt filter type is overridden
    bookable = filters.CharFilter(field_name='bookable__id_str')
    username = filters.CharFilter(field_name='user__username')
    booking_group = filters.CharFilter(field_name='booking_group')

    class Meta:
        model = Booking
        fields = ['bookable', 'before', 'after', 'username', 'booking_group']

class BookingsPagination(pagination.LimitOffsetPagination):
    default_limit = 100
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 5000

class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = NoMetaBookingSerializer # Exclude metadata to hide doorcode in this API
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = BookingFilter
    search_fields = ['comment', 'start', 'end', 'user__username', 'user__first_name', 'user__last_name', 'booking_group__name']
    ordering_fields = ['start', 'end', 'id']
    ordering = ['start', 'end']
    pagination_class = BookingsPagination

    def get_queryset(self):
        queryset = Booking.objects.all()
        user = self.request.user

        # Show all bookings to staff
        if user.is_staff:
            return queryset

        # Only show public bookables if not logged in
        if not user.is_authenticated:
            return queryset.filter(bookable__public=True)

        # For authenticated users, show bookings on unhidden bookables and on those bookables that the user can make bookings on (part of restriction or admin group)
        return queryset.filter(
            Q(bookable__hidden=False) |
            Q(bookable__booking_restriction_groups__isnull=True) |
            Q(bookable__booking_restriction_groups__in=user.groups.all()) |
            Q(bookable__admin_groups__in=user.groups.all())
        )

class BookablesList(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = BookableSerializer

    def get_queryset(self):
        queryset = Bookable.objects.all()
        user = self.request.user

        # Show all bookables to staff
        if user.is_staff:
            return queryset

        # Only show public bookables if not logged in
        if not user.is_authenticated:
            return queryset.filter(public=True)

        # For authenticated users, show unhidden bookables and those that the user can make bookings on (part of restriction or admin group)
        return queryset.filter(
            Q(hidden=False) |
            Q(booking_restriction_groups__isnull=True) |
            Q(booking_restriction_groups__in=user.groups.all()) |
            Q(admin_groups__in=user.groups.all())
        )

# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.filter(end__gt=datetime.datetime.now())
    serializer_class = BookingSerializer
    filter_class = BookingFilter
    renderer_classes = (GeneriKeyBookingRenderer, )

class TimeslotFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')

    class Meta:
        model = Timeslot
        fields = ['bookable']

class TimeslotsList(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = TimeslotSerializer
    filter_class = TimeslotFilter

    def get_queryset(self):
        queryset = Timeslot.objects.all()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(bookable__public=True)
        
        return queryset
