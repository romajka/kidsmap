from pathlib import Path
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1';O=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site08-pc-plan-r1'
assert not O.exists() and not Q.exists();Q.mkdir()
source=(F/'bootstrap.py').read_text().split("\n(O/'authorization.json')")[0]
source=source.replace("F=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1'","F=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'")
for a,b in [('site21-pc-fix-r1','site08-pc-plan-r1'),('m10s21_fix_r1','m10s08_plan_r1'),('m10s21-fix-r1','m10s08-plan-r1'),('33560','33570'),('len(fm)==67','len(fm)==301'),('len(prior)==32','len(prior)==33'),('==6234','==6536'),("'prior_packages':32","'prior_packages':33"),("'prior_files':6234","'prior_files':6536")]:source=source.replace(a,b)
source=source.replace("O=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'","O=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1'")
start=source.index("for name in ['qa_settings.py'");end=source.index("(Q/'stage.json')",start)
source=source[:start]+'''for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:
 content=(R/'.tmp/site21-pc-fix-r1'/name).read_text()
 for a,b in [('site21-pc-fix-r1','site08-pc-plan-r1'),('site-qa21-fix-2026-10-18-pc-r1','site-qa08-recheck-2026-10-18-pc-r1'),('m10s21_fix_r1','m10s08_plan_r1'),('m10s21-fix-r1','m10s08-plan-r1'),('33560','33570'),('site21_','site08_'),('qa/site21/','qa/site08/')]:content=content.replace(a,b)
 (Q/name).write_text(content)
'''+source[end:]
assert "F=R/'docs/qa/site-qa21-fix" in source and 'len(fm)==301' in source
(Q/'bootstrap.py').write_text(source)
print(str(Q/'bootstrap.py'))
