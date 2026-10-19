from config.settings import *

QA_ROOT = BASE_DIR / '.tmp/site08-pc-followup-r1'
SECRET_KEY = 'fictional-disposable-site19-plan-only'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'm10s08_followup_r1',
    'USER': 'm09full_r1', 'PASSWORD': '', 'HOST': 'm09full-r1-pg', 'PORT': '5432',
    'OPTIONS': {'options': '-c statement_timeout=20000 -c lock_timeout=2000'},
    'TEST': {'NAME': __import__('json').loads((QA_ROOT/'stage.json').read_text()).get('test_db', 'test_m10s08_followup_r1')}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'm10s08-followup-r1'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT = __import__('pathlib').Path('/tmp/site08-pc-followup-r1-media')
PRIVATE_MEDIA_ROOT = QA_ROOT / 'private-media'
STATIC_ROOT = QA_ROOT / 'staticfiles'
LOCALE_PATHS = [QA_ROOT / __import__('json').loads((QA_ROOT/'stage.json').read_text())['locales'] / 'locale']
ROOT_URLCONF = 'qa_urls'
GOOGLE_APPLICATION_CREDENTIALS = ''
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_MAP_ID = GOOGLE_ANALYTICS_MEASUREMENT_ID = GOOGLE_ANALYTICS_PROPERTY_ID = ''
GOOGLE_OAUTH_CLIENT_ID = GOOGLE_OAUTH_CLIENT_SECRET = INDEXNOW_KEY = ''
SOCIALACCOUNT_PROVIDERS = {}
LOCAL_ANALYTICS_STORAGE_ENABLED = OWNER_ANALYTICS_ENABLED = False
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT = False
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
LOGGING = {'version': 1, 'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'}}

# Own test storage/cache are separate from the normal QA fixture.
if len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='test':
    MEDIA_ROOT=__import__('pathlib').Path('/tmp/site08-pc-followup-r1-test-media')
    PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'
    CACHES['default']['LOCATION']='m10s08-followup-r1-test'
