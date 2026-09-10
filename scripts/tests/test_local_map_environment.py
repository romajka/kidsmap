"""Local runserver must receive map configuration without loading service credentials."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("kidsmap_manage", Path(__file__).resolve().parents[2] / "manage.py")
manage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manage)


class LocalMapEnvironmentTests(unittest.TestCase):
    def test_runserver_loads_only_map_values(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            (root / '.env').write_text('GOOGLE_MAPS_API_KEY="local-test-key" # comment\nGOOGLE_MAPS_MAP_ID=local-map\nDATABASE_URL=do-not-load\nDJANGO_SECRET_KEY=do-not-load\n')
            manage.load_local_map_environment(root, 'runserver')
            self.assertEqual(os.environ.get('GOOGLE_MAPS_API_KEY'), 'local-test-key')
            self.assertEqual(os.environ.get('GOOGLE_MAPS_MAP_ID'), 'local-map')
            self.assertNotIn('DATABASE_URL', os.environ)
            self.assertNotIn('DJANGO_SECRET_KEY', os.environ)

    def test_explicit_environment_including_empty_values_wins(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'explicit', 'GOOGLE_MAPS_MAP_ID': ''}, clear=True):
            root = Path(directory)
            (root / '.env').write_text('GOOGLE_MAPS_API_KEY=local\nGOOGLE_MAPS_MAP_ID=local-map\n')
            manage.load_local_map_environment(root, 'runserver')
            self.assertEqual(os.environ['GOOGLE_MAPS_API_KEY'], 'explicit')
            self.assertEqual(os.environ['GOOGLE_MAPS_MAP_ID'], '')

    def test_other_commands_do_not_read_local_configuration(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            (root / '.env').write_text('GOOGLE_MAPS_API_KEY=local\n')
            for command in ('test', 'migrate', 'check', 'collectstatic', ''):
                manage.load_local_map_environment(root, command)
                self.assertNotIn('GOOGLE_MAPS_API_KEY', os.environ)

    def test_missing_file_is_optional(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            manage.load_local_map_environment(Path(directory), 'runserver')
            self.assertNotIn('GOOGLE_MAPS_API_KEY', os.environ)


if __name__ == '__main__':
    unittest.main()
