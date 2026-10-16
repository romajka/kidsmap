from config.settings import *
import json
QA_ROOT=BASE_DIR/'.tmp/access-qa04-recheck-2026-10-15-r1'
_cfg=json.loads((QA_ROOT/'config.json').read_text())
_secret=json.loads((QA_ROOT/'credentials.json').read_text())
SECRET_KEY=_secret['django_secret']
DEBUG=False
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':_cfg['database'],'USER':_cfg['user'],'PASSWORD':_secret['db_password'],'HOST':'127.0.0.1','PORT':str(_cfg['pg_port']),'CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5},'TEST':{'NAME':'test_'+_cfg['database']}}}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':QA_ROOT.name}}
EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH=QA_ROOT/'email'
EMAIL_HOST=EMAIL_HOST_USER=EMAIL_HOST_PASSWORD=''
MEDIA_ROOT=QA_ROOT/'media';PRIVATE_MEDIA_ROOT=QA_ROOT/'private-media';STATIC_ROOT=QA_ROOT/'staticfiles'
LOCALE_PATHS=(json.loads((QA_ROOT/'locales/manifest.json').read_text())['locale_root'],)
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_MAP_ID=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_APPLICATION_CREDENTIALS=INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={}
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
PUBLIC_BASE_URL=f"http://127.0.0.1:{_cfg['http_port']}"
SESSION_COOKIE_NAME='accessqa04recheckr1_session';CSRF_COOKIE_NAME='accessqa04recheckr1_csrf'
SESSION_COOKIE_SECURE=CSRF_COOKIE_SECURE=SECURE_SSL_REDIRECT=False
ROOT_URLCONF='qa_urls'
LOCAL_ANALYTICS_STORAGE_ENABLED=False
OWNER_ANALYTICS_ENABLED=False
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
