import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module11-repair-2026-10-18-pc-r1';names=[p.stem for p in sorted((R/'src/catalog/testcases').glob('test_site_qa*.py'))]+[
'test_module11_seo','test_module11_routes','test_module11_identity',
'test_localized_place_urls','test_localized_place_seo','test_seo_indexability','test_seo_landing_visibility','test_judo_seo_landing','test_seo_audit_system',
'test_task33_localization','test_task33_public_details','test_task33_event_queries','test_task33_event_public','test_task33_event_schema.EventSchemaTests',
'test_task33_specialist_domain','test_task33_specialist_privacy','test_task33_specialist_screens','test_task33_specialist_screens_security','test_task33_specialist_security_review',
'test_specialist_entry_admin','test_specialist_entry_locations','test_specialist_identity_date_label',
'public.TestPublicPagesSmoke','public.PublicLanguageConsistencyTests','test_place_json_and_pricing_modes.PlaceSchemaOrgSeoTests']
labels=['catalog.testcases.'+n for n in names];assert len(labels)==len(set(labels));(O/'evidence/final-labels.json').write_text(json.dumps(labels,indent=2));raise SystemExit(subprocess.run(['python3',str(R/'.tmp/m11-tests.py'),'acceptance','green','r1',*labels]).returncode)
