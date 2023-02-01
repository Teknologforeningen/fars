from getenv import env
from fars.settings import TIME_ZONE
from django.utils import timezone
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from threading import Thread
import logging, json

logger = logging.getLogger(__name__)

# XXX: Translations?

class GoogleCalendar:
    def __init__(self, calendar_id):
        self.calendar_id = calendar_id
        self.service = build(
            'calendar',
            'v3',
            credentials=Credentials.from_service_account_file(
                env('GOOGLE_SERVICE_ACCOUNT_FILE'),
                scopes=['https://www.googleapis.com/auth/calendar'],
            )
        )

    def _create_event_timestamp(self, date):
        return {
            'dateTime': date.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': str(date.tzinfo) if timezone.is_aware(date) else TIME_ZONE,
        }

    def _create_event_description_footer(self, booking):
        description = ''

        name = booking.user.get_full_name() or booking.user.username
        description += f'<b>Booked by:</b> {name}'

        group = booking.booking_group
        if group:
            description += f'\n<b>Group:</b> {group}'

        base_url = env('FARS_BASE_URL', '')
        if base_url:
            # XXX: Booking ID not available if it has not been inserted yet. Not that the page showing an individual booking is meant to be shown on its own anyway...
            if booking.id:
                url = f'{base_url}/booking/booking/{booking.id}'
            else:
                url = f'{base_url}/booking/{booking.bookable.id_str}/{booking.start.strftime("%Y-%m-%d")}'

            description += f'\n<b>Booking:</b> {url}'

        description += '\n\n<i><font size="-2">This event was automatically generated/updated'
        description += f'\nat {timezone.localtime(timezone.now())}'
        description += f'\nby FARS{f" at {base_url}" if base_url else ""}</font></i>'

        # XXX: Adding attendees directly to the event can not be done by Google service acccounts
        # Adding them to the description instead, so that they can be invited through the use of a Google Script
        emails = booking.emails
        if booking.user.email:
            emails.append(booking.user.email)
        if len(emails):
            # Do not translate!
            description += '\n\nInvite list:\n' + '\n'.join(emails)

        return description

    """
    Create a body for a Google Calendar event.
    A previous event body can be provided to update it instead.
    Note that changes made to the event manually through Google Calendar migth get overridden if booking is updated.
    """
    def _create_event_body(self, booking, body = {}):
        # Always update these fields no matter what
        # XXX: This will lead to manual changes to the event being overridden. Is this always OK?
        body['summary'] = booking.comment
        body['start'] = self._create_event_timestamp(booking.start)
        body['end'] = self._create_event_timestamp(booking.end)
        body['status'] = 'confirmed'

        # Description is special because it should be both updated and preserved
        sep = 42*'-'
        footer = f'\n\n{sep}\n{self._create_event_description_footer(booking)}'
        if 'description' not in body:
            body['description'] = footer
        else:
            body['description'] = body['description'].replace('<br>', '\n').split(sep)[0].strip() + footer

        # Set these fields only at event creation
        if 'location' not in body:
            body['location'] = booking.bookable.google_calendar_event_location
        if 'visibility' not in body:
            body['visibility'] = 'private'
        if 'conferenceData' not in body:
            body['conferenceData'] = {
                'createRequest': {
                    'conferenceSolutionKey': {
                        'type': 'hangoutsMeet',
                    },
                },
            },
        if 'organizer' not in body and booking.user.email:
            body['organizer'] = {
                'email': booking.user.email,
            },
        if 'recurrence' not in body and booking.recurrence:
            f = booking.recurrence['frequency']
            date_str = booking.recurrence['repeat_until'].replace('-', '')
            body['recurrence'] = [
                f'RRULE:FREQ=DAILY;INTERVAL={f};UNTIL={date_str}T235959Z',
            ]

        return body

    def try_create_event(self, booking):
        try:
            return self.service.events().insert(
                calendarId=self.calendar_id,
                body=self._create_event_body(booking),
            ).execute()

        except HttpError as e:
            logger.error(e)

        return None

    def try_update_event_by_id(self, event_id, booking):
        try:
            event = self.try_get_event_by_id(event_id)

            return self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=self._create_event_body(booking, event),
            ).execute()

        except HttpError as e:
            logger.error(e)

        return None

    """
    Get the Google Calendar event that corresponds to a certain booking.
    """
    def try_get_event_by_id(self, event_id):
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id,
            ).execute()
            return event

        except HttpError as e:
            logger.error(e)

        return None

    '''
    Delete the Google Calendar event for a booking, if it exist.
    '''
    def try_delete_event_by_id(self, event_id):
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            return True

        except HttpError as e:
            error = json.loads(e.content)['error'] # = { errors, code, message }

            # If the event has already been deleted, OK
            if error['code'] == 410:
                return True
            logger.error(e)

        return False


class GCalCreateEventThread(Thread):
    def __init__(self, booking):
        self.booking = booking
        self.calendar_id = booking.bookable.google_calendar_id
        Thread.__init__(self)

    def run(self):
        if self.booking.get_gcalevent():
            raise Exception(f'Booking already has a Google Calendar event')
        event = GoogleCalendar(self.calendar_id).try_create_event(self.booking)
        if event:
            from .models import GCalEvent
            gcalevent = GCalEvent.objects.create(booking=self.booking, event_id=event['id'])
            gcalevent.save()


class GCalUpdateEventThread(Thread):
    def __init__(self, gcalevent):
        self.event_id = gcalevent.event_id
        self.calendar_id = gcalevent.get_calendar_id()
        self.booking = gcalevent.booking
        Thread.__init__(self)

    def run(self):
        GoogleCalendar(self.calendar_id).try_update_event_by_id(self.event_id, self.booking)


class GCalDeleteEventThread(Thread):
    def __init__(self, gcalevent):
        self.event_id = gcalevent.event_id
        # Important to store calendar id already here, since event->booking->bookable->calendar_id is not accessible once the thread gets around to it if the Booking is already deleted
        self.calendar_id = gcalevent.get_calendar_id()
        Thread.__init__(self)

    def run(self):
        GoogleCalendar(self.calendar_id).try_delete_event_by_id(self.event_id)
