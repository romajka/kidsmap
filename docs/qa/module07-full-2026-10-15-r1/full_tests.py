import unittest
from config.test_runner import KidsMapTestRunner
settings.EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend';settings.CSRF_COOKIE_NAME='csrftoken'
settings.MEDIA_ROOT=SCRATCH/'unit-media';settings.PRIVATE_MEDIA_ROOT=SCRATCH/'unit-private-media'
labels=json.loads((HERE/'full-test-selectors.json').read_text());retained=set(json.loads((HERE/'retained-target-tests.json').read_text()))
def flatten(suite):
 for test in suite:
  if isinstance(test,unittest.TestSuite):yield from flatten(test)
  else:yield test
class ModuleRunner(KidsMapTestRunner):
 def build_suite(self,test_labels=None,**kwargs):
  suite=super().build_suite(test_labels,**kwargs);unique={t.id():t for t in flatten(suite)};kept=list(unique.values())
  (HERE/'test-inventory.json').write_text(json.dumps({'collected_unique':len(unique),'overlap_with_prior_target_methods':sorted(retained & unique.keys()),'excluded_methods':[],'executed_methods':[t.id()for t in kept]},indent=2));return unittest.TestSuite(kept)
failures=ModuleRunner(interactive=False,verbosity=1).run_tests(labels);sys.exit(bool(failures))
