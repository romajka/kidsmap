import json,hashlib,subprocess,socket
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/module09-pc-close-r1';P=R/'docs/qa/social-qa11-fix-2026-10-18-pc-r1';O=R/'docs/qa/module09-close-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir();(O/'png').mkdir()
sources=json.loads((P/'source-final.json').read_text())['sources'];assert len(sources)==1025 and all(sha(R/p)==h for p,h in sources.items())
e=json.loads((P/'source-entry.json').read_text());prior=e['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};assert len(prior)==19 and all(all(sha(O.parent/n/p)==h for p,h in fs.items()) for n,fs in prior.items())
pg=json.loads(subprocess.check_output(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(subprocess.check_output(['docker','network','inspect','m09full-r1-net']))[0];safety={'pg_running':pg['State']['Running'],'own_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']),'no_pg_published_port':not any(pg['NetworkSettings']['Ports'].values()),'internal_network':net['Internal']};assert all(safety.values())
with socket.socket() as s:s.bind(('127.0.0.1',33430))
g=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert all(g[k]==e['git'][k] for k in ['head','branch','index_tree','task33_ref','staged'])
entry={'sources':sources,'shared_mo':e['shared_mo'],'prior_packages':prior,'git':g,'cbmignore':sha(R/'.cbmignore'),'guide_sha256':sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),'containers':subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safety,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
base=json.loads((R/'docs/qa/module09-full-2026-10-17-pc-r1/source-final.json').read_text())['sources'];changed=[p for p,h in base.items() if sources.get(p)!=h];added=[p for p in sources if p not in base]
assert set(changed)=={'src/catalog/controllers/workflow_notifications.py','src/catalog/templates/catalog/typed_reviews.html','src/catalog/templates/pages/account_notifications.html','static/css/site.css'} and added==['src/catalog/testcases/test_social_qa10_notification_login.py']
delta={'full_snapshot_sources':len(base),'current_sources':len(sources),'unchanged_original_sources':len(base)-len(changed),'changed_existing':changed,'added':added,'changes':'exact approved SOCIAL10 named-login decorators/new8method regression +SOCIAL11 inner div/CSS alias','full169_methods':'historical1024 only; not rerun or relabeled current1025'};(O/'acceptance-source-delta.json').write_text(json.dumps(delta,indent=2))
for n in ['qa_settings.py','runtime.py','proxy.py','browser_driver.py','playwright.json']:
 t=(R/'.tmp/social11-pc-fix-r1'/n).read_text().replace('social11-pc-fix-r1','module09-pc-close-r1').replace('test_m09s11_fix_r1','test_m09close_r1').replace('m09s11-fix-r1-app','m09close-r1-app').replace('s11-fix-r1','m09-close-r1')
 if n=='proxy.py':t=t.replace('33420','33430').replace('remote_port={33430:8000,33421:8001,33422:8002}[port]','remote_port=8000')
 (Q/n).write_text(t)
print(json.dumps({'source1025':True,'prior19':True,'source_delta':delta,'safety':safety,'containers':len(entry['containers'])}))
