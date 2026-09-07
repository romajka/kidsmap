"""Run isolated checks; --postgres uses only the dedicated localhost test DB."""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
labels = sys.argv[1:]
postgres = '--postgres' in labels
if postgres:
    labels.remove('--postgres')
labels = labels or ['catalog.testcases.test_volunteer_admin']

# Never inherit production credentials, cache, mail or external integrations.
os.environ.clear()
os.environ.update(
    PATH=os.defpath, DJANGO_SETTINGS_MODULE='config.settings',
    DJANGO_TESTING='1', DJANGO_DEBUG='1',
)
with tempfile.TemporaryDirectory(prefix='kidsmap-volunteer-') as directory:
    os.environ['DATABASE_URL'] = (
        'postgresql://postgres:local-test-only@127.0.0.1:55446/volunteer_tests'
        if postgres else 'sqlite://' + directory + '/checks.sqlite3'
    )
    import django
    from django.conf import settings

    settings.MEDIA_ROOT = Path(directory) / 'media'
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.INDEXNOW_ENABLED = False
    django.setup()
    from django.core.management import call_command

    assert settings.TESTING
    assert settings.CACHES['default']['BACKEND'] == 'django.core.cache.backends.locmem.LocMemCache'
    with patch('requests.sessions.Session.request', side_effect=AssertionError('Unexpected external HTTP')):
        call_command('check')
        call_command('makemigrations', check=True, dry_run=True, verbosity=1)
        call_command('test', *labels, interactive=False, verbosity=1)
