"""Artifact identity and isolation checks; no project services or credentials."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('r1_artifact', Path(__file__).with_name('artifact.py'))
artifact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(artifact)


class ArtifactSafetyTests(unittest.TestCase):
    def test_paths_cannot_import_env_private_data_or_escape(self):
        for path in ('../src/a.py', '/src/a.py', 'src/../../.env', 'src/.env', '.env', 'media/user.jpg', '.git/config', 'src/__pycache__/a.pyc'):
            self.assertFalse(artifact.permitted(path), path)
        self.assertTrue(artifact.permitted('src/catalog/models/place.py'))

    def test_repeat_freeze_identical_and_tampered_standby_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / 'source'
            (source / 'src').mkdir(parents=True)
            (source / 'src/a.py').write_text('value = 1\n')
            (source / '.env').write_text('excluded-synthetic-value')
            first = artifact.freeze(source, root / 'one', root / 'standby-one')
            second = artifact.freeze(source, root / 'two', root / 'standby-two')
            self.assertEqual(first['identity'], second['identity'])
            self.assertEqual(first['archive_sha256'], second['archive_sha256'])
            self.assertFalse((root / 'standby-one/.env').exists())
            import json
            manifest = json.loads((Path(first['archive']).parent / 'manifest.json').read_text())
            (root / 'standby-one/src/a.py').write_text('value = 2\n')
            with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
                artifact.verify(root / 'standby-one', manifest)
            with self.assertRaisesRegex(RuntimeError, 'Existing/unsafe'):
                artifact.freeze(source, root / 'three', root / 'standby-two')


if __name__ == '__main__':
    unittest.main()
