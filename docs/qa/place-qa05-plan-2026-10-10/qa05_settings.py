from config.settings import *

QA_ROOT = BASE_DIR / '.tmp/place-qa05-plan-20261010'
DEBUG = True
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'placeqa05_plan',
    'USER': 'placeqa05_plan', 'PASSWORD': '', 'HOST': '127.0.0.1', 'PORT': '55440',
    'CONN_MAX_AGE': 0, 'OPTIONS': {'connect_timeout': 5}, 'TEST': {'NAME': 'test_placeqa05_plan'}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'placeqa05-plan-20261010'}}
MEDIA_ROOT = QA_ROOT / 'media'
PRIVATE_MEDIA_ROOT = QA_ROOT / 'private-media'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ''
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_MAP_ID = GOOGLE_ANALYTICS_MEASUREMENT_ID = GOOGLE_ANALYTICS_PROPERTY_ID = GOOGLE_OAUTH_CLIENT_ID = GOOGLE_OAUTH_CLIENT_SECRET = GOOGLE_APPLICATION_CREDENTIALS = INDEXNOW_KEY = ''
SOCIALACCOUNT_PROVIDERS = {}
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
PUBLIC_BASE_URL = 'http://127.0.0.1:8819'
SESSION_COOKIE_NAME = 'placeqa05_plan_session'
CSRF_COOKIE_NAME = 'placeqa05_plan_csrf'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT = False
LOCALIZED_PLACE_URLS_ENABLED = True
TASK33_R1_WRITE_MODE = 'all'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'
