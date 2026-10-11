from config.settings import *
QA_ROOT = BASE_DIR / '.tmp/module07-20261010-r1'
DEBUG = True
ROOT_URLCONF = 'qa_urls'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'module07', 'USER': 'module07', 'PASSWORD': '', 'HOST': '127.0.0.1', 'PORT': '55438', 'CONN_MAX_AGE': 0, 'OPTIONS': {'connect_timeout': 5}, 'TEST': {'NAME': 'test_module07'}}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'module07-r1'}}
MEDIA_ROOT = QA_ROOT / 'media'
PRIVATE_MEDIA_ROOT = QA_ROOT / 'private-media'
EMAIL_BACKEND = 'qa_mail.EmailBackend'
EMAIL_HOST = EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ''
GOOGLE_MAPS_API_KEY = GOOGLE_MAPS_MAP_ID = GOOGLE_ANALYTICS_MEASUREMENT_ID = GOOGLE_ANALYTICS_PROPERTY_ID = GOOGLE_OAUTH_CLIENT_ID = GOOGLE_OAUTH_CLIENT_SECRET = GOOGLE_APPLICATION_CREDENTIALS = INDEXNOW_KEY = ''
SOCIALACCOUNT_PROVIDERS = {}
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']
PUBLIC_BASE_URL = 'http://localhost:8820'
SESSION_COOKIE_NAME = 'module07_r1_session'
CSRF_COOKIE_NAME = 'module07_r1_csrf'
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT = False
LOCALIZED_PLACE_URLS_ENABLED = True
TASK33_R1_WRITE_MODE = 'all'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
STORAGES['staticfiles']['BACKEND'] = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# SIMULATED existing test retention policy, own synthetic fixtures only.
ACCOUNT_DELETION_RETENTION_POLICY = {'active': True, 'version': 'ADRP-TEST-01', 'effective_date': '2026-09-13', 'approved_by': 'Automated test privacy owner', 'grace_period_days': 30, 'processor_cadence': 'daily', 'review_disposition': 'anonymize_approved_delete_other', 'owner_content_disposition': 'unlink_public_delete_team_access', 'moderation_history_disposition': 'anonymize', 'analytics_disposition': 'delete_user_events', 'audit_retention_days': 365, 'backup_expiry_days': 15, 'public_copy': {'ru': {'deleted': 'Профиль, избранное, реакции и активные приглашения будут удалены.', 'anonymized': 'Опубликованные отзывы сохранятся без связи с аккаунтом и имени автора.', 'legal_hold': 'Обработка может быть отложена только по утверждённому правовому основанию.', 'owner_content': 'Опубликованные карточки сохранятся, а владелец будет отвязан.', 'backups': 'Резервные копии истекают максимум через 15 дней.'}, 'az': {'deleted': 'Profil və şəxsi hesab məlumatları silinəcək.', 'anonymized': 'Dərc edilmiş rəylər hesabla əlaqə olmadan saxlanacaq.', 'legal_hold': 'Təsdiqlənmiş hüquqi əsas olduqda emal təxirə salına bilər.', 'owner_content': 'Dərc edilmiş kartlar saxlanacaq, sahib əlaqəsi silinəcək.', 'backups': 'Ehtiyat nüsxələri ən gec 15 günə silinir.'}, 'en': {'deleted': 'The profile, favorites, reactions and active invitations will be deleted.', 'anonymized': 'Published reviews remain without an account link or author name.', 'legal_hold': 'Processing may be delayed only under an approved legal basis.', 'owner_content': 'Published listings remain and their owner link is removed.', 'backups': 'Backups expire within at most 15 days.'}}}
