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

class BookingSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    booking_group = GroupSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = '__all__'
