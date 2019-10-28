from django.test import TestCase, Client
from booking.models import Bookable
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
