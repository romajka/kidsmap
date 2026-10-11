from config.settings import *
from pathlib import Path
import os
OWN = Path('C:/kidsmap/.tmp/module13-20261011-r1/test-review/baseline')
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'module13','USER':'module13','PASSWORD':'','HOST':'127.0.0.1','PORT':'55444','CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5},'TEST':{'NAME':'test_module13_head'}}}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'module13-head'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST=EMAIL_HOST_USER=EMAIL_HOST_PASSWORD=''
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_MAP_ID=GOOGLE_ANALYTICS_MEASUREMENT_ID=GOOGLE_ANALYTICS_PROPERTY_ID=GOOGLE_OAUTH_CLIENT_ID=GOOGLE_OAUTH_CLIENT_SECRET=GOOGLE_APPLICATION_CREDENTIALS=INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={}
MEDIA_ROOT=OWN/'media';PRIVATE_MEDIA_ROOT=OWN/'private-media'
PUBLIC_BASE_URL='http://testserver'
ALLOWED_HOSTS=['testserver','127.0.0.1','localhost']
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES['staticfiles']['BACKEND']='django.contrib.staticfiles.storage.StaticFilesStorage'
TASK33_R1_WRITE_MODE='all'
LOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=LOCALIZED_PLACE_URLS_ENABLED=False
if os.environ.get('KIDSMAP_QA_COMPILED_HEAD')=='1':
    DATABASES['default']['TEST']['NAME']='test_module13_head_compiled'
    LOCALE_PATHS=[OWN.parent/'head-gettext/locale']
