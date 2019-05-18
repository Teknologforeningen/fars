from rest_framework import viewsets, generics
from rest_framework.views import APIView
from django_filters import rest_framework as filters
from django.shortcuts import render, get_object_or_404
from datetime import datetime, timedelta
from booking.models import *
from api.serializers import *
from api.renderers import *


class BookingFilter(filters.FilterSet):
    bookable = filters.CharFilter(field_name='bookable__id_str')
    before = filters.IsoDateTimeFilter(field_name='start', lookup_expr='lte')
    after = filters.IsoDateTimeFilter(field_name='end', lookup_expr='gte')

    class Meta:
        model = Booking
        fields = ['bookable', 'before', 'after']


class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter


# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter
    renderer_classes = (GeneriKeyBookingRenderer, )



