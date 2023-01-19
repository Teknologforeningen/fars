from rest_framework import serializers
from booking.models import *
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('name', )

class BookableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookable
        fields = ('id', 'id_str', 'name', 'description', 'forward_limit_days', 'length_limit_hours')

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    booking_group = GroupSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = '__all__'

class NoMetaBookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    booking_group = GroupSerializer(read_only=True)
    class Meta:
        model = Booking
        exclude = ('metadata', )

class TimeslotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeslot
        fields = ('bookable', 'start_time', 'start_weekday', 'end_time', 'end_weekday', )
