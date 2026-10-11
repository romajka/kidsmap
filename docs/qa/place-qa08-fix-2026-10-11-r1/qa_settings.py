from config.settings import *
import json

QA_ROOT = BASE_DIR / '.tmp/place-qa08-fix-20261011-r1'
DEBUG = False
SECRET_KEY = (QA_ROOT/'credential').read_text(encoding='utf-8')
ROOT_URLCONF = 'qa_urls'
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':'qa08_district','USER':'qa08_district','PASSWORD':'','HOST':'127.0.0.1','PORT':'55447','CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5},'TEST':{'NAME':'test_qa08_district'}}}
CACHES = {'default': {'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'place-qa08-fix-r1'}}
MEDIA_ROOT = QA_ROOT/'media'
PRIVATE_MEDIA_ROOT = QA_ROOT/'private-media'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ''
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_MAP_ID = GOOGLE_ANALYTICS_MEASUREMENT_ID = GOOGLE_ANALYTICS_PROPERTY_ID = GOOGLE_OAUTH_CLIENT_ID = GOOGLE_OAUTH_CLIENT_SECRET = GOOGLE_APPLICATION_CREDENTIALS = INDEXNOW_KEY = ''
SOCIALACCOUNT_PROVIDERS = {}
ALLOWED_HOSTS = ['localhost','127.0.0.1','testserver']
PUBLIC_BASE_URL = 'http://localhost:8842'
SESSION_COOKIE_NAME = 'qa08_r1_session'
CSRF_COOKIE_NAME = 'qa08_r1_csrf'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT = False
LOCALIZED_PLACE_URLS_ENABLED = True
TASK33_R1_WRITE_MODE = 'all'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'
LOCAL_ANALYTICS_STORAGE_ENABLED = True
OWNER_ANALYTICS_ENABLED = True
ANALYTICS_COLLECTION_STARTED_AT = '2026-08-01T00:00:00+04:00'
ANALYTICS_IDENTITY_HASH_KEY = (QA_ROOT/'credential').read_text(encoding='utf-8')
LOCALE_PROFILE = (QA_ROOT/'locale-profile').read_text(encoding='utf-8').strip()
LOCALE_PATHS = (json.loads((QA_ROOT/LOCALE_PROFILE/'manifest.json').read_text(encoding='utf-8'))['locale_root'],)
