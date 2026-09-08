"""Exercise only a copied backup script and temporary synthetic backups."""
import gzip
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest


class BackupFailureTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="kidsmap-backup-test-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.script = root / "scripts" / "backup-db.sh"
        self.script.parent.mkdir()
        source = Path(__file__).resolve().parents[1] / "backup-db.sh"
        shutil.copyfile(source, self.script)
        self.backups = root / "backups"
        self.backups.mkdir()
        self.old = self.backups / "kidsmap-db-20000101-000000.sql.gz"
        self.old.write_bytes(gzip.compress(b"old synthetic backup"))
        old_time = time.time() - 20 * 86400
        os.utime(self.old, (old_time, old_time))

    def run_backup(self, dump_exit=0, gzip_exit=None):
        # Exported functions take precedence over the script's fixed PATH.
        # No real Docker executable, daemon, credentials or repository backups.
        env = {
            "PATH": "/usr/bin:/bin", "BACKUP_DIR": str(self.backups),
            "BASH_FUNC_docker%%": "() { printf 'synthetic SQL\\n'; return " + str(dump_exit) + "; }",
        }
        if gzip_exit is not None:
            env["BASH_FUNC_gzip%%"] = "() { cat >/dev/null; return " + str(gzip_exit) + "; }"
        return subprocess.run(["/bin/bash", str(self.script)], env=env,
                              capture_output=True, text=True, timeout=10)

    def assert_failure_preserves_backups(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("database saved", result.stdout)
        self.assertEqual(list(self.backups.iterdir()), [self.old])
        self.assertEqual(gzip.decompress(self.old.read_bytes()), b"old synthetic backup")

    def test_dump_failure_does_not_report_success_or_run_retention(self):
        self.assert_failure_preserves_backups(self.run_backup(dump_exit=23))

    def test_compression_failure_does_not_run_retention(self):
        self.assert_failure_preserves_backups(self.run_backup(gzip_exit=24))

    def test_success_produces_valid_archive_and_runs_retention(self):
        result = self.run_backup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("database saved", result.stdout)
        archives = list(self.backups.iterdir())
        self.assertEqual(len(archives), 1)
        self.assertNotEqual(archives[0], self.old)
        self.assertEqual(gzip.decompress(archives[0].read_bytes()), b"synthetic SQL\n")
