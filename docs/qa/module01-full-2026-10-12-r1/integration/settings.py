from config.settings import *
from pathlib import Path
import json
QA_ROOT=BASE_DIR/'.tmp/module01-full-2026-10-12-r1/integration'
_cfg=json.loads((BASE_DIR/'.tmp/start-local-2026-10-12-r1/config.json').read_text())
_secret=json.loads((BASE_DIR/'.tmp/start-local-2026-10-12-r1/credentials.json').read_text())
SECRET_KEY=_secret['django_secret']
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'accept01_integration_20261012_r1','USER':_cfg['user'],'PASSWORD':_secret['db_password'],'HOST':'127.0.0.1','PORT':str(_cfg['pg_port']),'CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5},'TEST':{'NAME':'test_accept01_integration_20261012_r1'}}}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'accept01-integration-20261012-r1'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST=EMAIL_HOST_USER=EMAIL_HOST_PASSWORD=''
MEDIA_ROOT=QA_ROOT/'media';PRIVATE_MEDIA_ROOT=QA_ROOT/'private-media';STATIC_ROOT=QA_ROOT/'staticfiles'
LOCALE_PATHS=(json.loads((QA_ROOT/'locales/manifest.json').read_text())['locale_root'],)
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_MAP_ID=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_APPLICATION_CREDENTIALS=INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={}
ALLOWED_HOSTS=['127.0.0.1','localhost','testserver']
ROOT_URLCONF='config.urls'
LOCAL_ANALYTICS_STORAGE_ENABLED=False
OWNER_ANALYTICS_ENABLED=False
STORAGES={'default':{'BACKEND':'django.core.files.storage.FileSystemStorage'},'staticfiles':{'BACKEND':'django.contrib.staticfiles.storage.StaticFilesStorage'}}
