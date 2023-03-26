from rest_framework import routers
from api.views import *

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'bookings', BookingsList, basename='Booking')
router.register(r'bookables', BookablesList, basename='Bookable')
router.register(r'gkey', GeneriKeyBookingsList)
router.register(r'timeslots', TimeslotsList, basename='Timeslot')

urlpatterns = router.urls