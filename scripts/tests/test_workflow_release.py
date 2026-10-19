"""No online0142 migration while old notification writers remain active."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


@unittest.skipUnless(os.name == 'posix', 'Deployment shell runs on Linux')
class WorkflowReleaseBoundaryTests(unittest.TestCase):
    def run_release(self, pending, stopped=False):
        with tempfile.TemporaryDirectory(prefix='kidsmap-workflow-release-') as directory:
            root = Path(directory)
            (root/'locale').mkdir()
            (root/'release.sh').write_text((Path(__file__).resolve().parents[2]/'scripts/release-server.sh').read_text(), newline='\n')
            python = root/'python'
            python.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$AUDIT_CALLS"\ncase "$*" in\n *showmigrations*) printf "%s\\n" "$AUDIT_PLAN" ;;\nesac\n')
            python.chmod(0o755)
            calls = root/'calls'
            env = {'PATH':str(root)+os.pathsep+os.defpath, 'AUDIT_CALLS':str(calls),
                'AUDIT_PLAN':('[ ]' if pending else '[X]')+' catalog.0142_workflownotification_event_context'}
            if stopped:
                env['KIDSMAP_WRITERS_STOPPED'] = '1'
            result = subprocess.run(['sh',str(root/'release.sh')],cwd=root,env=env,capture_output=True,text=True,timeout=15)
            return result, calls.read_text()

    def test_pending_0142_requires_an_explicit_stopped_writer_boundary(self):
        result,calls = self.run_release(pending=True)
        self.assertNotEqual(result.returncode,0)
        self.assertNotIn('manage.py migrate',calls)

    def test_reviewed_stopped_writer_boundary_allows_the_complete_batch(self):
        result,calls = self.run_release(pending=True,stopped=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('manage.py migrate --noinput',calls)

    def test_already_compatible_installation_does_not_require_initial_transition(self):
        result,calls = self.run_release(pending=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('manage.py migrate --noinput',calls)
