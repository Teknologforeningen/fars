from django.test import TestCase
from booking.models import *
# Create your tests here.
class BookableTestCase(TestCase):
    def setUp(self):
        Bookable.objects.create(id_str="bookable1", name="Bookable1", description="A bookable")

    def test_string_representation(self):
        """Testing that string representation works correctly"""
        bookable = Bookable.objects.get(id_str="bookable1")
        self.assertEqual(str(bookable), "Bookable1")
