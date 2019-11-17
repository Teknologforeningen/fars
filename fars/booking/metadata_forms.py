from django import forms
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator
from zlib import crc32
from random import choice

### Metadata forms ###

class DoorCodeField(forms.CharField):
    # obfuscated hex hash for the doorcode, as used by Generikey
    def clean(self, value):
        value = super().clean(value)
        return self.get_salted_crc_hash(value) if value else '0'

    def get_salted_crc_hash(self, code):
        # Generate a random hex digit salt
        salt = choice('0123456789abcdef')

        # Calculate the JAMCRC (bitwise-not of the standard CRC-32) of the code plus salt
        hashval = ~crc32((code + salt).encode('ascii', 'ignore'))

        # Get the hex value of the hash, drop the 0x part, pad with zeros
        # The & 0xffffffff is there because we don't want a signed hex
        hexval = hex(hashval & 0xffffffff)[2:].zfill(8)

        # Replace the last character with the salt
        salted = hexval[:-1] + salt

        return salted


class PiSaunaMetadataForm(forms.Form):
    disable_sauna_heating = forms.BooleanField(
        required=False,
        label=_('Disable sauna heating'),
        help_text=_('Check to disable heating of the sauna during your booking')
    )
    restrict_keys = forms.BooleanField(
        required=False,
        label=_('Restrict keys'),
        help_text=_('Check to restrict the door to the Lounge to only open with your key')
    )
    doorcode = DoorCodeField(
        required=False,
        label=_('Doorcode'),
        help_text=_('Optionally provide a doorcode with which the door to the Lounge can be opened during your booking'),
        widget=forms.NumberInput,
        validators=[
            RegexValidator(
                regex='^[0-9]{4,6}$',
                message=_('Doorcode must be 4-6 digits')
            ),
        ]
    )

class HumpsSaunaMetadataForm(forms.Form):
    unlock_door = forms.BooleanField(
        required=False,
        label=_('Unlock door'),
        help_text=_('Check to keep the door unlocked during your booking')
    )
    doorcode = DoorCodeField(
        required=False,
        label=_('Doorcode'),
        help_text=_('Optionally provide a doorcode with which the door to Humpsbadet can be opened during your booking'),
        widget=forms.NumberInput,
        validators=[
            RegexValidator(
                regex='^[0-9]{4,6}$',
                message=_('Doorcode must be 4-6 digits')
            ),
        ]
    )

# These are the choices used in the bookable model.
# Adding your metadata form here will make it available for bookables
METADATA_FORM_OPTIONS = (
    (None, 'No metadata'),
    ('PI', 'Pi sauna'),
    ('HB', 'Humpsbadet'),
)

# This is the mapping from choice string stored in DB to a real class.
# Every choice in METADATA_FORM_OPTIONS should have a form class mapped here 
METADATA_FORM_CLASSES = {
    'PI': PiSaunaMetadataForm,
    'HB': HumpsSaunaMetadataForm
}