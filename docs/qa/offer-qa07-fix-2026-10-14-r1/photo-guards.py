from django.db import connection
from django.conf import settings
from django.core.management import call_command
from catalog.testcases.utils import ensure_quality_subcategory
main=connection.settings_dict['NAME'];test=connection.settings_dict['TEST']['NAME'];assert main=='offerqa07fix_20261014_r1' and test=='test_'+main
connection.close();connection.settings_dict['NAME']=test
ensure_quality_subcategory('EDU')
connection.close();connection.settings_dict['NAME']=main
settings.MEDIA_ROOT=settings.BASE_DIR/'.tmp/offer-qa07-fix-2026-10-14-r1/unit-media';settings.PRIVATE_MEDIA_ROOT=settings.BASE_DIR/'.tmp/offer-qa07-fix-2026-10-14-r1/unit-private-media';settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
call_command('test','catalog.testcases.test_offer_qa07_stale_draft_restore.StaleDraftRetirementTests.test_consumed_copy_photo_write_conflicts_without_touching_history','catalog.testcases.test_task33_drafts.DraftApiTests.test_photo_requires_successful_upload_and_is_private','catalog.testcases.test_task33_drafts.DraftApiTests.test_materialize_keeps_uploaded_photo_outside_public_media',keepdb=True,interactive=False,verbosity=1)
