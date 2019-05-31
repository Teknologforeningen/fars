from rest_framework import renderers
from dateutil import parser

# Renders bookings in the format demanded by GeneriKey
class GeneriKeyBookingRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'

    def render(self, data, media_type=None, renderer_context=None):
        results = []
        for booking in data:
            booking_str = '{CARD}:{COM}:{START}:{END}:{SPECIAL}:{CODE}'.format(
                CARD=booking['user']['username'],
                COM=booking['booking_group']['name'] if booking['booking_group'] else 0,
                # The serializer just had to stringify the dates for us, so now we have to parse them again
                START=int(parser.parse(booking['start']).timestamp()),
                END=int(parser.parse(booking['end']).timestamp()),
                # The following fields relate to metadata, and should be implemented in respective metadata forms
                SPECIAL=0,
                CODE=0
            )
            results.append(booking_str)
        
        return '\n'.join(results)
