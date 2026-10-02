"""Imported only by run.py's sanitized child, never production settings."""
import os
from pathlib import Path
if os.environ.get('DJANGO_TESTING') != '1' or not os.environ.get('TASK33_QA_ROOT'):
    raise RuntimeError('Use qa04/run.py; direct settings import is forbidden')
from config.settings import *  # noqa: F403
qa_root=Path(os.environ['TASK33_QA_ROOT']).resolve()
if not str(qa_root).startswith('/tmp/kidsmap-task33-qa04-'):
    raise RuntimeError('Unsafe disposable QA root')
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'qa_stage04','USER':'qa_stage04','PASSWORD':'','HOST':os.environ.get('TASK33_QA_SOCKET',str(qa_root/'socket')),'PORT':'5432','CONN_MAX_AGE':0,'OPTIONS':{'connect_timeout':5,'options':'-c statement_timeout=20000 -c lock_timeout=2000'},'TEST':{'NAME':'test_qa_stage04'}}}
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'task33-stage04'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
EMAIL_HOST='';EMAIL_HOST_USER='';EMAIL_HOST_PASSWORD='';EMAIL_PORT=0
# Keep canonical display senders; clean env + locmem backend already isolate email.
MEDIA_ROOT=qa_root/'media';MEDIA_URL='/media/'
GOOGLE_APPLICATION_CREDENTIALS='';GOOGLE_MAPS_API_KEY='';GOOGLE_MAPS_MAP_ID=''
GOOGLE_ANALYTICS_MEASUREMENT_ID='';GOOGLE_ANALYTICS_PROPERTY_ID=''
GOOGLE_OAUTH_CLIENT_ID='';GOOGLE_OAUTH_CLIENT_SECRET='';INDEXNOW_KEY=''
SOCIALACCOUNT_PROVIDERS={}
DEBUG=False
ALLOWED_HOSTS=['testserver','localhost','127.0.0.1']
SECURE_SSL_REDIRECT=False
# Existing password assertions remain untouched; test-only hashing matches Django testing guidance.
PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher']
TEST_RUNNER='commands.BaselineRunner'
