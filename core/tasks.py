from __future__ import absolute_import, unicode_literals

import logging

logger=logging.getLogger(__name__)

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

