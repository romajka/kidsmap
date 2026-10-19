import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa06-recheck-2026-10-18-pc-r1';O=Path(__file__).resolve().parent;Q=R/'.tmp/site06-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=json.loads((O/'source-entry.json').read_text());m=json.loads((P/'candidate-manifest.json').read_text());red=json.loads((O/'evidence/red-backend.json').read_text());baseline=json.loads((O/'evidence/browser-baseline.json').read_text())
assert red['exit']==1 and red['candidate_methods']==29 and len(red['failed_methods'])==21 and red['failure_observations']==106 and red['errors']==0
assert len(baseline['rows'])==36 and all(all(x['checks'].values()) for x in baseline['rows']) and not baseline['pageerrors']
assert all(sha(R/p)==h for p,h in entry['sources'].items())
for rel,item in m['files'].items():
 p=R/rel;assert (sha(p) if p.exists() else None)==item['before_sha256'],rel
 if p.exists():
  dest=O/'entry-source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
assert sha(P/'proposed.diff')==m['diff_sha256']
subprocess.run(['git','-C',str(R),'apply','--check',str(P/'proposed.diff')],check=True)
subprocess.run(['git','-C',str(R),'apply',str(P/'proposed.diff')],check=True)
for rel,item in m['files'].items():assert sha(R/rel)==item['candidate_sha256'],rel
sources={p:sha(R/p) for p in entry['sources']}
sources.update({p:sha(R/p) for p,v in m['files'].items() if v['before_sha256'] is None});assert len(sources)==1031
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
(O/'applied.json').write_text(json.dumps({'approved_plan':str(P.relative_to(R))+'/IMPLEMENTATION_PLAN.md','diff_sha256':m['diff_sha256'],'exact_candidate7':True,'source_count':len(sources),'files':{p:sha(R/p) for p in m['files']}},indent=2))
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-green'),'--compiler','native'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'green-locales.log').write_text(r.stdout+r.stderr);assert r.returncode==0
# Distinct migration-backed test DB, never reuse RED after TransactionTestCase flush.
cmd=['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1','-O','m09full_r1','test_m10s06_fix_r1_green'];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
(Q/'stage.json').write_text(json.dumps({'locales':'locales-green','test_db':'test_m10s06_fix_r1_green'}))
# Expand only owned fixture login; normal permissions still use the application.
p=Q/'qa_urls.py';s=p.read_text().replace("role in ['content','super']","role in ['content','super','proxyfooter','viewer','addonly','denied','volunteer']");p.write_text(s)
print(json.dumps({'applied_exact_seven_files':True,'source_count':1031,'current_root_green_locales_built':True,'fresh_green_test_db':True}))
