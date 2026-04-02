# -*- coding: utf-8 -*-

from django.conf import settings


def sige_version(request):
    return {
        'versao': settings.APP_VERSION,
        'app_display_name': settings.APP_DISPLAY_NAME,
        'app_brand_primary': settings.APP_BRAND_PRIMARY,
        'app_brand_accent': settings.APP_BRAND_ACCENT,
        'app_tagline': settings.APP_TAGLINE,
        'app_version': settings.APP_VERSION,
        'app_copyright_start_year': settings.APP_COPYRIGHT_START_YEAR,
        'app_docs_url': settings.APP_DOCS_URL,
    }
