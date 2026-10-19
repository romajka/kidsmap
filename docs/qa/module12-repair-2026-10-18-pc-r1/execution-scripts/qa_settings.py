from config.settings import *

QA_ROOT = BASE_DIR / '.tmp/m12-full-r1'
SECRET_KEY = 'fictional-disposable-site19-plan-only'
DEBUG = False
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'm12full_r1',
    'USER': 'm12_guard', 'PASSWORD': '', 'HOST': '127.0.0.1', 'PORT': '55493',
    'OPTIONS': {'options': '-c statement_timeout=20000 -c lock_timeout=2000'},
    'TEST': {'NAME': __import__('json').loads((QA_ROOT/'stage.json').read_text()).get('test_db', 'test_m10seq_red02_r1')}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'm12full-r1'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT = __import__('pathlib').Path('/tmp/m12-full-r1-media')
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
    MEDIA_ROOT=__import__('pathlib').Path('/tmp/m12-full-r1-test-media')
    PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'
    CACHES['default']['LOCATION']='m12full-r1-test'

PUBLIC_BASE_URL = 'http://127.0.0.1:33780'

MEDIA_ROOT=QA_ROOT/'media'
LOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=True
ANALYTICS_IDENTITY_HASH_KEY='fictional-module12-disposable-identity-key'
CSRF_TRUSTED_ORIGINS=[]
if len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='test':
 MEDIA_ROOT=QA_ROOT/'test-media'
 PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'
 LOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=False
 PUBLIC_BASE_URL=''
 ROOT_URLCONF='config.urls'

MIDDLEWARE=['qa_simulation.SimulationMiddleware']+list(MIDDLEWARE)

if len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='test':
 CACHES['default']['LOCATION']='m12-full-r1-test'

ANALYTICS_RAW_EVENT_RETENTION_DAYS=90
ANALYTICS_COLLECTION_STARTED_AT='2026-08-20T00:00:00+04:00'
