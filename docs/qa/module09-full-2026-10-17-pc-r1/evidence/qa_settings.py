from config.settings import *

QA_ROOT = BASE_DIR / '.tmp/module09-full-pc-r1'
SECRET_KEY = '<redacted-disposable-key>'
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'm09full_r1',
    'USER': 'm09full_r1', 'PASSWORD': '', 'HOST': 'm09full-r1-pg', 'PORT': '5432',
    'OPTIONS': {'options': '-c statement_timeout=20000 -c lock_timeout=2000'},
    'TEST': {'NAME': 'test_m09full_r1'}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 's09-fix-r1'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT = QA_ROOT / 'media'
PRIVATE_MEDIA_ROOT = QA_ROOT / 'private-media'
STATIC_ROOT = QA_ROOT / 'staticfiles'
LOCALE_PATHS = [QA_ROOT / 'locales/locale']
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
