from django.urls import path
from . import views

urlpatterns = [
   path('<slug:bookable>', views.TabletView.as_view(), name='tablet'),
]
