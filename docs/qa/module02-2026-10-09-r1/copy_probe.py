import sys,json
sys.stdout.reconfigure(encoding='utf-8');sys.argv=['run.py','observe']
from run import *
from django.utils import translation
rows=[]
for language in ['ru','az','en']:
 with translation.override(language):rows.append({'language':language,'names_gettext':translation.gettext('Названия'),'organizations_gettext':translation.gettext('Организации')})
(HERE/'copy-source-proof.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=False))
