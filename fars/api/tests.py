from django.contrib.auth.models import User, Group
from booking.models import Bookable, Booking
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone, translation

def plus_one_day(d):
    return d.replace(day=d.day + 1)

t1 = plus_one_day(timezone.now())
t2 = plus_one_day(t1)

# Bookings per bookable
N = 4

class BaseAPITest(APITestCase):
    def setUp(self):
        translation.activate('en')

        # Create two users
        self.user1 = User.objects.create_user(username='svakar', password='teknolog')
        self.user2 = User.objects.create_user(username='svatta', password='teknolog')
        self.admin = User.objects.create_user(username='admin', password='teknolog')
        self.superuser = User.objects.create_superuser(username='superuser', password='teknolog')

        # Create a group used for restricting booking access to
        self.restriction_group = Group.objects.create(name='group')
        self.restriction_group.user_set.add(self.user2)

        # Create a group used for admin access
        self.admin_group = Group.objects.create(name='admin')
        self.admin_group.user_set.add(self.admin)

        # Public bookable
        Bookable.objects.create(public=True, hidden=False, id_str='public')

        # Restricted public bookable
        Bookable.objects.create(public=True, hidden=False, id_str='publicrestricted').booking_restriction_groups.set([self.restriction_group])

        # Normal bookable
        Bookable.objects.create(public=False, hidden=False, id_str='normal')

        # Restricted normal bookable
        Bookable.objects.create(public=False, hidden=False, id_str='normalrestricted').booking_restriction_groups.set([self.restriction_group])

        # Hidden bookable
        Bookable.objects.create(public=False, hidden=True, id_str='hidden')

        # Restricted hidden bookable
        Bookable.objects.create(public=False, hidden=True, id_str='hiddenrestricted').booking_restriction_groups.set([self.restriction_group])

        for bookable in Bookable.objects.all():
            # Add admin group to all bookables
            bookable.admin_groups.set([self.admin_group])
            # Create one booking per user per bookable
            Booking.objects.create(bookable=bookable, user=self.user1, start=t1, end=t2)
            Booking.objects.create(bookable=bookable, user=self.user2, start=t1, end=t2, booking_group=self.restriction_group)
            Booking.objects.create(bookable=bookable, user=self.admin, start=t1, end=t2)
            Booking.objects.create(bookable=bookable, user=self.superuser, start=t1, end=t2)

    def login_user(self):
        self.client.login(username='svakar', password='teknolog')

    def login_user_part_of_restriction_group(self):
        self.client.login(username='svatta', password='teknolog')

    def login_user_part_of_admin_group(self):
        self.client.login(username='admin', password='teknolog')

    def login_superuser(self):
        self.client.login(username='superuser', password='teknolog')


class BookablesAPITest(BaseAPITest):
    def get_bookables(self):
        response = self.client.get('/api/bookables')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()

    def test_for_anonymous_users(self):
        # Should see the two public bookables
        self.assertEqual(2, len(self.get_bookables()))

    def test_for_user(self):
        self.login_user()
        # Should see all bookables except the restricted hidden one
        self.assertEqual(5, len(self.get_bookables()))

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        # Should see all bookables
        self.assertEqual(6, len(self.get_bookables()))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        # Should see all bookables
        self.assertEqual(6, len(self.get_bookables()))

    def test_for_superuser(self):
        self.login_superuser()
        # Should see all bookables
        self.assertEqual(6, len(self.get_bookables()))


class BookingsAPITest(BaseAPITest):
    def get_bookings(self, bookable=None):
        url = '/api/bookings'
        if bookable:
            url += f'?bookable={bookable.id_str}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.json()['results']

    def test_for_anonymous_users(self):
        # Should see bookings on the two public bookables
        self.assertEqual(2*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(N if bookable.public else 0, len(self.get_bookings(bookable)))

    def test_for_user(self):
        self.login_user()
        # Should see bookings on all bookables except the restricted hidden one
        self.assertEqual(5*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(0 if bookable.hidden and bookable.booking_restriction_groups.count() else N, len(self.get_bookings(bookable)))

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        # Should see all bookings
        self.assertEqual(6*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(N, len(self.get_bookings(bookable)))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        # Should see all bookings
        self.assertEqual(6*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(N, len(self.get_bookings(bookable)))

    def test_for_superuser(self):
        self.login_superuser()
        # Should see all bookings
        self.assertEqual(6*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(N, len(self.get_bookings(bookable)))

    def test_pagination(self):
        self.login_superuser()
        response = self.client.get('/api/bookings?limit=1')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json = response.json()
        self.assertEqual(6*N, json['count'])
        self.assertEqual(1, len(json['results']))
        self.assertEqual(None, json['previous'])

class GenerikeyAPITest(BaseAPITest):
    def get_bookings(self, bookable=None):
        url = '/api/gkey'
        if bookable:
            url += f'?bookable={bookable.id_str}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.content.decode("utf-8").split()

    def test_for_anonymous_users(self):
        # Should see bookings on the two public bookables
        self.assertEqual(6*N, len(self.get_bookings()))
        for bookable in Bookable.objects.all():
            self.assertEqual(N, len(self.get_bookings(bookable)))

    def test_booking_format(self):
        username, group, start, end, special, code = self.get_bookings()[0].split(':')
        self.assertEqual("svakar", username)
        self.assertEqual("0", group)
        int(start)
        int(end)
        self.assertEqual("0", special)
        self.assertEqual("0", code)

    def test_booking_format_booking_group(self):
        username, group, start, end, special, code = self.get_bookings()[1].split(':')
        self.assertEqual("svatta", username)
        self.assertEqual("group", group)
        int(start)
        int(end)
        self.assertEqual("0", special)
        self.assertEqual("0", code)
