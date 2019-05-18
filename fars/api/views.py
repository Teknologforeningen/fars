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
    
    '''
    def get(self, request):
     404 for non-existant bookable
    start = datetime.now()
    end = start + timedelta(days=7)
    bookable_obj = get_object_or_404(Bookable, id_str=bookable)
    bookings = Booking.objects.filter(bookable=bookable_obj, start__lte=end, end__gte=start)

    <CARD>:<COM>:<START>:<END>:<SPECIAL>:<CODE>\n

    <CARD> -> bokarens kortnummer = bill-kontonummer (har du tillgång till
    detta?)
    <COM> -> kommittékod (LDAP-GID) ifall access skall ges till en grupp, i
    annat fall 0; alltid 0 på utrymmen som inte stöder kommittébokning
    <START> -> starttidens UNIX-timestamp (UTC)
    <STOP> -> sluttidens UNIX-timestamp (UTC)
    <SPECIAL> -> en bitfield vars betydelse beror på det bokningsbara
    utrymmet; i böldens fall alltid 0
    <CODE> -> en hash som definierar en kod som kan användas under
    bokningens tid, 0 ifall funktionen inte används, unset ifall ingen kod,
    annars en hex-hash
    '''


