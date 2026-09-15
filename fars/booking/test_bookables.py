from django.test import TestCase
from booking.models import Bookable

class BookableTestCase(TestCase):
    def setUp(self):
      pass

    def test_create_plain_bookable_name(self):
        """Creating a plain bookable should create a simple bookable with default values and no extra features"""
        b = Bookable.objects.create(name="Room A")
        self.assertEqual(b.name, "Room A")
        
    def test_create_plain_bookable_description(self):
        """Creating a plain bookable should create a simple bookable with default values and no extra features"""
        b = Bookable.objects.create(name="Room A", description="A nice room")
        self.assertEqual(b.description, "A nice room")
        
    def test_create_plain_bookable_public(self):
        """Creating a plain bookable should create a simple bookable with default values and no extra features"""
        b = Bookable.objects.create(name="Room A")
        self.assertFalse(b.public)