import subprocess,json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';labels=['catalog.testcases.'+p.stem for p in sorted((R/'src/catalog/testcases').glob('test_site_qa*.py'))]+['catalog.testcases.public.TestPublicPagesSmoke']
(O/'evidence/final-backend-labels.json').write_text(json.dumps(labels,indent=2));r=subprocess.run(['python3',str(O/'run_stage_tests.py'),'99','green',*labels]);raise SystemExit(r.returncode)
