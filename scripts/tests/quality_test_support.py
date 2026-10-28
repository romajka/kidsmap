"""Minimal offline settings for runner unit tests; never load project credentials."""
import os
from pathlib import Path
import sys

os.environ['DJANGO_TESTING'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from django.conf import settings

if not settings.configured:
    settings.configure(
        SECRET_KEY='fictional-runner-unit-tests', INSTALLED_APPS=[],
        LANGUAGE_CODE='az', USE_I18N=True,
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
        CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    )
    import django
    django.setup()
