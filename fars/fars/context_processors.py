from django.conf import settings

def fars_settings(_):
    return {
        'FARS_FOOTER': settings.FARS_FOOTER,
    }
