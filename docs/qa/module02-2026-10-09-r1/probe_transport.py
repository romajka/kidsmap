from pathlib import Path
import sys,json
sys.argv=['run.py','observe']
from run import *
from django.utils.translation import gettext,override
from catalog.domain_admin.business import OrganizationForm
from django.conf import settings
out={'locale_paths':[str(p) for p in settings.LOCALE_PATHS],'i18n':settings.USE_I18N,'translations':{}}
for language in ['ru','az','en']:
    with override(language):out['translations'][language]=str(OrganizationForm().fields['name_az'].label)
print(json.dumps(out,ensure_ascii=True))
