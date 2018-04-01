from rest_framework import viewsets, generics
from django_filters import rest_framework as filters
from booking.models import *
from api.serializers import *


class BookingFilter(filters.FilterSet):
    bookable = filters.CharFilter(name='bookable__id_str')
    before = filters.IsoDateTimeFilter(name='start', lookup_expr='lte')
    after = filters.IsoDateTimeFilter(name='end', lookup_expr='gte')

    class Meta:
        model = Booking
        fields = ['bookable', 'before', 'after']


class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter