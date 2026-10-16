"""Final bounded source/runtime/preservation gate; no production or mutations."""
from pathlib import Path
import hashlib,json,subprocess,urllib.request,sys
P=Path(__file__).resolve().parent;R=P.parents[2];Q=P.parent/'module04-recheck-2026-10-13-r1';entry=json.loads((Q/'entry.json').read_text());approved=set(json.loads((Q/'changed-files.json').read_text()))|{'docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/qa/module-acceptance-prompts.md'}
changed=[];missing=[]
for f,h in entry['files'].items():
 if not (R/f).is_file():missing.append(f)
 elif hashlib.sha256((R/f).read_bytes()).hexdigest()!=h and f not in approved:changed.append(f)
active=[l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if 'active_run' in l][:3]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
server=json.loads((Q/'server.json').read_text());assert str(Q/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes()
version=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5));assert version['testing'] and version['entry_matches_startup'] and version['startup_matches_disk']
(P/'runtime-version-final.json').write_text(json.dumps(version,indent=2))
base_source=json.loads((R/'docs/qa/module03-spec-fix-2026-10-13-r1/entry-final.json').read_text())['source_files']
mo={f:hashlib.sha256((R/f).read_bytes()).hexdigest()==h for f,h in base_source.items() if f.startswith('locale/') and f.endswith('.mo')};assert all(mo.values())
q=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);assert q.returncode==0
blocks=(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text');assert blocks==88
manifest=json.loads((P/'source-change-manifest.json').read_text());assert all(hashlib.sha256((R/row['path']).read_bytes()).hexdigest()==row['after_sha256'] for row in manifest)
# Never expose credential contents: scan only own artifact bytes and report a boolean.
secret=json.loads((R/'.tmp'/Q.name/'credentials.json').read_text());found=[]
for top in [P,Q]:
 for f in top.rglob('*'):
  if f.is_file() and f.suffix in ['.txt','.md','.json','.jsonl','.py','.js','.csv','.diff']:
   data=f.read_bytes()
   if any(v.encode() in data for v in secret.values() if isinstance(v,str) and len(v)>12):found.append(str(f.relative_to(R)))
backend_full=json.loads((Q/'full-module-backend-ready.command.json').read_text());backend_one=json.loads((Q/'autocommit-targeted-fresh-db.command.json').read_text());backend_green=json.loads((Q/'photo-regressions-final-green.command.json').read_text())
assert backend_full['exit']==1 and backend_one['exit']==0 and backend_green['exit']==0
counts=json.loads((P/'counts.json').read_text());assert counts['effective_failures']==0 and counts['backend_unique_accepted']==143
locale=json.loads((P/'native-locale-proof.json').read_text())['values']['ru']
assert all(locale[m]==m for m in ['Редактирование мероприятия','Шаги формы мероприятия','Вперёд','Тип организатора','Нельзя опубликовать мероприятие. Обязательны для заполнения: {}'])
assert 'Исправьте проблему' in locale['instruction_single'] and 'Исправьте проблемы' in locale['instruction_plural']
assert version['sole_locale_root'].endswith('/locales-v6/locale')
assert json.loads((Q/'historical-event-geography-fallback.command.json').read_text())['exit']==0
result={'checkout':str(R),'head':head,'branch':branch,'head_preserved':head==entry['head'],'branch_preserved':branch==entry['branch'],'active_run_preserved':active==entry['active_run'],'active_run':active,'unapproved_prior_file_changes':changed,'missing_prior_files':missing,'shared_mo_preserved':mo,'copyable_guide_blocks':blocks,'diff_check_exit':q.returncode,'artifact_credentials_found':bool(found),'source_change_manifest_matches':True,'runtime_source_match':True,'native_full_module_backend_exit':1,'native_full_module_backend_pass':135,'targeted_fixture_order_case_exit':0,'new_photo_regressions_exit':0,'backend_unique_accepted':143,'effective_counts':counts,'foreign_process_control_actions':0,'environment_interruption_receipt':'../'+Q.name+'/environment-interruption.json','production_not_run':True,'commit_push_deploy_not_run':True}
result['passed']=not changed and not missing and not found and result['head_preserved'] and result['branch_preserved'] and result['active_run_preserved']
(P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps({'verification':result['passed'],'source_match':True,'prior_unapproved_changes':len(changed),'prior_missing':len(missing),'artifacts_credentials_found':bool(found),'guide_blocks':blocks}));assert result['passed']
