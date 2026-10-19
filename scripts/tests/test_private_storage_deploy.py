"""Release must stop before recreating a container holding unmounted private bytes."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


@unittest.skipUnless(os.name=='posix','Deployment shell runs on Linux')
class PrivateStorageDeployGuardTests(unittest.TestCase):
    def run_deploy(self,mounts,*,stopped=False):
        temp=tempfile.TemporaryDirectory(prefix='kidsmap-private-deploy-test-')
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        (root/'.git').mkdir()
        scripts=root/'scripts'
        scripts.mkdir()
        for name in ('deploy-server.sh','check-private-storage.sh'):
            source=ROOT/'scripts'/name
            if source.exists():
                # The release artifact is a Linux shell script. Normalize the
                # Windows checkout's line endings in this controlled fixture.
                (scripts/name).write_text(source.read_text(),newline='\n')
        bin_dir=root/'bin'
        bin_dir.mkdir()
        docker=bin_dir/'docker'
        docker.write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$AUDIT_CALLS"
case "$*" in
  'compose ps '*)
    case "$*" in
      *'--all'*|*'-aq'*|*'-qa'*|*' -a '*) printf '%s\\n' fake-web ;;
      *) [ "$AUDIT_STOPPED" = 1 ] || printf '%s\\n' fake-web ;;
    esac ;;
  inspect*) printf '%s\\n' "$AUDIT_MOUNTS" ;;
  exec*) exit 1 ;;
esac
exit 0
''')
        git=bin_dir/'git'
        git.write_text('#!/bin/sh\nexit 0\n')
        curl=bin_dir/'curl'
        curl.write_text('#!/bin/sh\nprintf "200 http://fictional.invalid/"\n')
        for path in (docker,git,curl):
            path.chmod(0o755)
        calls=root/'calls'
        env={'PATH':str(bin_dir)+os.pathsep+os.defpath,'AUDIT_CALLS':str(calls),'AUDIT_MOUNTS':mounts,
             'AUDIT_STOPPED':'1' if stopped else '0'}
        result=subprocess.run(['bash',str(scripts/'deploy-server.sh')],cwd=root,env=env,capture_output=True,text=True,timeout=15)
        return result,calls.read_text() if calls.exists() else ''

    def test_unmounted_private_bytes_block_before_any_build_or_recreate(self):
        result,calls=self.run_deploy('/app/media\n/app/staticfiles')
        self.assertNotEqual(result.returncode,0,'Deployment must stop while private bytes live only in the old container')
        self.assertNotIn('compose build',calls)
        self.assertNotIn('compose up',calls)
        self.assertNotIn('release-server.sh',calls)

    def test_persisted_private_roots_allow_existing_release_path(self):
        result,calls=self.run_deploy('/app/media\n/app/staticfiles\n/kidsmap-private-media\n/app/private_media_drafts')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('compose build web',calls)

    def test_stopped_container_with_private_bytes_blocks_before_recreation(self):
        result,calls=self.run_deploy('/app/media\n/app/staticfiles',stopped=True)
        self.assertNotEqual(result.returncode,0,
            'Stopped containers can still hold private bytes and must not be silently replaced')
        self.assertNotIn('compose build',calls)
        self.assertNotIn('compose up',calls)
        self.assertNotIn('release-server.sh',calls)
