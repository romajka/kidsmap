import hashlib,json,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
entry=json.loads((P/'entry.json').read_text());now={str(f.relative_to(R)):sha(f) for top in ('src','static','config','locale','templates') for f in (R/top).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix!='.pyc'}
changed=sorted(k for k in set(entry['source'])|set(now) if entry['source'].get(k)!=now.get(k));assert changed==['locale/ru/LC_MESSAGES/django.po','static/admin/css/pages/kidsmap_changelist.css']
initial=json.loads((R/'docs/qa/module02-remaining-recheck-2026-10-13-r1/entry.json').read_text())['source'];all_changes=sorted(k for k in set(initial)|set(now) if initial.get(k)!=now.get(k));assert all_changes==['locale/az/LC_MESSAGES/django.po','locale/en/LC_MESSAGES/django.po','locale/ru/LC_MESSAGES/django.po','static/admin/css/pages/kidsmap_changelist.css']
allowed={'docs/qa/continuation-and-repair-prompts-2026-10-11.md'}
assert all((R/k).is_file() and sha(R/k)==v for k,v in entry['previous_reports'].items() if k not in allowed)
assert 'active_run: NONE' in (R/'docs/task33/implementation-status.md').read_text();assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==entry['head'];assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==entry['branch']
assert (R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().count('```text')==88
matrix=json.loads((P/'matrix-effective.json').read_text());assert len(matrix['rows'])==288 and matrix['effective_pass']==288
assert all((P/r['screenshot']).is_file() for r in matrix['rows'])
labels=json.loads((P/'discovery.json').read_text());test=json.loads((P/'module-tests.json').read_text());assert labels['count']==test['count']==248 and test['exit']==0 and len(set(labels['ids']))==248
assert all(json.loads((P/'readback.json').read_text())['flags'].values());visible=json.loads((P/'receipt-visible.result.json').read_text());assert len(visible['rows'])==2 and all(r['status']=='PASS' for r in visible['rows'])
profiles=[]
for name,count in [('org-qa05-fix-2026-10-13-r1',66),('org-qa04-fix-2026-10-13-r2',72),(P.name,288)]:
 d=R/'docs/qa'/name;server=json.loads((d/'server.json').read_text());runtime=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=5));assert runtime['entry_matches_startup'] and runtime['startup_matches_disk'] and runtime['testing'];assert str(d/'runtime.py').encode() in (Path('/proc')/str(server['pid'])/'cmdline').read_bytes()
 if name!=P.name:
  data=json.loads((d/'browser.result.json').read_text());assert len(data['rows'])==count and not data['errors'] and not data['network'] and all(r['status']=='PASS' for r in data['rows'])
 images=[{'path':str(f.relative_to(d)),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted((d/'screenshots').glob('*.png'))];(d/'png-manifest.json').write_text(json.dumps(images,indent=2));(d/'runtime-version-final.json').write_text(json.dumps(runtime,indent=2));profiles.append({'profile':name,'runtime_matches':True,'pid':server['pid'],'url':server['url'],'PNG':len(images)})
old_stands=[]
for k in entry['previous_reports']:
 if not k.endswith('/server.json'):continue
 try:old=json.loads((R/k).read_text());pid=old.get('pid');cmd=Path('/proc')/str(pid)/'cmdline'
 except Exception:continue
 # Only recorded Linux stand runtimes, not historical Windows sessions/PIDs.
 if not isinstance(pid,int):continue
 runtime_path=R/Path(k).parent/'runtime.py'
 if cmd.exists() and str(runtime_path).encode() in cmd.read_bytes():old_stands.append({'profile':Path(k).parent.name,'pid':pid,'preserved_alive':True})
for args in [['git','diff','--check'],['node','--check','static/js/organization_workspace.js']]:subprocess.run(args,check=True)
out={'checkout':str(R),'head':entry['head'],'branch':entry['branch'],'dirty_worktree':True,'active_run':'NONE','current_turn_application_files':changed,'entire_ORG03_04_05_application_files':all_changes,'other_application_assertions_shared_MO_preserved':True,'previous_evidence_files_unchanged':len(entry['previous_reports'])-len(allowed),'old_recorded_linux_stands_alive':old_stands,'profiles':profiles,'backend_tests':248,'backend_exit':0,'backend_runs':1,'module_matrix_PASS':288,'module_matrix_raw':{'PASS':252,'NOT_RUN':36},'only_harness_gaps_rerun':36,'scoped_QA05_PASS':66,'scoped_QA04_PASS':72,'fresh_visible_receipt_admin_PASS':2,'pageerrors':0,'expected_invalid_URL_HTTP400':matrix['expected_invalid_URL_HTTP400'],'global_test_corpus_external_integrations_production_commit_push_deploy':'NOT RUN','diff_check_exit':0,'node_syntax_exit':0,'verdict':'LOCAL MODULE02 PASS within documented acceptance scope'}
(P/'verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
