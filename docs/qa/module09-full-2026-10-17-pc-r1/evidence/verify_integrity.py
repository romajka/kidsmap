import json,hashlib,subprocess
from pathlib import Path
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent;R=Q.parents[1];O=R/'docs/qa/module09-full-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'source-entry.json').read_text());safe=json.loads((O/'safety-entry.json').read_text());g=json.loads((Q/'git-final.json').read_text(encoding='utf-8-sig'));checks={}
checks['source1024_unchanged']=len(e['sources'])==1024 and all(sha(R/p)==h for p,h in e['sources'].items())
checks['shared_mo_unchanged']=all(sha(R/p)==h for p,h in safe['shared_mo'].items())
checks['cbmignore_unchanged']=sha(R/'.cbmignore')==e['cbmignore']
checks['refs_index_and_staged_unchanged']=all(g[k]==safe['git'][k] for k in ['head','branch','index_tree','task33_ref','staged']) and not g['staged']
prefix='docs/qa/module09-full-2026-10-17-pc-r1/'
checks['all_other_git_status_entries_unchanged']=set(x for x in g['status'] if not x[3:].startswith(prefix))==set(x for x in safe['git']['status'] if not x[3:].startswith(prefix))
checks['active_run_none']=[x for x in (R/'docs/task33/implementation-status.md').read_text().splitlines() if x.startswith('active_run:')]==['active_run: NONE']
packages={n:all(sha(O.parent/n/p)==h for p,h in fs.items()) for n,fs in e['prior_packages'].items()};checks['prior14_packages_unchanged']=len(packages)==14 and all(packages.values())
append=json.loads((O/'guide-append.json').read_text());guide=(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_bytes();checks['guide_old_bytes_preserved']=hashlib.sha256(guide[:-append['appended_utf8_bytes']]).hexdigest()==e['guide_sha256'] and hashlib.sha256(guide).hexdigest()==append['after_sha256']
current=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();before={x.split()[0]:x.split()[1:] for x in e['containers']};after={x.split()[0]:x.split()[1:] for x in current}
checks['entry47_container_identities_preserved']=len(before)==47 and all(i in after and after[i][0]==s[0] for i,s in before.items())
deltas=[{'id':i,'name':s[0],'before':s[1],'after':after.get(i,[None,None])[1],'cause':'UNKNOWN; no agent stop/restart of entry container'} for i,s in before.items() if i not in after or after[i][1]!=s[1]]
checks['fresh_runtime_source_locale_gate']=json.loads((Q/'runtime-info.json').read_text())['source1024'] and json.loads((Q/'runtime-info.json').read_text())['testing']
checks['backend_full_and_targeted_exits_retained']=(Q/'tests.exit').read_text().strip()=='1' and (Q/'socket-tests.exit').read_text().strip()=='0'
checks['readback_v2_verified']=all(r['passed'] for r in json.loads((Q/'extra-readback-v2.json').read_text())['rows']) and json.loads((Q/'extra-readback-v2.json').read_text())['no_duplicate_outbox']
checks['native_png1402_manifest']=len(json.loads((O/'png-manifest.json').read_text()))==1402 and all(sha(O/p)==v['sha256'] for p,v in json.loads((O/'png-manifest.json').read_text()).items())
(O/'git-final.json').write_text(json.dumps(g,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':e['sources']},indent=2));(O/'container-preservation.json').write_text(json.dumps({'entry_count':len(before),'current_count':len(after),'entry_identity_preserved':checks['entry47_container_identities_preserved'],'state_changes':deltas,'owned_added_names':[v[0] for k,v in after.items() if k not in before]},indent=2))
# File inventory includes final reports/evidence/native pixels, excludes its own digest and verification.
manifest={p.relative_to(O).as_posix():{'sha256':sha(p),'bytes':p.stat().st_size} for p in O.rglob('*') if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));checks['artifact_manifest_valid']=all(sha(O/p)==d['sha256'] for p,d in manifest.items())
v={'utc':datetime.now(timezone.utc).isoformat(),'audit_execution':'COMPLETE','module_acceptance':'FAIL / OPEN','application_changes':False,'source_files':1024,'backend_unique_final_passed':169,'screens':810,'png_files':1402,'raw_observations':4235,'findings':['SOCIAL-QA-10 P2 OPEN (alias ADJ-ANONYMOUS-LOGIN-08)','SOCIAL-QA-11 P3 OPEN'],'checks':checks,'preservation_pass':all(checks.values()),'prior_packages':packages,'container_state_changes':deltas,'artifact_files_excluding_manifest_verification':len(manifest),'limits_file':'REPORT.md','initial_failure_ledger':'HARNESS_AND_ENVIRONMENT.md','production':'NOT RUN','global_suite':'NOT RUN'}
(O/'verification.json').write_text(json.dumps(v,indent=2));print(json.dumps({'preservation_pass':all(checks.values()),'failed_checks':[k for k,v in checks.items() if not v],'prior_packages':len(packages),'entry_containers':len(before),'state_changes':deltas,'artifacts':len(manifest),'audit':'COMPLETE','acceptance':'FAIL / OPEN'}));assert all(checks.values()),checks
