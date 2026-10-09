from pathlib import Path
import hashlib,json,subprocess,urllib.request
R=Path('/home/ramin/kidsmap');S=Path(__file__).parent;x=json.loads((S/'runtime-source.json').read_text());before=json.loads((S/'preservation-before.json').read_text());owned={'docs/qa/place-acceptance-contract-2026-10-09-review.md'}
changed=[p for p,h in before.items() if p not in owned and (not(R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h)]
source_changed=[p for p,h in x['source_files'].items() if not(R/p).exists() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
version=json.load(urllib.request.urlopen('http://localhost:8792/qa/acceptance-version/'))
y={'head_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==x['head'],'branch_unchanged':subprocess.check_output(['git','branch','--show-current'],text=True).strip()==x['branch'],'preexisting_files':len(before),'changed_preexisting_excluding_owned_report':changed,'application_files':len(x['source_files']),'source_changed':source_changed,'source_digest':x['source_digest'],'runtime_version':version,'runtime_matches_snapshot':version['source_digest']==x['source_digest'],'active_run_current':[l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')][0]}
(S/'preservation-final.json').write_text(json.dumps(y,indent=2));print(json.dumps(y))
