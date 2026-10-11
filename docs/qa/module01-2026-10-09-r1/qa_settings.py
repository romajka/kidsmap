from config.settings import *
QA_ROOT = BASE_DIR / '.tmp/module01-20261009-r1'
DEBUG = True
ROOT_URLCONF = 'qa_urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'module01', 'USER': 'module01', 'PASSWORD': '', 'HOST': '127.0.0.1', 'PORT': '55431', 'CONN_MAX_AGE': 0, 'OPTIONS': {'connect_timeout': 5}, 'TEST': {'NAME': 'test_module01'}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'module01-r1'}}
MEDIA_ROOT = QA_ROOT / 'media'
PRIVATE_MEDIA_ROOT = QA_ROOT / 'private-media'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ''
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_MAP_ID = GOOGLE_ANALYTICS_MEASUREMENT_ID = GOOGLE_ANALYTICS_PROPERTY_ID = GOOGLE_OAUTH_CLIENT_ID = GOOGLE_OAUTH_CLIENT_SECRET = GOOGLE_APPLICATION_CREDENTIALS = INDEXNOW_KEY = ''
SOCIALACCOUNT_PROVIDERS = {}
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
PUBLIC_BASE_URL = 'http://localhost:8811'
SESSION_COOKIE_NAME = 'module01_r1_session'
CSRF_COOKIE_NAME = 'module01_r1_csrf'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT = False
LOCALIZED_PLACE_URLS_ENABLED = True
TASK33_R1_WRITE_MODE = 'all'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'
