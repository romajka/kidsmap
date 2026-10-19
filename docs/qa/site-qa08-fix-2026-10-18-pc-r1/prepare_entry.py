from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site08-pc-fix-r1';O=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1'
assert not Q.exists() and not O.exists();Q.mkdir()
s=(P/'bootstrap.py').read_text().replace("F=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'","F=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1'")
for a,b in [('site08-pc-plan-r1','site08-pc-fix-r1'),('m10s08_plan_r1','m10s08_fix_r1'),('m10s08-plan-r1','m10s08-fix-r1'),('33570','33580'),('len(fm)==301','len(fm)==226'),('len(prior)==33','len(prior)==34'),('==6536','==6763'),("'prior_packages':33","'prior_packages':34"),("'prior_files':6536","'prior_files':6763")]:s=s.replace(a,b)
s=s.replace("O=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1'","O=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1'")
start=s.index("for name in ['qa_settings.py'");end=s.index("(Q/'stage.json')",start)
s=s[:start]+'''for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:
 content=(R/'.tmp/site08-pc-plan-r1'/name).read_text()
 for a,b in [('site08-pc-plan-r1','site08-pc-fix-r1'),('site-qa08-recheck-2026-10-18-pc-r1','site-qa08-fix-2026-10-18-pc-r1'),('m10s08_plan_r1','m10s08_fix_r1'),('m10s08-plan-r1','m10s08-fix-r1'),('33570','33580')]:content=content.replace(a,b)
 (Q/name).write_text(content)
'''+s[end:]
s+='''\n(O/'authorization.json').write_text(json.dumps({'human_request':'дальше','authorization_context':'Direct continuation response to exact SITE08 two-file PLAN apply question','approved_plan':'docs/qa/site-qa08-recheck-2026-10-18-pc-r1/IMPLEMENTATION_PLAN.md','plan_sha256':sha(F/'IMPLEMENTATION_PLAN.md'),'approved_files':list(read(F/'candidate-manifest.json')['files']),'application_implementation_authorized':True,'no_other_fixes_commit_push_deploy_production':True},ensure_ascii=False,indent=2))\n'''
assert 'len(fm)==226' in s and '==6763' in s and "F=R/'docs/qa/site-qa08-recheck" in s
(Q/'bootstrap.py').write_text(s);print('Fresh fix bootstrap prepared.')
