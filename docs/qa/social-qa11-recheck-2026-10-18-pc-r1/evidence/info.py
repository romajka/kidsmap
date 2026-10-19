import sys,runpy,json
from pathlib import Path
Q=Path(__file__).resolve().parent
mode=sys.argv[1];sys.argv=['runtime.py',mode]
runpy.run_path(str(Q/'runtime.py'))
from django.conf import settings
from django.template.loader import get_template
from django.contrib.staticfiles.finders import find
data={'testing':settings.TESTING,'database_owned':settings.DATABASES['default']['NAME']=='m09full_r1','sole_locales':list(map(str,settings.LOCALE_PATHS)),'templates':{p:get_template(p).origin.name for p in ['catalog/typed_reviews.html','pages/account_notifications.html']},'css':find('css/site.css')}
(Q/(mode+'.json')).write_text(json.dumps(data,indent=2));print(json.dumps(data))
