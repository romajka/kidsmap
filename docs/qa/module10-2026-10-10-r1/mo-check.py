import sys,json,gettext,hashlib
sys.argv=['run.py','qa-source-check'];from run import *
from django.utils.translation import override,gettext as translate
from catalog.models.site import SiteVisibilitySettings
out={}
for lang in ['ru','az','en']:
 path=ROOT/'locale'/lang/'LC_MESSAGES/django.mo'
 raw=gettext.GNUTranslations(path.open('rb'))
 with override(lang):
  out[lang]={'mo_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'fields':{field:{'raw_mo':raw.gettext(field),'runtime':translate(field)} for field in ['Показывать «Афишу»','Показывать «Педагогов и специалистов»','Показывать «Организации»']}}
(HERE/'mo-evidence.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print('PO/MO source/runtime observations saved; no catalogs changed')
