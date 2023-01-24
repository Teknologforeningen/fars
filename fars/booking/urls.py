from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('profile', views.ProfileView.as_view(), name='profile'),
    path('<slug:bookable>', views.MonthView.as_view(), name='month'),
    path('<slug:bookable>/<int:year>-<int:month>-<int:day>', views.DayView.as_view(), name='day'),
    path('book/<slug:bookable>', views.BookView.as_view(), name='book'),
    path('booking/<int:booking_id>', views.BookingView.as_view(), name='booking'),
]
