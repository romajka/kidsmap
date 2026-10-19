from pathlib import Path
import sys
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/cross'
(S/'IMPLEMENTATION_PLAN.md').write_text((O/'IMPLEMENTATION_PLAN.md').read_text()+'\nConfirmed RED r2: 7 methods, 10 failed observations, no errors. Canonical complete discovery uses every current catalog.testcases Python module through the existing custom runner; explicit labels and explicit pattern keep their scope. Wrapper full invokes no-label canonical runner. No root wildcard imports or application test assertions changed.\n')
sys.path.insert(0,str(Q));from stage_apply import apply
path='src/catalog/controllers/public_details.py';t=(R/path).read_text();assert t.count("occurrence_state='scheduled'")==1;t=t.replace("occurrence_state='scheduled'","occurrence_state__in=('scheduled', 'rescheduled')")
runner='src/config/test_runner.py';r=(R/runner).read_text();r=r.replace('import unittest\n','import unittest\nimport pkgutil\n')
needle='    parallel_test_suite = KidsMapParallelTestSuite\n'
assert r.count(needle)==1
r=r.replace(needle,needle+'''
    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            # src/ is not traversed by repository-root unittest discovery.
            # Discover the domain package and legacy non-test-prefixed suites
            # automatically so new modules cannot silently miss the CI gate.
            from catalog import testcases

            test_labels = ["catalog.testcases"]
            if self.pattern == "test*.py":
                test_labels += [
                    f"catalog.testcases.{module.name}"
                    for module in sorted(pkgutil.iter_modules(testcases.__path__), key=lambda item: item.name)
                    if not module.ispkg and not module.name.startswith("test")
                ]
        return super().build_suite(test_labels, **kwargs)
''')
wrapper='scripts/run_kidsmap_tests.sh';w=(R/wrapper).read_text();assert '    run_suite catalog\n' in w;w=w.replace('    run_suite catalog\n','    # No labels selects the canonical complete KidsMapTestRunner corpus.\n    run_suite\n')
apply('cross',{path:t.encode(),runner:r.encode(),wrapper:w.encode()},'stages/cross/evidence/red-r2.json')
