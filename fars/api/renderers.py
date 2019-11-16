from rest_framework import renderers
from dateutil import parser
import json

# Renders bookings in the format demanded by GeneriKey
class GeneriKeyBookingRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'

    def render(self, data, media_type=None, renderer_context=None):
        results = []
        for booking in data:
            metadata = {} if not booking['metadata'] else json.loads((booking['metadata']))
            booking_str = '{CARD}:{COM}:{START}:{END}:{SPECIAL}:{CODE}'.format(
                CARD=booking['user']['username'],
                COM=booking['booking_group']['name'] if booking['booking_group'] else 0,
                # The serializer just had to stringify the dates for us, so now we have to parse them again
                START=int(parser.parse(booking['start']).timestamp()),
                END=int(parser.parse(booking['end']).timestamp()),
                # The following fields relate to metadata, and should be implemented in respective metadata forms
                SPECIAL=self.render_special_bitfield(metadata),
                CODE=metadata['doorcode'] if 'doorcode' in metadata else '0'
            )
            results.append(booking_str)
        
        return '\n'.join(results)


    def render_special_bitfield(self, metadata):
        # Render a binary bitfield as string
        # Note that this order of bits must be preserved.
        bitfield = ''.join([
            str(int(metadata['disable_sauna_heating'])) if 'disable_sauna_heating' in metadata else '0',
            str(int(metadata['restrict_keys'])) if 'restrict_keys' in metadata else '0',
            str(int(metadata['unlock_door'])) if 'unlock_door' in metadata else '0',
        ])

        # Convert binary bitfield string to int
        return int(bitfield, 2)
