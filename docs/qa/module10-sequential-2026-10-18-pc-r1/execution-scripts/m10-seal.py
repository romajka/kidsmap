import hashlib,json,re,shutil
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
assert not (O/'artifact-manifest.json').exists();v=read(O/'verification.json');assert v['final_backend_methods']==238 and v['final_public_checks']==1064 and v['remaining_OPEN']==0
for path,h in read(Q/'expected-source.json')['sources'].items():assert sha(R/path)==h
for path,h in read(O/'document-current.json').items():assert sha(R/path)==h
assert sha(R/'.git/index')==read(O/'source-entry.json')['git']['index_sha256']
(O/'stages/SITE99/README.md').write_text('# Final regression checkpoint\n\n99 is the execution runner checkpoint for the final238method acceptance, not another finding or module. All18siteQA test modules and the unchanged public smoke class ran once on final source, fresh own database test_m10seq_99_green_r1, isolated cache/media/private-media/email and disabled external integrations. Structured result duplicated at ../../evidence/final-backend.json. Full raw test log remains ignored scratch and is not copied here.\n')
(O/'execution-scripts/README.md').write_text('# Execution support\n\nRoot executed these local scripts; no independent agent was used. Current-source reference is source-final.json and own scratch runtime is .tmp/m10-seq-r1/runtime.py. Stage plans/diffs/RED/GREEN evidence are retained, including initial failures and observer corrections. Avoid replay against foreign or production state: fixture mutations are real native UI actions on owned m10seq_r1 only.\n\nFinal backend command: python3 .tmp/m10-final-tests.py → run_stage_tests.py 99 green plus exact labels in evidence/final-backend-labels.json. Test runner validates fresh own DB name and clears environment before Django setup. Native command: python3 docs/qa/module10-sequential-2026-10-18-pc-r1/browser_driver.py <script-name>, Chromium session m10-seq-r1. Final accepted browser matrix is composed transparently from raw final-public and native OFF-precondition retired-r2 runs; original ON200 expectation failures and initial script compilation error are retained.\n\nPreservation command: python3 .tmp/m10-final-preservation.py validates source, prior41packages/8514files, Git/index, sharedMO, foreign container identity/state and restored original fixture values. Final artifact verification: PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/module10-sequential-2026-10-18-pc-r1/verify_artifacts.py. Verification reads only.\n')
for src in [R/'.tmp/m10-compose-final-browser.py',Path(__file__)]:shutil.copyfile(src,O/'execution-scripts'/src.name)
leaks=[]
for p in O.rglob('*'):
 if p.is_file() and p.suffix in {'.json','.txt','.log','.html','.md'}:
  text=p.read_text(errors='replace')
  if re.search(r'name=[\\]?"csrfmiddlewaretoken[\\]?"[^>]{0,80}value=[\\]?"[A-Za-z0-9]{64}[\\]?"',text):leaks.append(p.relative_to(O).as_posix())
assert not leaks,leaks
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file()};(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'sealed_files':len(manifest),'raw_HTML_CSRF_token_scan':'PASS','source_and_documents_current':True}))
