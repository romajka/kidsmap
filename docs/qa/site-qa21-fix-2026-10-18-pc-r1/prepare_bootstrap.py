from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site21-pc-fix-r1';P=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1'
source=(P/'bootstrap.py').read_text().replace('site21-pc-plan-r1','site21-pc-fix-r1').replace('site-qa21-recheck-2026-10-18-pc-r1','site-qa21-fix-2026-10-18-pc-r1').replace('m10s21_plan_r1','m10s21_fix_r1').replace('m10s21-plan-r1','m10s21-fix-r1').replace('33550','33560').replace('locales-plan','locales-current')
source=source.replace("F=R/'docs/qa/site-qa19-fix-2026-10-18-pc-r1'","F=R/'docs/qa/site-qa21-recheck-2026-10-18-pc-r1'")
source=source.replace('len(fm)==221','len(fm)==67').replace('len(prior)==31','len(prior)==32').replace('==6166','==6234').replace("'prior_packages':31","'prior_packages':32").replace("'prior_files':6166","'prior_files':6234")
source+='''\n(O/'authorization.json').write_text(json.dumps({'human_request':'давльеш','authorization_context':'Continuation reply to concrete one-file PLAN21 apply question; accepted as proceed with that exact scope','application_implementation_authorized':True,'approved_plan':'docs/qa/site-qa21-recheck-2026-10-18-pc-r1/IMPLEMENTATION_PLAN.md','plan_sha256':sha(F/'IMPLEMENTATION_PLAN.md'),'approved_files':list(read(F/'candidate-manifest.json')['files']),'no_other_app_fixes_commit_push_deploy_production':True},ensure_ascii=False,indent=2))\n'''
assert "len(fm)==67" in source and "len(prior)==32" in source and "==6234" in source and "F=R/'docs/qa/site-qa21-recheck" in source
(Q/'bootstrap.py').write_text(source)
