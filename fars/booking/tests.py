from api.tests import BaseAPITest
from rest_framework import status
from booking.models import Bookable, Booking

class HomeViewTest(BaseAPITest):
    def get_bookables(self):
        response = self.client.get('/booking/', follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'base.html')
        return response.context['bookables']

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


class ProfileViewTest(BaseAPITest):
    url = '/booking/profile'

    def go_to_profile_view(self):
        return self.client.get(self.url, follow=True)

    def assert_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.redirect_chain))
        self.assertTemplateUsed(response, 'profile.html')

    def test_for_anonymous_users(self):
        r = self.go_to_profile_view()
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(1, len(r.redirect_chain))
        self.assertEqual(f'/login/?next={self.url}', r.redirect_chain[0][0])

    def test_for_user(self):
        self.login_user()
        self.assert_response(self.go_to_profile_view())

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        self.assert_response(self.go_to_profile_view())

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        self.assert_response(self.go_to_profile_view())

    def test_for_superuser(self):
        self.login_superuser()
        self.assert_response(self.go_to_profile_view())


class MonthViewTest(BaseAPITest):
    def url(self, bookble_id_str):
        return f'/booking/{bookble_id_str}'

    def go_to_month_view(self, bookable):
        return self.client.get(self.url(bookable.id_str), follow=True)

    def assert_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.redirect_chain))
        self.assertTemplateUsed(response, 'month.html')

    def test_invalid_bookables(self):
        # Non-existant bookable
        response = self.client.get(self.url('invalid'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Correct bookable but trailing slash
        bookable = Bookable.objects.filter(public=True).first()
        response = self.client.get(self.url(bookable.id_str) + '/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_for_anonymous_users(self):
        for bookable in Bookable.objects.all():
            r = self.go_to_month_view(bookable)
            if not bookable.public:
                self.assertEqual(r.status_code, status.HTTP_200_OK)
                self.assertEqual(1, len(r.redirect_chain))
                self.assertEqual(f'/login/?next={self.url(bookable.id_str)}', r.redirect_chain[0][0])
            else:
                self.assert_response(r)

    def test_for_user(self):
        self.login_user()
        for bookable in Bookable.objects.all():
            response = self.go_to_month_view(bookable)
            if bookable.hidden and bookable.booking_restriction_groups.count():
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            else:
                self.assert_response(response)

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_month_view(bookable))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_month_view(bookable))

    def test_for_superuser(self):
        self.login_superuser()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_month_view(bookable))


class DayViewTest(BaseAPITest):
    day = "2001-09-11"

    def url(self, bookble_id_str):
        return f'/booking/{bookble_id_str}/{self.day}'

    def go_to_day_view(self, bookable):
        return self.client.get(self.url(bookable.id_str), follow=True)

    def assert_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.redirect_chain))
        self.assertTemplateUsed(response, 'day.html')

    def test_invalid_bookables(self):
        # Non-existant bookable
        response = self.client.get(self.url('invalid'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_for_anonymous_users(self):
        for bookable in Bookable.objects.all():
            r = self.go_to_day_view(bookable)
            if not bookable.public:
                self.assertEqual(r.status_code, status.HTTP_200_OK)
                self.assertEqual(1, len(r.redirect_chain))
                self.assertEqual(f'/login/?next={self.url(bookable.id_str)}', r.redirect_chain[0][0])
            else:
                self.assert_response(r)

    def test_for_user(self):
        self.login_user()
        for bookable in Bookable.objects.all():
            response = self.go_to_day_view(bookable)
            if bookable.hidden and bookable.booking_restriction_groups.count():
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            else:
                self.assert_response(response)

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_day_view(bookable))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_day_view(bookable))

    def test_for_superuser(self):
        self.login_superuser()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_day_view(bookable))


class BookViewTest(BaseAPITest):
    t1 = "2001-09-11T09:30:00"
    t2 = "2001-09-11T10:00:00"

    def url(self, bookble_id_str):
        return f'/booking/book/{bookble_id_str}?st={self.t1}&et={self.t2}'

    def go_to_book_view(self, bookable):
        return self.client.get(self.url(bookable.id_str), follow=True)

    def assert_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.redirect_chain))
        self.assertTemplateUsed(response, 'book.html')

    def test_invalid_bookable(self):
        # Non-existant bookable
        response = self.client.get(self.url('invalid'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_for_anonymous_users(self):
        for bookable in Bookable.objects.all():
            response = self.go_to_book_view(bookable)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertTemplateUsed(response, 'modals/forbidden_login.html')

    def test_for_user(self):
        self.login_user()
        for bookable in Bookable.objects.all():
            response = self.go_to_book_view(bookable)
            if bookable.booking_restriction_groups.count():
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertTemplateUsed(response, 'modals/forbidden.html')
            else:
                self.assert_response(response)

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_book_view(bookable))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_book_view(bookable))

    def test_for_superuser(self):
        self.login_superuser()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_book_view(bookable))


class BookingViewTest(BaseAPITest):
    def url(self, booking_id):
        return f'/booking/booking/{booking_id}'

    def go_to_booking_view(self, bookable):
        b = Booking.objects.filter(bookable=bookable).first()
        return self.client.get(self.url(b.id), follow=True)

    def assert_response(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(0, len(response.redirect_chain))
        self.assertTemplateUsed(response, 'booking.html')

    def test_invalid_booking(self):
        response = self.client.get(self.url('invalid'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(self.url(42))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.get(self.url(5) + '/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_for_anonymous_users(self):
        for bookable in Bookable.objects.all():
            response = self.go_to_booking_view(bookable)
            if not bookable.public:
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertTemplateUsed(response, 'modals/forbidden_login.html')
            else:
                self.assert_response(response)

    def test_for_user(self):
        self.login_user()
        for bookable in Bookable.objects.all():
            response = self.go_to_booking_view(bookable)
            if bookable.hidden and bookable.booking_restriction_groups.count():
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertTemplateUsed(response, 'modals/forbidden.html')
            else:
                self.assert_response(response)

    def test_for_user_part_of_restriction_group(self):
        self.login_user_part_of_restriction_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_booking_view(bookable))

    def test_for_user_part_of_admin_group(self):
        self.login_user_part_of_admin_group()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_booking_view(bookable))

    def test_for_superuser(self):
        self.login_superuser()
        for bookable in Bookable.objects.all():
            self.assert_response(self.go_to_booking_view(bookable))
