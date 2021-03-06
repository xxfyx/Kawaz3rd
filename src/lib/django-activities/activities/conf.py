# coding=utf-8
"""
"""

from django.conf import settings
from appconf import AppConf


class ActivitiesAppConf(AppConf):
    # Default template extension which used if no extension for a particular
    # `typename` is specified in TEMPLATE_EXTENSIONS
    DEFAULT_TEMPLATE_EXTENSION = '.html'

    # A dictionary which contains extensions for each `typename`
    TEMPLATE_EXTENSIONS = {
        'twitter': '.txt',
    }

    DEFAULT_NOTIFIERS = ()
    ENABLE_NOTIFICATION = True
    ENABLE_OAUTH_NOTIFICATION = False
