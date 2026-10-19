import subprocess,json
from pathlib import Path
Q=Path(__file__).resolve().parent
labels=['catalog.testcases.public.TestPublicPagesSmoke','catalog.testcases.public.PublicLanguageConsistencyTests','catalog.testcases.public.TestCatalogContentSettingsWiring','catalog.testcases.test_public_section_switches','catalog.testcases.events_feature','catalog.testcases.specialists.TestSpecialistsFeatureFlag','catalog.testcases.test_public_favorite_count','catalog.testcases.test_site_whatsapp','catalog.testcases.admin.TestAdminSidebarStructure.test_hidden_public_sections_remain_available_in_admin']
(Q/'test-labels.json').write_text(json.dumps(labels,indent=2));r=subprocess.run(['docker','exec','m10full-pc-r1-app','python',str(Q/'runtime.py'),'test']+labels,capture_output=True,text=True);(Q/'tests.log').write_text(r.stdout+r.stderr);(Q/'tests.exit').write_text(str(r.returncode)+'\n');print(json.dumps({'exit':r.returncode,'tail':(r.stdout+r.stderr)[-2000:]}))
