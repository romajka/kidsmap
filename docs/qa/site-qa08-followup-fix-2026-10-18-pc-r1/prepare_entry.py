from pathlib import Path
import hashlib,json
R=Path('/mnt/c/kidsmap');F=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1';O=R/'docs/qa/site-qa08-followup-fix-2026-10-18-pc-r1';Q=R/'.tmp/site08-pc-followup-r1'
assert not Q.exists() and not O.exists();Q.mkdir()
def adapt(s):
 for a,b in [('site08-pc-fix-r1','site08-pc-followup-r1'),('site-qa08-fix-2026-10-18-pc-r1','site-qa08-followup-fix-2026-10-18-pc-r1'),('m10s08_fix_r1','m10s08_followup_r1'),('m10s08-fix-r1','m10s08-followup-r1'),('33580','33590')]:s=s.replace(a,b)
 return s
s=adapt((F/'bootstrap.py').read_text())
s=s.replace("F=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1'", "F=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1'")
s=s.replace('==1032','==1033').replace('==226','==363').replace('==34','==35').replace('==6763','==7127').replace("'source_count':1032","'source_count':1033").replace("'prior_packages':34","'prior_packages':35").replace("'prior_files':6763","'prior_files':7127")
s=s.replace("rel='src/catalog/templates/admin/catalog/shared_settings_change_form.html'", "rel='static/admin/css/pages/kidsmap_settings_forms.css'")
start=s.index("for name in ['qa_settings.py'");end=s.index("(Q/'stage.json')",start)
s=s[:start]+'''for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:
 content=(R/'.tmp/site08-pc-fix-r1'/name).read_text()
 for a,b in [('site08-pc-fix-r1','site08-pc-followup-r1'),('site-qa08-fix-2026-10-18-pc-r1','site-qa08-followup-fix-2026-10-18-pc-r1'),('m10s08_fix_r1','m10s08_followup_r1'),('m10s08-fix-r1','m10s08-followup-r1'),('33580','33590')]:content=content.replace(a,b)
 (Q/name).write_text(content)
'''+s[end:]
s=s[:s.index("(O/'authorization.json')")]+'''(O/'authorization.json').write_text(json.dumps({'human_request':'дальше','authorization_context':'Direct continuation approving the exact one-CSS SITE08 followup after prior final application question','approved_plan':'docs/qa/site-qa08-fix-2026-10-18-pc-r1/followup/IMPLEMENTATION_PLAN.md','plan_sha256':sha(F/'followup/IMPLEMENTATION_PLAN.md'),'approved_diff_sha256':sha(F/'followup/proposed.diff'),'approved_files':['static/admin/css/pages/kidsmap_settings_forms.css'],'application_implementation_authorized':True,'no_other_fixes_commit_push_deploy_production':True},ensure_ascii=False,indent=2))
'''
(Q/'bootstrap.py').write_text(s)
# Preparation only; bootstrap executes as a separate observable command.
(Q/'adapt.py').write_text('')
