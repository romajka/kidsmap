from pathlib import Path
import hashlib,json,shutil
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
shutil.copyfile(Q/'discovery-baseline.json',O/'evidence/discovery-baseline.json')
test='''"""The CI no-label command must execute the complete current domain corpus."""
import importlib
import pkgutil
from django.test import SimpleTestCase
from config.test_runner import KidsMapTestRunner
from catalog import testcases

def ids(suite):
    for test in suite:
        if hasattr(test, '_tests'):
            yield from ids(test)
        else:
            yield test.id()

class FullDiscoveryContractTests(SimpleTestCase):
    def runner(self):
        return KidsMapTestRunner(verbosity=0, interactive=False)
    def test_no_label_matches_every_domain_module(self):
        modules=['catalog.testcases.'+m.name for m in pkgutil.iter_modules(testcases.__path__) if not m.ispkg]
        expected=set(ids(self.runner().build_suite(modules)))
        actual=set(ids(self.runner().build_suite([])))
        self.assertGreater(len(expected),2500)
        self.assertEqual(actual,expected)
    def test_full_contains_legacy_and_new_modules_once(self):
        actual=list(ids(self.runner().build_suite([])))
        self.assertEqual(len(actual),len(set(actual)))
        for module in ['catalog.testcases.place_readiness','catalog.testcases.phone_reveal','catalog.testcases.test_module13_event_projection']:
            self.assertTrue(any(i.startswith(module+'.') for i in actual), module)
    def test_explicit_label_remains_scoped(self):
        label='catalog.testcases.test_module13_event_projection'
        actual=list(ids(self.runner().build_suite([label])))
        self.assertEqual(len(actual),3)
        self.assertTrue(all(i.startswith(label+'.') for i in actual))
    def test_explicit_pattern_is_honored(self):
        runner=KidsMapTestRunner(verbosity=0, interactive=False,pattern='test_module13_event_projection.py')
        actual=list(ids(runner.build_suite([])))
        self.assertEqual(len(actual),3)
        self.assertTrue(all(i.startswith('catalog.testcases.test_module13_event_projection.') for i in actual))
'''
p=R/'src/catalog/testcases/test_module13_discovery.py';assert not p.exists();p.write_text(test)
d=json.loads((Q/'expected-source.json').read_text());d['sources'][p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(d,indent=2))
print('Discovery regression added; implementation still entry bytes.')
