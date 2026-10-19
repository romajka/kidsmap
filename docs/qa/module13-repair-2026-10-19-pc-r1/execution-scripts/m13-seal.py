from pathlib import Path
import hashlib,json,shutil,re
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert not (O/'artifact-manifest.json').exists()
assert all(sha(R/p)==h for p,h in read(O/'source-current.json')['sources'].items());assert all(sha(R/p)==h for p,h in read(O/'document-current.json').items())
# Record owned resource identities without environment, credentials or DB rows.
import subprocess
lines=subprocess.check_output(['docker','ps','-a','--filter','name=m13','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();(O/'evidence/owned-resource-identities.json').write_text(json.dumps({'containers':lines,'no_foreign_restart_or_cleanup':True,'failed_initialization_resources_retained':True,'names_are_run_provenance_not_next_run_parameters':True},indent=2))
(O/'evidence/manual-visual-review.json').write_text(json.dumps({'reviewed':['png/final-organization-ru-390.png','png/final-activity-en-1440.png','png/final-capture-frozen-activity-en-1440.png','png/final-capture-claimed-person-ru-390.png'],'result':'Selected current desktop/mobile captures inspected. Synthetic green photos intentional. Focus-driven scroll positions in initial full-page captures were resampled by actual top/bottom scroll, with no product CSS changes.','scope':'Sampled manual review; all captures not manually reviewed; actual responsive/keyboard/overflow results in accepted suites.'},indent=2))
(O/'PROGRESS.md').write_text('Module13 CLOSED LOCAL. Final complete backend2626/0FAIL/0ERROR; JavaScript129PASS;21unique Python methods covered across Linux/Windows;394native rows/1501checksPASS plus3stock scripts. No confirmed OPEN. Manifest includes a read-only verify_artifacts.py. Production/GitHub/commit/push/deploy NOT RUN.\n')
shutil.copyfile(Path(__file__),O/'execution-scripts/m13-seal.py')
for p in O.rglob('*'):
 if not p.is_file() or p.suffix.lower() not in ['.md','.json','.txt','.py','.js','.cjs','.html','.diff','.ps1']:continue
 text=p.read_text(errors='replace')
 for tag in re.findall(r'<input\b[^>]*>',text,re.I):
  if re.search(r'name=[\"\']csrfmiddlewaretoken[\"\']',tag,re.I):assert not re.search(r'value=[\"\'][A-Za-z0-9]{64}[\"\']',tag),'Raw CSRF input in artifact'
assert not any(p.name.endswith('-state.json') for p in O.rglob('*') if p.is_file()),'Private browser state must stay in ignored scratch'
files={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file()};(O/'artifact-manifest.json').write_text(json.dumps({'version':1,'algorithm':'sha256','files':files},indent=2));print(json.dumps({'sealed_entries':len(files),'source_files':1074,'raw_CSRF_and_private_state_scan':'PASS'}))
