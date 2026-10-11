"""AUDIT instrumentation only; original assertions and state-reset runner preserved."""
from pathlib import Path
import ast, hashlib, importlib, json, os, runpy, sys, time, traceback, unittest

OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
QA = OUT.parent
ROOT = QA.parents[2]
SCRATCH = ROOT / '.tmp/module13-20261011-r1/test-review'
OUT.mkdir(exist_ok=True)
SCRATCH.mkdir(parents=True, exist_ok=True)
mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
sys.argv = [str(QA/'run.py'), 'audit-bootstrap']
runpy.run_path(str(QA/'run.py'), run_name='__qa_bootstrap__')
from django.conf import settings
from django.test.utils import get_runner

# Exactly the parent's test profile; no assertion or contract overrides.
settings.LOCAL_ANALYTICS_STORAGE_ENABLED = False
settings.LOCALIZED_PLACE_URLS_ENABLED = False
settings.OWNER_ANALYTICS_ENABLED = False
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
settings.PUBLIC_BASE_URL = 'http://testserver'
settings.CSRF_COOKIE_NAME = 'csrftoken'
settings.MEDIA_ROOT = SCRATCH/'unit-media'
settings.PRIVATE_MEDIA_ROOT = SCRATCH/'unit-private-media'
assert settings.TESTING and os.environ['DJANGO_TESTING'] == '1'
assert settings.DATABASES['default']['NAME'] == 'module13'
assert settings.DATABASES['default']['TEST']['NAME'] == 'test_module13'
assert settings.DATABASES['default']['HOST'] == '127.0.0.1'
assert settings.DATABASES['default']['PORT'] == '55444'
assert 'locmem' in settings.CACHES['default']['BACKEND'].lower()
assert 'locmem' in settings.EMAIL_BACKEND.lower()
assert not settings.GOOGLE_APPLICATION_CREDENTIALS and not settings.GOOGLE_OAUTH_CLIENT_SECRET

def flatten(suite):
    for entry in suite:
        if isinstance(entry, unittest.TestSuite):
            yield from flatten(entry)
        else:
            yield entry

imports = {n.module for n in ast.walk(ast.parse((ROOT/'src/catalog/tests.py').read_text())) if isinstance(n, ast.ImportFrom)}
extras = ['catalog.testcases.'+p.stem for p in sorted((ROOT/'src/catalog/testcases').glob('*.py')) if not p.name.startswith('test_') and p.stem not in ('__init__','utils') and 'catalog.testcases.'+p.stem not in imports]
labels = ['catalog'] + extras
if mode == 'target':
    labels = json.loads((OUT/'target-labels.json').read_text())
base = get_runner(settings)
probe = base(verbosity=0, interactive=False, parallel=1)
discovered = list(flatten(probe.build_suite(labels)))
unique = {}
for case in discovered:
    unique.setdefault(case.id(), case)
snapshot = json.loads((QA/'snapshot.json').read_text())
inventory = {'mode': mode, 'labels': labels, 'raw_discovery_count': len(discovered), 'unique_count': len(unique), 'deduplicated_identical_ids': len(discovered)-len(unique), 'ids': list(unique), 'head': snapshot['head'], 'branch': snapshot['branch'], 'source_digest': snapshot['source_digest'], 'launcher_sha256': hashlib.sha256((QA/'run.py').read_bytes()).hexdigest(), 'profile': {'testing': True, 'database': 'test_module13', 'host': '127.0.0.1', 'port': 55444, 'cache': 'LocMem', 'email': 'LocMem', 'localized_place_urls': False, 'local_analytics': False, 'owner_analytics': False, 'external_network': 'blocked', 'media': str(settings.MEDIA_ROOT), 'private_media': str(settings.PRIVATE_MEDIA_ROOT)}}
(OUT/(mode+'-inventory.json')).write_text(json.dumps(inventory, indent=2), encoding='utf-8')
print('Discovered', len(discovered), 'unique', len(unique), 'extra non-prefixed modules', extras, flush=True)
observations = []
started = time.monotonic()

class AuditRunner(base):
    def build_suite(self, test_labels=None, **kwargs):
        return unittest.TestSuite(unique.values())

    def get_resultclass(self):
        parent = super().get_resultclass() or unittest.TextTestResult
        class AuditResult(parent):
            def record(self, test, status, error=None, reason=None):
                row = {'id': test.id(), 'status': status, 'elapsed_total_seconds': round(time.monotonic()-started, 3)}
                if error:
                    row['traceback'] = ''.join(traceback.format_exception(*error))
                if reason:
                    row['reason'] = reason
                observations.append(row)
                with (OUT/(mode+'-observations.jsonl')).open('a', encoding='utf-8') as handle:
                    handle.write(json.dumps(row)+'\n')
            def addSuccess(self, test):
                self.record(test, 'PASS'); super().addSuccess(test)
            def addFailure(self, test, err):
                self.record(test, 'FAIL', err); super().addFailure(test, err)
            def addError(self, test, err):
                self.record(test, 'ERROR', err); super().addError(test, err)
            def addSkip(self, test, reason):
                self.record(test, 'SKIP', reason=reason); super().addSkip(test, reason)
            def addExpectedFailure(self, test, err):
                self.record(test, 'EXPECTED_FAILURE', err); super().addExpectedFailure(test, err)
            def addUnexpectedSuccess(self, test):
                self.record(test, 'UNEXPECTED_SUCCESS'); super().addUnexpectedSuccess(test)
            def addSubTest(self, test, subtest, err):
                if err:
                    self.record(subtest, 'SUBTEST_FAIL', err)
                super().addSubTest(test, subtest, err)
        return AuditResult

exit_code = 2
try:
    failures = AuditRunner(verbosity=1, interactive=False, parallel=1).run_tests(labels)
    exit_code = 1 if failures else 0
except BaseException:
    traceback.print_exc()
finally:
    statuses = {s: sum(x['status']==s for x in observations) for s in sorted({x['status'] for x in observations})}
    result = {**{k:v for k,v in inventory.items() if k != 'ids'}, 'elapsed_seconds': round(time.monotonic()-started, 3), 'exit_code': exit_code, 'statuses': statuses, 'method_observations': observations, 'not_observed_ids': sorted(set(unique)-{x['id'] for x in observations})}
    (OUT/(mode+'-results.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('AUDIT RESULT', json.dumps({'exit_code': exit_code, 'statuses': statuses, 'not_observed': len(result['not_observed_ids'])}), flush=True)
sys.exit(exit_code)
