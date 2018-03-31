from rest_framework import viewsets, generics
from django_filters.rest_framework import DjangoFilterBackend
from booking.models import *
from api.serializers import *


class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    filter_backends = (DjangoFilterBackend,)
    # These filter fields allow us to filter by bookable and a date range
    filter_fields = ('bookable__id_str')