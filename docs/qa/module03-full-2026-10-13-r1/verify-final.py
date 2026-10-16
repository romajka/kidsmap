"""Preservation and final evidence checks; no credentials or process mutations."""
import hashlib,json,subprocess,urllib.request
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];Q=P.parent/'module03-spec-fix-2026-10-13-r1';S=R/'.tmp'/Q.name
snapshot=json.loads((P.parent/'module03-plan-2026-10-13-r1/snapshot.json').read_text())
allowed={'requirements.txt','src/catalog/services/specialist_documents.py','src/catalog/controllers/specialist_workspace.py','src/catalog/forms.py','static/css/pages/specialists.css','src/catalog/testcases/test_task33_specialist_screens_security.py','src/catalog/testcases/test_task33_specialist_workspace.py','src/catalog/testcases/specialists.py','src/catalog/testcases/test_task33_specialist_db_review.py','docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/qa/module-acceptance-prompts.md'}|{f'locale/{lang}/LC_MESSAGES/django.po' for lang in ['ru','az','en']}
changed=[s for s,h in snapshot['sha256'].items() if not (R/s).is_file() or hashlib.sha256((R/s).read_bytes()).hexdigest()!=h]
assert set(changed)<=allowed,changed
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==snapshot['HEAD']
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==snapshot['branch']
assert snapshot['active_run'] in (R/'docs/task33/implementation-status.md').read_text().splitlines()
for lang in ['ru','az','en']:
 p=f'locale/{lang}/LC_MESSAGES/django.po';text=(R/p).read_text();base=text[:text.index('\n#: src/catalog/services/specialist_document_validation.py')];assert hashlib.sha256(base.encode()).hexdigest()==snapshot['sha256'][p],lang
assert len((R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text().split('```text'))-1==88
assert json.loads((Q/'green-targeted.json').read_text())['exit']==0
assert json.loads((P/'backend-supplement.command.json').read_text())['exit']==0
ids=json.loads((P/'discovery.json').read_text())['ids'];assert len(ids)==len(set(ids))==154
assert len(json.loads((P/'supplement-labels.json').read_text()))==8
server=json.loads((Q/'server.json').read_text());version=json.load(urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=15));assert version['testing'] and version['entry_matches_startup'] and version['startup_matches_disk']
(P/'runtime-version-final.json').write_text(json.dumps(version,indent=2))
root=json.loads((S/'config.json').read_text());proc=Path('/proc')/str(server['pid']);assert str(Q/'runtime.py').encode() in (proc/'cmdline').read_bytes()
for p in ['assertion-preservation.json']:
 assert all(v['existing_assertions_unchanged'] for v in json.loads((Q/p).read_text()).values())
assert all(v['all_original_business_assertions_retained'] for v in json.loads((P/'supplement-assertion-preservation.json').read_text()).values())
assert all(json.loads((P/'readback.json').read_text())['genuine_download_bytes_match'].values())
mo_preserved=all(s not in changed for s in snapshot['sha256'] if s.endswith('.mo'))
assert mo_preserved
old=json.loads((P/'previous-stands.json').read_text());alive=[x for x in old if x['alive']];assert all((Path('/proc')/str(x['pid'])).exists() for x in alive)
check=subprocess.run(['git','diff','--check'],capture_output=True,text=True);assert check.returncode==0,check.stdout
result={'HEAD':snapshot['HEAD'],'branch':snapshot['branch'],'active_run_preserved':True,'preexisting_files':len(snapshot['sha256']),'preserved_preexisting_files':len(snapshot['sha256'])-len(changed),'changed_within_scope':changed,'shared_MO_unchanged':True,'old_live_server_receipts_preserved':len(alive),'test_methods_accepted':154,'test_execution':'146 from original full batch plus8 targeted approved supplement; unchanged full suite not repeated','targeted_tests_PASS':91,'runtime_source_match':True,'loopback_url':server['url'],'pid':server['pid'],'locale_root':version['sole_locale_root'],'diff_check_exit':0,'commit_push_deploy_production':'NOT RUN'}
(P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
