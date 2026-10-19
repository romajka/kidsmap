"""Isolation must fail closed before a full quality run can touch a database."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('quality_profile', ROOT/'scripts/run_isolated_quality.py')


@unittest.skipUnless(os.name == 'posix', 'Linux quality profile; run in WSL or CI')
class QualityProfilePathTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(prefix='quality-profile-unit-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)/'repo'
        self.socket = self.repo/'.tmp/kidsmap-task33-qa04-socket-unit/socket'
        self.socket.mkdir(parents=True)
        self.profile_temp = tempfile.TemporaryDirectory(prefix='kidsmap-task33-qa04-unit-')
        self.addCleanup(self.profile_temp.cleanup)
        self.profile = Path(self.profile_temp.name)

    def test_current_owned_directory_layout_is_accepted(self):
        self.assertEqual(self.module.validate_paths(self.profile, self.socket, self.repo), (self.profile, self.socket))

    def test_unrelated_profile_root_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.validate_paths(Path(self.temp.name), self.socket, self.repo)

    def test_foreign_socket_is_rejected(self):
        with self.assertRaises(ValueError):
            self.module.validate_paths(self.profile, Path(self.temp.name)/'socket', self.repo)

    def test_socket_parent_symlink_is_rejected(self):
        link = self.repo/'.tmp/kidsmap-task33-qa04-socket-link'
        link.symlink_to(self.socket.parent, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.module.validate_paths(self.profile, link/'socket', self.repo)

    def test_profile_symlink_is_rejected(self):
        link = self.repo/'profile-link'
        link.symlink_to(self.profile, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.module.validate_paths(link, self.socket, self.repo)
