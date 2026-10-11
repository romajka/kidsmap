from pathlib import Path
import subprocess,json,re,sys,gettext,hashlib,datetime
P=Path(__file__).resolve().parent;R=P.parents[2]
node='C:/Program Files/nodejs/node.exe';cmd=[node,'--test','static/js/tests/google_maps_motion.test.js']
r=subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
(P/'js-tests.log').write_text(r.stdout+r.stderr,encoding='utf-8');(P/'js-tests-command.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':r.returncode},indent=2),encoding='utf-8')
p=P/'tests.log';s=p.read_text(encoding='utf-8');s,n=re.subn(r'(name=["\']csrfmiddlewaretoken["\']\s+value=["\'])([^"\']+)',r'\1[LOCAL-CSRF-REDACTED]',s);p.write_text(s,encoding='utf-8')
locale=[]
for lang in ('az','en'):
 mo=R/f'locale/{lang}/LC_MESSAGES/django.mo';po=mo.with_suffix('.po');msg='Показывать «Афишу»'
 with mo.open('rb') as f:t=gettext.GNUTranslations(f)
 locale.append({'language':lang,'message':msg,'runtime_mo_translation':t.gettext(msg),'source_po_contains_message':('msgid "'+msg+'"') in po.read_text(encoding='utf-8'),'mo_sha256':hashlib.sha256(mo.read_bytes()).hexdigest(),'po_sha256':hashlib.sha256(po.read_bytes()).hexdigest(),'mo_tracked':bool(subprocess.check_output(['git','ls-files',str(mo.relative_to(R))],cwd=R,text=True).strip())})
(P/'locale-proof.json').write_text(json.dumps(locale,indent=2,ensure_ascii=False),encoding='utf-8');(P/'redaction.json').write_text(json.dumps({'local_csrf_values_redacted_from_tests_log':n,'application_assertions_changed':False},indent=2))
print('JS tests exit',r.returncode,'local CSRF occurrences redacted',n,'locale proof2');sys.exit(r.returncode)
