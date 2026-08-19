from django.conf import settings

def fars_settings(_):
    return {
        'FARS_FOOTER_PUBLIC': settings.FARS_FOOTER_PUBLIC,
        'FARS_FOOTER_PRIVATE': settings.FARS_FOOTER_PRIVATE,
    }
