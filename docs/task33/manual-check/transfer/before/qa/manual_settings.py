from settings import *  # isolated QA04 settings
DEBUG=True
QA_ROOT=qa_root
ROOT_URLCONF='manual_urls'
PUBLIC_BASE_URL='http://localhost:8780'
TASK33_R1_WRITE_MODE='all'
LOCALIZED_PLACE_URLS_ENABLED=True
PRIVATE_MEDIA_ROOT=qa_root/'private-media'
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_NAME='kidsmap_manual_session'
CSRF_COOKIE_NAME='kidsmap_manual_csrf'
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
SECURE_HSTS_SECONDS=0
