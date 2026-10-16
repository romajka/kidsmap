import json,hashlib,difflib,subprocess
from pathlib import Path
import polib
P=Path(__file__).resolve().parent;R=P.parents[2];M=R/'docs/qa/module05-full-2026-10-14-r1';S=R/'.tmp'/M.name
ids={'Абонемент','Лагерь','Тур','Дополнительная услуга','Точная цена','Диапазон','По запросу','Год','Индивидуальный'};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for lang in ['ru','az','en']:
 old=(P/('incoming-'+lang+'.po')).read_text();phase=(S/'locales-offer10/source'/lang/'LC_MESSAGES/django.po').read_text();oldpo=polib.pofile(old);newpo=polib.pofile(phase)
 def entries(po):return{(e.msgctxt,e.msgid,e.msgid_plural,e.obsolete):(e.msgstr,e.msgstr_plural,e.flags,e.comment,e.tcomment,e.occurrences) for e in po}
 a,b=entries(oldpo),entries(newpo);assert set(a)==set(b);changed=[k for k in a if a[k]!=b[k]]
 if lang=='ru':assert old==phase
 else:assert {k[1] for k in changed}==ids and all(not k[0] for k in changed)
 (P/('diff-'+lang+'.patch')).write_text(''.join(difflib.unified_diff(old.splitlines(True),phase.splitlines(True),fromfile='incoming/'+lang+'.po',tofile='approved/'+lang+'.po')))
 current=polib.pofile(str(R/'locale'/lang/'LC_MESSAGES/django.po'))
 for key in ids:
  expected=newpo.find(key).msgstr;e=current.find(key);assert e.msgstr==expected and 'fuzzy' not in e.flags
for n in ['locale-build','django-locales','readback']:assert json.loads((P/(n+'.command.json')).read_text())['exit']==0
first=json.loads((P/'native.result.json').read_text());owner=[x for x in first['rows'] if x['id'].startswith('owner-')];assert len(owner)==216 and all(x['status']=='PASS' for x in owner)
admin=json.loads((P/'admin-accept.result.json').read_text());matrix=[x for x in admin['rows'] if x['id'].startswith('admin-')];assert len(matrix)==216 and all(x['status']=='PASS' for x in matrix)
extra=[x for x in admin['rows'] if x['status']=='PASS' and not x['id'].startswith('admin-')];assert len(extra)==4
bug=json.loads((P/'select2-diagnostic.result.json').read_text());assert not bug.get('error') and bug['after']=={'DOM':'tour','nested':'membership'}
readback=json.loads((P/'readback.json').read_text());assert readback['candidate_product_type']=='membership' and readback['live'][0]['price']=='20.00'
prior=json.loads((M/'counts.json').read_text());assert all(sha(R/k)==v for k,v in prior['test_file_hashes'].items())
incoming=json.loads((P/'incoming-source.json').read_text());changed=[k for k,v in incoming.items() if sha(R/k)!=v]
common=[k for k in incoming if k.startswith('locale/') and k.endswith('.mo')];assert all(sha(R/k)==incoming[k] for k in common)
q=subprocess.run(['git','diff','--check','--','locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'],capture_output=True,text=True);assert q.returncode==0,q.stdout
png=[{'file':'screenshots/'+f.name,'sha256':sha(f)} for f in sorted((P/'screenshots').glob('*.png'))];(P/'png-manifest.json').write_text(json.dumps(png,indent=2))
v={'id':'OFFER-QA-10','decision':'CLOSED LOCAL enum captions; full module05 FAIL due separate OFFER11','application_files_changed_by_this_task':['locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po'],'entries_changed':18,'ru_changed_by_task':False,'Django_target_checks':54,'prior_caption_checks':30,'native_matrix_cells':36,'native_matrix_checks':432,'owner_native_save_reload_checks':4,'native_admin_selection_save':'FAIL OFFER11 confirmed independently; not a locale regression','fresh_readback':'READ ONLY own PostgreSQL; live20, candidateoldmembership','full334_tests':'reused hashes; not rerun','PNG':len(png),'current_changed_input_paths':changed,'foreign_changes':'preserved, no revert; phase copies demonstrate only18authorized entries','shared_MO_preserved':True,'active_run':'NONE preserved','runtime':'initial owned start0; final refresh1 because foreign PO changed; no stale-verification bypass','open_findings':['OFFER-QA-11'],'next_plan':'docs/superpowers/plans/2026-10-14-offer-qa11-admin-select2-serialization.md','production':'NOT RUN'};(P/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps({'id':v['id'],'native':436,'Django':84,'PNG':len(png),'full_module05':'FAIL: OFFER11 OPEN'}))
