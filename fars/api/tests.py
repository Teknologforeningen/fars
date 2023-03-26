from django.contrib.auth.models import User, Group
from booking.models import Bookable, Booking
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.utils import timezone
import json


class BookingApiTest(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='svakar', password='teknolog')
        self.user2 = User.objects.create_user(username='another', password='user')
        self.group1 = Group.objects.create(name='group1')
        self.group2 = Group.objects.create(name='group2')

        self.bookable_public = Bookable.objects.create(id_str='room1', name='My room', public=True)
        self.bookable_private = Bookable.objects.create(id_str='room2', name='My second room', public=False)
        self.bookable_hidden = Bookable.objects.create(id_str='room3', name='My third room', public=False, hidden=True)

        self.bookable_hidden.admin_groups.add(self.group1)
        self.user1.groups.add(self.group1)
        self.user1.groups.add(self.group2)

        d = timezone.now()
        for _ in range(5):
            Booking.objects.create(bookable=self.bookable_public, user=self.user1, start=d, end=d)
            Booking.objects.create(bookable=self.bookable_private, user=self.user1, start=d, end=d)
            Booking.objects.create(bookable=self.bookable_hidden, user=self.user1, start=d, end=d)


    # BOOKABLES

    def test_bookables_list_show_only_public_if_not_logged_in(self):
        response = self.client.get('/api/bookables')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(1, len(content))

    def test_bookables_list_show_unhidden_if_logged_in(self):
        User.objects.create_user(username='new', password='user')
        self.client.login(username='new', password='user')

        response = self.client.get('/api/bookables')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(len(content), 2)

    def test_bookables_list_show_hidden_to_admin(self):
        self.client.login(username='svakar', password='teknolog')
        response = self.client.get('/api/bookables')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(len(content), 3)


    # BOOKINGS

    def test_bookings_list_show_only_public_if_not_logged_in(self):
        response = self.client.get('/api/bookings')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(len(content), 5)

    def test_bookings_list_show_unhidden_if_logged_in(self):
        User.objects.create_user(username='new', password='user')
        self.client.login(username='new', password='user')

        response = self.client.get('/api/bookings')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(len(content), 10)

    def test_bookings_list_show_hidden_to_admin(self):
        self.client.login(username='svakar', password='teknolog')
        response = self.client.get('/api/bookings')
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        content = json.loads(response.content)
        self.assertEqual(len(content), 15)
