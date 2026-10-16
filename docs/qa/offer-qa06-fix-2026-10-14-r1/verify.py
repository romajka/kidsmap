import json,hashlib,subprocess,urllib.request,difflib,polib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];merged={};historical=[]
for name in ['matrix','variants','pending-r3','keyboard','owner','owner-resume','owner-valid','owner-en-save','owner-en-canonical','owner-en-settled']:
 d=json.loads((P/(name+'.result.json')).read_text())
 if d.get('error'):historical.append({'file':name+'.result.json','error':d['error']})
 for row in d.get('rows',[]):
  key='matrix-'+row['kind']+'-'+row['lang']+'-'+str(row['width']) if name=='matrix' else row['id']
  if key=='en-settled-normal-reload-code-values':key='en-reload-code-values'
  merged[key]=row
fails=[(k,v) for k,v in merged.items() if v['status']!='PASS'];assert not fails,fails;assert len(merged)==350,len(merged)
for name,count in [('gettext-check',54),('pending-check',6)]:
 d=json.loads((P/(name+'.json')).read_text());assert len(d['rows'])==count and all(x['status']=='PASS' for x in d['rows'])
assert json.loads((P/'readback.command.json').read_text())['exit']==0
values=json.loads((P/'translations.json').read_text());allowed=set(values)|{'На проверке'}
for lang,count in [('ru',5),('az',11),('en',11)]:
 before=polib.pofile(str(P/('incoming-'+lang+'.po')));after=polib.pofile(str(R/'locale'/lang/'LC_MESSAGES/django.po'));changed=[]
 for e in after:
  old=next((v for v in before if v.msgid==e.msgid and v.msgctxt==e.msgctxt and v.obsolete==e.obsolete),None)
  if not old or old.msgstr!=e.msgstr or old.flags!=e.flags:changed.append(e.msgid)
  if old:
   assert e.occurrences==old.occurrences and e.msgstr_plural==old.msgstr_plural
   if e.msgid not in allowed or e.msgctxt is not None:assert e.msgstr==old.msgstr and e.flags==old.flags
 assert len(changed)==count and set(changed)<=allowed,(lang,changed)
 for key,v in values.items():
  es=[e for e in after if e.msgid==key and e.msgctxt is None and not e.obsolete];assert len(es)==1 and es[0].msgstr==(key if lang=='ru' else v[lang]) and 'fuzzy' not in es[0].flags
 beforetext=(P/('incoming-'+lang+'.po')).read_text();aftertext=(R/'locale'/lang/'LC_MESSAGES/django.po').read_text();(P/('application-'+lang+'.diff')).write_text(''.join(difflib.unified_diff(beforetext.splitlines(True),aftertext.splitlines(True),fromfile='incoming-WORKTREE/locale/'+lang+'/LC_MESSAGES/django.po',tofile='approved-WORKTREE/locale/'+lang+'/LC_MESSAGES/django.po')))
h=json.loads((P/'incoming-source.json').read_text());changed=[k for k,v in h.items() if not (R/k).is_file() or hashlib.sha256((R/k).read_bytes()).hexdigest()!=v];expected={f'locale/{l}/LC_MESSAGES/django.po' for l in ['ru','az','en']};assert set(changed)==expected,changed
snap=json.loads((P/'snapshot.json').read_text());assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==snap['HEAD'];assert subprocess.check_output(['git','branch','--show-current'],cwd=R).decode().strip()==snap['branch'];assert '\nactive_run: NONE\n' in (R/'docs/task33/implementation-status.md').read_text()
server=json.loads((P/'server.json').read_text());assert str(P/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes();receipt=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10));assert receipt['entry_matches_startup'] and receipt['startup_matches_disk'] and receipt['testing'];(P/'runtime-final.json').write_text(json.dumps(receipt,indent=2))
png=[{'file':'screenshots/'+f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'role':'diagnostic' if 'diagnostic' in f.name else 'accepted','note':'Final pending PNG from r3; other unchanged captions may retain r1 provenance. EN reload PNG from settled normal reload.'} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
q=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert q.returncode==0,q.stdout
v={'id':'OFFER-QA-06','status':'CLOSED LOCAL','source_changes':changed,'locale_entries':27,'native_unique_assertions':350,'native_failures':fails,'Django_gettext_service_assertions':60,'read_only_owner_cells':3,'admin_main_cells':54,'admin_other_states_cells':18,'owner_cells':18,'accepted_png':sum(x['role']=='accepted' for x in png),'diagnostic_png':sum(x['role']=='diagnostic' for x in png),'preserved_other_source_files':len(h)-3,'runtime_source_match':True,'initial_harness_failures_retained':historical,'full_ACCEPT05':'NOT RUN','backend_suite':'NOT RUN','global':'NOT RUN','external':'NOT RUN','production':'NOT RUN','git_diff_check_exit':0}
(P/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2));print(json.dumps(v,ensure_ascii=False))
