from pathlib import Path
import json
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa22-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-plan-r1'
(O/'test_site22_candidate-v1.py').write_bytes((O/'test_site22_candidate.py').read_bytes())
(O/'evidence/red-backend-v1.json').write_bytes((O/'evidence/red-backend.json').read_bytes());(Q/'red-tests-v1.log').write_bytes((Q/'red-tests.log').read_bytes())
(O/'evidence/QA-fixture-correction.json').write_text(json.dumps({'initial_unexpected_failure':'catalog control GET302 before form; helper incorrectly reused SiteSettings pk for distinct CatalogContentSettings table','correction':'Use actual CatalogContentSettings fixture pk; keep destination and persistence assertions unchanged','initial_evidence_preserved':True,'initial_application_changes':0},indent=2))
