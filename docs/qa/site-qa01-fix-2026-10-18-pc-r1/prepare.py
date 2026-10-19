import hashlib, json, socket, subprocess
from pathlib import Path

R = Path('/mnt/c/kidsmap')
O = R/'docs/qa/site-qa01-fix-2026-10-18-pc-r1'
Q = R/'.tmp/site01-pc-fix-r1'
P = R/'docs/qa/site-qa01-recheck-2026-10-18-pc-r1'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
run = lambda args: subprocess.check_output(args, text=True).strip()
assert not Q.exists()
Q.mkdir(); (O/'evidence').mkdir(); (O/'png').mkdir()
baseline = json.loads((P/'source-entry.json').read_text())
assert len(baseline['sources']) == 1027
assert all(sha(R/p) == h for p,h in baseline['sources'].items())
m = json.loads((P/'candidate-manifest.json').read_text())
for p,d in m['files'].items():
    assert (sha(R/p) if (R/p).exists() else None) == d['before_sha256']
    assert sha(P/'candidate'/p) == d['candidate_sha256']
assert sha(P/'proposed.diff') == m['diff_sha256']
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
prior = baseline['prior_packages']
for pkg in [P,R/'docs/qa/site-qa01-resume-2026-10-18-pc-r1']:
    prior[pkg.name] = {p.relative_to(pkg).as_posix():sha(p) for p in pkg.rglob('*') if p.is_file()}
assert all(sha(R/'docs/qa'/pkg/p)==h for pkg,files in prior.items() for p,h in files.items())
pg = json.loads(run(['docker','inspect','m09full-r1-pg']))[0]
net = json.loads(run(['docker','network','inspect','m09full-r1-net']))[0]
safe = {'pg_running':pg['State']['Running'], 'owned_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']), 'internal_network':net['Internal'], 'no_published_pg_ports':not any(pg['NetworkSettings']['Ports'].values())}
assert all(safe.values())
with socket.socket() as s: s.bind(('127.0.0.1',33480))
dbs = run(['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-At','-c',"BEGIN READ ONLY; SET LOCAL statement_timeout='5s'; SELECT count(*) FROM pg_database WHERE datname IN ('m10s01_fix_r1','test_m10s01_fix_r1'); COMMIT;"])
assert '0' in dbs.splitlines()
git = lambda *a:run(['git','-C',str(R),*a])
entry = {'sources':baseline['sources'],'prior_packages':prior,'shared_mo':baseline['shared_mo'],'cbmignore':sha(R/'.cbmignore'),
 'git':{'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'index_tree':git('rev-parse','HEAD^{tree}'),'index_sha256':sha(R/'.git/index'),'task33_ref':git('rev-parse','task33-progress'),'staged':git('diff','--cached','--name-only')},
 'containers':run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines(),
 'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
assert not entry['git']['staged']
(O/'source-entry.json').write_text(json.dumps(entry,indent=2))
(O/'safety-entry.json').write_text(json.dumps(safe,indent=2))
(Q/'expected-source.json').write_text(json.dumps({'sources':baseline['sources']},indent=2))
old=R/'.tmp/site01-pc-plan-r1'
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json']:
    s=(old/name).read_text().replace('site01-pc-plan-r1','site01-pc-fix-r1').replace('m10s01_plan_r1','m10s01_fix_r1').replace('m10s01-plan-r1','m10s01-fix-r1').replace('33470','33480')
    (Q/name).write_text(s)
(Q/'test_site01_candidate.py').write_bytes((P/'candidate/src/catalog/testcases/test_site_qa01_media_permissions.py').read_bytes())
subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','m10s01_fix_r1'],check=True)
image=run(['docker','inspect','m10s01-plan-r1-app','--format','{{.Config.Image}}'])
subprocess.run(['docker','run','-d','--name','m10s01-fix-r1-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp:rw,size=64m','--mount',f'type=bind,src={R},dst={R},readonly','--mount',f'type=bind,src={Q},dst={Q}','--entrypoint','sleep',image,'infinity'],check=True,capture_output=True)
(O/'authorization.json').write_text(json.dumps({'user_approval':'дальше; начни 10ый мобудь','scope':list(m['files']),'policy_plan':str(P.relative_to(R)/'IMPLEMENTATION_PLAN.md'),'mode':'APPROVED IMPLEMENT','app':'m10s01-fix-r1-app','normal_db':'m10s01_fix_r1','test_db':'test_m10s01_fix_r1','loopback':33480},ensure_ascii=False,indent=2))
print(json.dumps({'source1027_match':True,'prior_packages':len(prior),'safe':safe,'own_app':'m10s01-fix-r1-app','new_normal_and_test_db':True}))
