from django import forms
from django.utils.translation import gettext as _
from django.core.validators import RegexValidator

### Metadata forms ###

class DoorCodeField(forms.CharField):
    # obfuscated hex hash for the doorcode, as used by Generikey
    def clean(self, value):
        value = super().clean(value)
        # TODO: implement obfuscated hex hash
        salt = '42'
        return value + salt

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
        ])

# These are the choices used in the bookable model.
# Adding your metadata form here will make it available for bookables
METADATA_FORM_OPTIONS = (
    (None, 'No metadata'),
    ('PI', 'Pi sauna'),
)

# This is the mapping from choice string stored in DB to a real class.
# Every choice in METADATA_FORM_OPTIONS should have a form class mapped here 
METADATA_FORM_CLASSES = {
    'PI': PiSaunaMetadataForm
}