from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('<slug:bookable>', views.bookings_month, name="month"),
    path('<slug:bookable>/<int:year>-<int:month>-<int:day>', views.bookings_day, name="day"),
    path('book/<slug:bookable>', views.book, name="book"),
    path('unbook/<int:booking_id>', views.unbook, name="unbook"),
]
