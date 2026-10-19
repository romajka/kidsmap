import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=json.loads((O/'evidence/browser-site03-r2.json').read_text());g=json.loads((S/'evidence/green-backend.json').read_text())
checks=[v for r in n['rows'] for v in r['checks'].values()];bad=[r for r in n['rows'] if False in r['checks'].values()]
assert len(checks)==337 and sum(checks)==331 and len(bad)==6 and all(r['width']==1280 and [k for k,v in r['checks'].items() if not v]==['no_document_overflow'] for r in bad)
assert g['exit']==0 and len(g['test_ids'])==30 and not n['pageerrors'] and not n['local_errors'] and n['initial']['values']==n['final']['values']
v={'status':'CLOSED LOCAL scoped SITE03; existing SITE18 header remains OPEN','backend_methods':30,'native_rows':41,'native_checks':337,'PASS':331,'known_SITE18_FAIL':6,'original_settings_restored':True,'initial_harness_failures_retained':'initial-harness; CRLF serialization and actual Tab order verified separately','full_module_acceptance':'PENDING'}
(S/'verification.json').write_text(json.dumps(v,indent=2));(S/'REPORT.md').write_text('# SITE03 CLOSED LOCAL\n\nConfigured localized contact text now uses existing context with escaped linebreaks. Fresh30 cumulative backend methods PASS. Native admin saves,3languages/6widths,configured/blank copy,escaping,links and keyboard:41rows337checks331PASS,6existing SITE18 header1280 overflowFAIL. Original settings restored. Initial observer assumptions retained and corrected from actual form serialization/Tab-order evidence. No production or module-wide PASS claim.\n')
p=json.loads((O/'progress.json').read_text());p.update(closed=['02','03'],active='04',remaining_OPEN=13);(O/'progress.json').write_text(json.dumps(p,indent=2))
docs=json.loads((O/'document-current.json').read_text())
for rel,h in docs.items():
 path=R/rel;assert sha(path)==h;prefix='' if rel.startswith('docs/qa/') else '../qa/'
 path.write_bytes(path.read_bytes()+('\n\n## Module10 SITE03 CLOSED LOCAL — 2026-10-18 pc-r1\n\n[Report]('+prefix+O.name+'/stages/SITE03/REPORT.md). Saved contacts text now visible with safe line breaks in AZ/RU/EN. Fresh30 cumulative backend methods PASS; corrected native41rows337checks331PASS/6known SITE18 header1280 FAIL. Initial failed observer assumptions retained with serialization/keyboard evidence. Original settings restored. Remaining13OPEN(7P2/6P3); continue SITE04 under existing sequential immediate-fix authorization.\n').encode());docs[rel]=sha(path)
(O/'document-current.json').write_text(json.dumps(docs,indent=2))
S=O/'stages/SITE04';D=S/'query-control-investigation';D.mkdir(exist_ok=True)
for source,dest in [(Q/'test_site04_candidate.py',D/'test-with-home-query-assumption.py'),(S/'evidence/red-backend.json',D/'red-r2.json'),(Q/'site04-red.log',D/'red-r2.log')]:dest.write_bytes(source.read_bytes())
(D/'finding.md').write_text('Home q is intentionally removed by CleanPublicQueryMiddleware and PUBLIC_QUERY_PARAMS (home absent). The old observer expected q to survive on home, contrary to existing canonical policy. Correct control asserts the existing301 cleanup, then submits q to the form catalog action and verifies the actual catalog request retains q. No application assertion relaxed for the SITE04 text defect.\n')
path=Q/'test_site04_candidate.py';t=path.read_text();t=t.replace("_,p,catalog=self.page(lang,'qa & chess')", "response,p,catalog=self.page(lang,'qa & chess')\n                self.assertTrue(response.redirect_chain);self.assertEqual(response.redirect_chain[0][1],301)\n                self.assertNotIn('q',response.wsgi_request.GET)\n                submitted=self.client.get(catalog,{'q':'qa & chess'},follow=True)\n                self.assertEqual(submitted.status_code,200);self.assertEqual(submitted.wsgi_request.GET.get('q'),'qa & chess')")
t=t.replace("self.assertEqual(p.input['value'],'qa & chess')","self.assertEqual(p.input['value'],'')");path.write_text(t)
runner=(O/'run_stage_tests.py').read_text().replace("+'_r1'","+'_r3'");(Q/'run_stage_tests_r3.py').write_text(runner)
subprocess.run(['python3',str(Q/'run_stage_tests_r3.py'),'04','red','test_site04_candidate'],check=True)
