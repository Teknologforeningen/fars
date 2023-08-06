from django.utils.translation import gettext as _
from rest_framework import viewsets, generics, pagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from booking.models import *
from api.serializers import *
from api.renderers import *
import datetime


class BookingFilter(filters.FilterSet):
    # Custom filter fields
    before = filters.IsoDateTimeFilter(field_name='start', lookup_expr='lte', label=_('Booking starts before'))
    after = filters.IsoDateTimeFilter(field_name='end', lookup_expr='gte', label=_('Booking ends after'))
    # Fields where the defualt filter type is overridden
    bookable = filters.CharFilter(field_name='bookable__id_str', label=_('Bookable id_str is'))
    username = filters.CharFilter(field_name='user__username', label=_('User username is'))
    booking_group = filters.CharFilter(field_name='booking_group__name', label=_('Booking group name is'))

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
        return Booking.get_readable_bookings_for_user(self.request.user)

class BookablesList(viewsets.ViewSetMixin, generics.ListAPIView):
    serializer_class = BookableSerializer

    def get_queryset(self):
        return Bookable.get_readable_bookables_for_user(self.request.user)

class GenerikeyBookingFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')
    class Meta:
        model = Booking
        fields = ['bookable']

# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.filter(end__gt=datetime.datetime.now())
    serializer_class = BookingSerializer
    filter_class = GenerikeyBookingFilter
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
