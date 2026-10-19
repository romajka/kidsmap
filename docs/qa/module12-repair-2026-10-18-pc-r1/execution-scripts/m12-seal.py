import json,hashlib,re,shutil,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';Q=R/'.tmp/m12-full-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert not (O/'artifact-manifest.json').exists()
current=read(O/'source-current.json')['sources'];assert current==read(O/'evidence/final-backend-source.json')['sources'];assert all(sha(R/p)==h for p,h in current.items());assert all(sha(R/p)==h for p,h in read(O/'document-current.json').items())
with urllib.request.urlopen('http://127.0.0.1:33780/qa/m12/state/',timeout=10) as response:state=json.loads(response.read())
assert state['place_state']['status']=='published' and state['place_state']['is_active'];assert read(Q/'simulation.json')=={'report':'disabled','storage':'healthy'}
(O/'evidence/fixture-final-summary.json').write_text(json.dumps({'own_fixture_published':True,'synthetic_public_names_present':all(v.strip().startswith('M12') for v in state['place_state']['names'].values()),'original_contacts_restored':state['place_state']['website']==state['place_state']['instagram']=='','public_flags':state['flags'],'media_file_count':len(state['media']),'raw_event_count':state['events_total'],'aggregate_summary':state['metrics'],'simulation_reset_to_disabled_provider_healthy_storage':True,'source':'own loopback read-only aggregate helper; no user rows or identity hashes exported'},indent=2))
shutil.copyfile(Path(__file__),O/'execution-scripts/m12-seal.py')
for path in O.rglob('*'):
 if not path.is_file() or path.suffix.lower() not in ['.md','.json','.txt','.py','.js','.cjs','.html','.diff','.ps1']:continue
 text=path.read_text(errors='replace')
 for tag in re.findall(r'<input\b[^>]*>',text,re.I):
  if re.search(r'name=[\"\']csrfmiddlewaretoken[\"\']',tag,re.I):assert not re.search(r'value=[\"\'][A-Za-z0-9]{64}[\"\']',tag),'Raw CSRF input in artifact'
files={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file()};(O/'artifact-manifest.json').write_text(json.dumps({'version':1,'algorithm':'sha256','files':files},indent=2));print(json.dumps({'sealed_entries':len(files),'source_files':len(current),'raw_CSRF_input_scan':'PASS'}))
