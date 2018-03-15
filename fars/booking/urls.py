from django.urls import path
from . import views

urlpatterns = [
    path('bookings/<int:year>/<int:month>', views.bookings_month, name="bookings_month"),
    path('bookings/<int:year>/<int:month>/<int:day>', views.bookings_day, name="bookings_day"),
    path(r'', views.home, name="home"),
]
