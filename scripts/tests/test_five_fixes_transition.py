import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('five_transition', ROOT / 'scripts/releases/five-fixes-20261116/transition.py')
transition = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transition)


class TransitionTests(unittest.TestCase):
    def fixture(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        release = transition.AttestedRelease(ROOT, Path(tmp.name))
        release.target_revision = 'a' * 40
        release.inspect = lambda: {'Image': transition.BASE_IMAGE}
        release.actual = {p: row['live'] for p, row in transition.DRIFT.items()}
        def command(args, **kwargs):
            if args[:2] == ['git', 'rev-parse']:
                revision, path = args[-1].split(':', 1)
                row = transition.DRIFT[path]
                return row['git'] if revision == transition.BASE_REVISION else row['live']
            if args[:2] == ['docker', 'exec']:
                return json.dumps(release.actual)
            raise AssertionError(args)
        release.command = command
        def baseline(_self, revision):
            (release.directory / 'baseline-source-drift.json').write_text(json.dumps(list(transition.DRIFT)))
            raise RuntimeError('Running image contains uncommitted overlays; reconcile them before release')
        self.patch = patch.object(transition.Release, 'verify_baseline_source', baseline)
        self.patch.start(); self.addCleanup(self.patch.stop)
        return release

    def test_exact_audited_baseline_and_preserved_analytics_are_accepted(self):
        self.fixture().verify_baseline_source(transition.BASE_REVISION)

    def test_another_image_or_revision_is_never_accepted(self):
        release = self.fixture()
        with self.assertRaises(RuntimeError): release.verify_baseline_source('b' * 40)
        release.inspect = lambda: {'Image': 'sha256:' + 'b' * 64}
        with self.assertRaises(RuntimeError): release.verify_baseline_source(transition.BASE_REVISION)

    def test_modified_audited_overlay_is_rejected(self):
        release = self.fixture()
        release.actual['src/catalog/context_processors.py'] = 'b' * 40
        with self.assertRaises(RuntimeError): release.verify_baseline_source(transition.BASE_REVISION)

    def test_unlisted_source_drift_is_rejected(self):
        release = self.fixture()
        def unknown(_self, revision):
            (release.directory / 'baseline-source-drift.json').write_text(json.dumps([*transition.DRIFT, 'src/unknown.py']))
            raise RuntimeError('Running image contains uncommitted overlays; reconcile them before release')
        with patch.object(transition.Release, 'verify_baseline_source', unknown):
            with self.assertRaises(RuntimeError): release.verify_baseline_source(transition.BASE_REVISION)

    def test_candidate_must_preserve_each_production_analytics_file(self):
        release = self.fixture(); original = release.command
        def changed(args, **kwargs):
            if args[:2] == ['git', 'rev-parse'] and args[-1].startswith(release.target_revision): return 'c' * 40
            return original(args, **kwargs)
        release.command = changed
        with self.assertRaises(RuntimeError): release.verify_baseline_source(transition.BASE_REVISION)

    def test_clean_candidate_probe_uses_python_code_and_no_network(self):
        release = self.fixture(); calls = []
        release.command = lambda args, **kwargs: calls.append(args) or ''
        release.state['candidate_image'] = 'sha256:' + 'c' * 64
        def probe(verifier, revision):
            verifier.command(['docker', 'exec', '-i', 'kidsmap-web', 'python', '-c', 'print(1)'], input=b'{}')
        with patch.object(transition.Release, 'prepare'), patch.object(transition.Release, 'verify_baseline_source', probe):
            release.prepare('a' * 40)
        self.assertEqual(calls, [['docker', 'run', '--rm', '--network', 'none', '-i', '--entrypoint',
                                 'python', 'sha256:' + 'c' * 64, '-c', 'print(1)']])
