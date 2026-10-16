from django.conf import settings
from django.db import connection
from django.core.management import call_command
from catalog.testcases.utils import ensure_quality_subcategory
main=connection.settings_dict['NAME'];test=connection.settings_dict['TEST']['NAME'];assert main=='module05full_20261014_r1' and test=='test_'+main
connection.close();connection.settings_dict['NAME']=test
for code in ['EDU','TECH','MUS','SPRT']:ensure_quality_subcategory(code)
connection.close();connection.settings_dict['NAME']=main
settings.MEDIA_ROOT=settings.BASE_DIR/'.tmp/module05-full-2026-10-14-r1/unit-media';settings.PRIVATE_MEDIA_ROOT=settings.BASE_DIR/'.tmp/module05-full-2026-10-14-r1/unit-private-media';settings.SESSION_COOKIE_NAME='sessionid';settings.CSRF_COOKIE_NAME='csrftoken'
call_command('test','catalog.testcases.test_task33_admin_editors',keepdb=True,interactive=False,verbosity=2)
