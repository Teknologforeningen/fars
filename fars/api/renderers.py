from rest_framework import renderers
from dateutil import parser
import json

# Renders bookings in the format demanded by GeneriKey
class GeneriKeyBookingRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'

    def render(self, data, media_type=None, renderer_context=None):
        results = []
        for booking in data:
            metadata = json.loads((booking['metadata']))
            booking_str = '{CARD}:{COM}:{START}:{END}:{SPECIAL}:{CODE}'.format(
                CARD=booking['user']['username'],
                COM=booking['booking_group']['name'] if booking['booking_group'] else 0, # TODO: this needs to be LDAP GID
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
        # TODO: check order of these
        # Render a binary bitfield as string
        bitfield = ''.join([
            str(int(metadata['unlock_door'])) if 'unlock_door' in metadata else '0',
            str(int(metadata['disable_sauna_heating'])) if 'disable_sauna_heating' in metadata else '0',
            str(int(metadata['restrict_keys'])) if 'restrict_keys' in metadata else '0',
        ])

        # Convert binary bitfield string to int
        return int(bitfield, 2)


# {"disable_sauna_heating": false, "restrict_keys": true, "doorcode": "3dbc89c9"}
