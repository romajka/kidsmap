"""Exact wording oracle for the four approved-plan candidates; expected RED before patch."""
import gettext,json,sys,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent
s=json.loads((H/'server.json').read_text());state=json.load(urllib.request.urlopen(s['url']+'/qa/source/',timeout=10));m=json.loads((H/'locale-manifest.json').read_text());entries=json.loads((H/'exact-entries.json').read_text());rows=[]
for lang,expected in entries.items():
 with open(Path(m['locale_root'])/lang/'LC_MESSAGES/django.mo','rb')as fp:catalog=gettext.GNUTranslations(fp)
 for entry in expected:
  for kind,actual in [('runtime',state['translations'][lang][entry['msgid']]),('own MO',catalog.gettext(entry['msgid']))]:rows.append({'lang':lang,'kind':kind,'msgid':entry['msgid'],'actual':actual,'expected':entry['planned'],'status':'PASS'if actual==entry['planned']else'FAIL'})
result={'classification':'exact same expected strings as RED; GREEN required','rows':rows,'fail':sum(r['status']=='FAIL'for r in rows)}
(H/'locale-regression-green.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'checks':len(rows),'fail':result['fail']}));sys.exit(1 if result['fail']else 0)
