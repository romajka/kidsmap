"""Build the separately authorized ACCEPT07 harness after scoped fix completion."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent;R=H.parents[2];F=R/'docs/qa/module07-full-2026-10-15-r1';OLD=R/'docs/qa/module07-2026-10-10-r1'
assert json.loads((H/'verification.json').read_text())['decision']=='ACCESS-QA-05 SCOPED LOCAL PASS'
F.mkdir()
for name in ['capture.py','settings.py','launch.py','runtime.py','drive.py','browser_run.py','run_record.py']:
 s=(H/name).read_text().replace(H.name,F.name).replace('accessqa05fixr1','module07fullr1').replace('access_qa05_fix_r1','module07_full_r1').replace('APPROVED IMPLEMENT ACCESS-QA-05; user одобряю; exact twoPO fourentry plan','ACCEPT-07 AUDIT ONLY; all approved repairs completed; no new application fixes')
 if name=='runtime.py':
  a=s.index(" from django.contrib.auth import get_user_model",s.index("if mode=='prepare':"));b=s.index("elif mode=='serve'",a)
  s=s[:a]+" STATE=SCRATCH\n exec(compile((HERE/'seed.py').read_text(),str(HERE/'seed.py'),'exec'),globals())\n"+s[b:]
  a=s.index("elif mode=='mailproof':");s=s[:a]+"elif mode=='test-full':\n exec(compile((HERE/'full_tests.py').read_text(),str(HERE/'full_tests.py'),'exec'),globals())\nelse:raise SystemExit('Unknown mode')\n"
 if name=='settings.py':s=s.replace('SIMULATED-QA05','SIMULATED-QA07')+"\nTASK33_R1_WRITE_MODE='all' # SIMULATED writes on own disposable DB only\nEMAIL_BACKEND='qa_mail.EmailBackend'\n"
 (F/name).write_text(s)
paths=sorted(str(p.relative_to(R))for top in ('src','static','templates','locale')for p in(R/top).rglob('*')if p.is_file()and p.suffix in('.py','.html','.css','.js','.po')and '__pycache__'not in p.parts)
(F/'source-paths.json').write_text(json.dumps(paths,indent=2))
s=(OLD/'seed.py').read_text();s=s.replace("sys.argv=['run.py','qa-seed'];from run import *","STATE=SCRATCH\n(STATE/'assets').mkdir(exist_ok=True)")
s=s.replace("password=(STATE/'credential').read_text()","password=json.loads((STATE/'credentials.json').read_text())['login_password']")
s=s[:s.index('# Existing test policy reused')]+"print('Prepared18synthetic roles,8places,1organization,2specialists,6private docs; initial fixtures only')\n"
s=s.replace("username='qa07_'+role","username='qa07_'+role") # fixture identifiers remain fictional
(F/'seed.py').write_text(s)
# Keep actual local filebased letters and a private structured copy for native flows.
s=(OLD/'qa_mail.py').read_text().replace('from django.core.mail.backends.locmem import EmailBackend as LocMem','from django.core.mail.backends.filebased import EmailBackend as FileBased').replace('class EmailBackend(LocMem):','class EmailBackend(FileBased):');(F/'qa_mail.py').write_text(s)
(F/'qa_evidence.py').write_bytes((OLD/'qa_evidence.py').read_bytes())
s=(H/'qa_urls.py').read_text();a=s.index('def fixtures(request):');s=s[:a]+'''def fixtures(request):
 if not allowed(request):return JsonResponse({},status=403)
 data=json.loads((HERE/'fixtures.json').read_text());data['password']=json.loads((settings.QA_ROOT/'credentials.json').read_text())['login_password'];return JsonResponse(data)
from qa_evidence import mail,state
urlpatterns=[path('qa/source/',source),path('qa/fixtures/',fixtures),path('qa/mail/',mail),path('qa/state/',state)]+application
''';(F/'qa_urls.py').write_text(s)
labels=['auth_flow','auth_access','test_email_verification_consumption','test_google_auth','test_account_deletion','test_task33_permissions','test_task33_ownership','test_organization_invitation_transport','test_volunteer_admin','test_volunteer_dashboard','test_task33_specialist_privacy','test_task33_specialist_security_review','test_task33_specialist_transfer','test_access_qa02_invitation_decline','test_network_grant_ui','owner.TestOwnerTeamAndReviewModeration']
(F/'full-test-selectors.json').write_text(json.dumps(['catalog.testcases.'+x for x in labels],indent=2));(F/'retained-target-tests.json').write_bytes((H/'target-tests.json').read_bytes())
(F/'full_tests.py').write_text('''import unittest
from django.test.runner import DiscoverRunner
settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend';settings.CSRF_COOKIE_NAME='csrftoken'
settings.MEDIA_ROOT=SCRATCH/'unit-media';settings.PRIVATE_MEDIA_ROOT=SCRATCH/'unit-private-media'
labels=json.loads((HERE/'full-test-selectors.json').read_text());retained=set(json.loads((HERE/'retained-target-tests.json').read_text()))
def flatten(suite):
 for test in suite:
  if isinstance(test,unittest.TestSuite):yield from flatten(test)
  else:yield test
class ModuleRunner(DiscoverRunner):
 def build_suite(self,test_labels=None,**kwargs):
  suite=super().build_suite(test_labels,**kwargs);unique={t.id():t for t in flatten(suite)};kept=list(unique.values())
  (HERE/'test-inventory.json').write_text(json.dumps({'collected_unique':len(unique),'overlap_with_prior_target_methods':sorted(retained & unique.keys()),'excluded_methods':[],'executed_methods':[t.id()for t in kept]},indent=2));return unittest.TestSuite(kept)
failures=ModuleRunner(interactive=False,verbosity=1).run_tests(labels);sys.exit(bool(failures))
''')
print(json.dumps({'new_accept_run':str(F),'source_paths':len(paths),'suites':len(labels),'overlap_target_methods':7,'application_changes':[]}))
