from rest_framework import viewsets, generics, pagination
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from booking.models import *
from api.serializers import *
from api.renderers import *
import datetime


class BookingFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')
    before = filters.IsoDateTimeFilter(field_name='start', lookup_expr='lte')
    after = filters.IsoDateTimeFilter(field_name='end', lookup_expr='gte')
    booking_group = filters.CharFilter(field_name='booking_group')

    class Meta:
        model = Booking
        fields = ['bookable', 'before', 'after', 'booking_group']

class BookingsPagination(pagination.LimitOffsetPagination):
    default_limit = 5000
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 50000

class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.all()
    serializer_class = NoMetaBookingSerializer # Exclude metadata to hide doorcode in this API
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filter_class = BookingFilter
    search_fields = ['comment', 'start', 'end', 'user__username', 'user__first_name', 'user__last_name', 'booking_group__name']
    ordering_fields = ['start', 'end', 'id']
    ordering = ['start', 'end']
    pagination_class = BookingsPagination

    # Override default pagination response
    def get_paginated_response(self, data):
        return Response(data)

# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.filter(end__gt=datetime.datetime.now())
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter
    renderer_classes = (GeneriKeyBookingRenderer, )
