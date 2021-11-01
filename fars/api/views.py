from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
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


class BookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.all()
    serializer_class = NoMetaBookingSerializer # Exclude metadata to hide doorcode in this API
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter

    def filter_on_bookable(self, bookings, request):
        bookable = request.query_params.get('bookable')
        if bookable:
            return bookings.filter(bookable__id_str=bookable), True
        return bookings, False

    def serialize_one(self, booking):
        # If the booking is None, the serializer will create a null object, which we don't want
        return Response(self.get_serializer_class()(booking).data if booking else None)

    def serialize_many(self, bookings):
        # If the booking is None, the serializer will create a null object, which we don't want
        return Response(self.get_serializer_class()(bookings, many=True).data)

    def filter_on_bookable_and_serialize_many(self, bookings, request):
        bookings, _ = self.filter_on_bookable(bookings, request)
        return self.serialize_many(bookings)

    @action(methods=['get'], detail=False)
    def future(self, request):
        bookings = self.get_queryset().filter(start__gte=datetime.datetime.now())
        return self.filter_on_bookable_and_serialize_many(bookings, request)

    @action(methods=['get'], detail=False)
    def past(self, request):
        bookings = self.get_queryset().filter(end__lte=datetime.datetime.now())
        return self.filter_on_bookable_and_serialize_many(bookings, request)

    @action(methods=['get'], detail=False)
    def next(self, request):
        bookings = self.get_queryset().filter(start__gte=datetime.datetime.now())
        bookings, _ = self.filter_on_bookable(bookings, request)

        # Find the next booking
        b = bookings.order_by('start').first()

        return self.serialize_one(b)

    @action(methods=['get'], detail=False)
    def previous(self, request):
        bookings = self.get_queryset().filter(end__lte=datetime.datetime.now())
        bookings, _ = self.filter_on_bookable(bookings, request)

        # Find the next booking
        b = bookings.order_by('end').last()

        return self.serialize_one(b)

    @action(methods=['get'], detail=False)
    def now(self, request):
        t = datetime.datetime.now()
        bookings = self.get_queryset().filter(start__lte=t, end__gte=t)
        bookings, filtered = self.filter_on_bookable(bookings, request)

        # Filtering on bookable should result in a maximum of one booking
        if filtered:
            return self.serialize_one(bookings.first())

        return self.serialize_many(bookings)

# This class provides the view used by GeneriKey to get the list of bookings they need
class GeneriKeyBookingsList(viewsets.ViewSetMixin, generics.ListAPIView):
    queryset = Booking.objects.filter(end__gt=datetime.datetime.now())
    serializer_class = BookingSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = BookingFilter
    renderer_classes = (GeneriKeyBookingRenderer, )
