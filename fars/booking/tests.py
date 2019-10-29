from django.test import TestCase, Client
from booking.models import Bookable, Booking
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# Create your tests here.
class BookTestCase(TestCase):
    def setUp(self):
        Bookable.objects.create(
            id_str = "b",
            name = "B",
            description = "A bookable"
        )

        User = get_user_model()
        User.objects.create_user(
            username = "u",
            password = "pw"
        )


    def test_user_can_book(self):
        """A valid user can book a bookable"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }

        c.login(username='u', password='pw')
        response = c.post('/booking/book/b', postdata)

        self.assertEqual(response.status_code, 201)


    def test_cant_book_unauthorized(self):
        """If not logged in, bookable cant be booked"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }
        response = c.post('/booking/book/b', postdata)
        self.assertEqual(response.status_code, 403)


    def test_cant_book_in_the_past(self):
        """Making a booking in the past shouldn't work"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }

        c.login(username='u', password='pw')
        response = c.post('/booking/book/b', postdata)
        self.assertEqual(response.status_code, 403)


    def test_cant_book_too_far_in_future(self):
        """Making a booking too far in the future shouldn't be allowed"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': (now + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now + timedelta(days=365, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }

        c.login(username='u', password='pw')
        response = c.post('/booking/book/b', postdata)
        self.assertEqual(response.status_code, 403)


    def test_cant_book_too_long(self):
        """You cant make a too long booking"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }

        c.login(username='u', password='pw')
        response = c.post('/booking/book/b', postdata)

        self.assertEqual(response.status_code, 403)


    def test_booking_from_past_to_future(self):
        """When booking from the past to the future, the booking should have starttime now and retain its endtime"""
        c = Client()
        now = datetime.now()
        postdata = {
            'before': (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'after': (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            'bookable': 'b'
        }

        c.login(username='u', password='pw')
        response = c.post('/booking/book/b', postdata)
        self.assertEqual(response.status_code, 201)

        bookable = Bookable.objects.get(id_str="b")
        b = Booking.objects.get(bookable=bookable)
        self.assertEqual(b.start, now)
        self.assertEqual(b.end, now + timedelta(hours=1))
