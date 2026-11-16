"""The public deployment entry point must refuse moving branch names."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class DeployRevisionGuardTests(unittest.TestCase):
    def invoke(self, args):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / '.git').mkdir(); (root / 'scripts').mkdir()
            for name in ('deploy-server.sh', 'check-private-storage.sh', 'deploy_server.py'):
                source = ROOT / 'scripts' / name
                if source.exists(): (root / 'scripts' / name).write_text(source.read_text())
            bindir = root / 'bin'; bindir.mkdir(); calls = root / 'calls'
            for name in ('git', 'docker', 'curl'):
                executable = bindir / name
                executable.write_text('#!/bin/sh\nprintf "%s\\n" "'+name+' $*" >> "$AUDIT_CALLS"\n' +
                                      ('printf "200 http://fictional.invalid/"\n' if name == 'curl' else 'exit 0\n'))
                executable.chmod(0o755)
            result = subprocess.run(['bash', str(root / 'scripts/deploy-server.sh'), *args], cwd=root,
                                    env={'PATH': str(bindir)+os.pathsep+os.defpath, 'AUDIT_CALLS': str(calls)},
                                    capture_output=True, text=True, timeout=10)
            return result, calls.read_text() if calls.exists() else ''

    def test_missing_tested_revision_stops_before_docker(self):
        result, calls = self.invoke([])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('docker', calls)

    def test_moving_branch_is_not_a_deployable_revision(self):
        result, calls = self.invoke(['main'])
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('docker', calls)
