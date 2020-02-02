from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class BookingApiTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svakar', password='teknolog')

    def test_bookings_list_requires_authentication(self):
        response = self.client.get('/api/bookings')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.login(username='svakar', password='teknolog')
        response = self.client.get('/api/bookings')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
