"""Fault injection at the Docker boundary, using real static files and journals."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts.deploy_server import Release, fingerprint

OLD = 'sha256:' + '1' * 64
NEW = 'sha256:' + '2' * 64
SHA = 'a' * 40

class DockerFixture(Release):
    def __init__(self, root, failure=None):
        directory = root / 'release'; directory.mkdir()
        super().__init__(root, directory)
        self.failure = failure
        self.calls = []
        self.static = root / 'staticfiles'; self.static.mkdir()
        (self.static / 'staticfiles.json').write_text('old manifest')
        self.config = {'services': {'web': {'image': OLD, 'environment': {'PUBLIC_BASE_URL': 'https://kidsmap.test'},
                                         'labels': {'org.opencontainers.image.revision': 'b'*40}}}}
        configfile = root / 'current.json'; configfile.write_text(json.dumps(self.config))
        self.container = {'Id':'old-container', 'Image': OLD, 'State':{'Running':True},
            'Config':{'Env':['PUBLIC_BASE_URL=https://kidsmap.test'], 'Labels':{
                'org.opencontainers.image.revision':'b'*40, 'com.docker.compose.project':'kidsmap',
                'com.docker.compose.config-hash':'config-hash', 'com.docker.compose.project.working_dir':str(root), 'com.docker.compose.project.config_files':str(configfile)}},
            'HostConfig': {'Binds': [str(self.static)+':/app/staticfiles:rw']},
            'Mounts':[{'Type':'bind','Source':str(self.static),'Destination':'/app/staticfiles','RW':True}],
            'NetworkSettings':{'Networks':{'kidsmap_default':{}}}}
    def inspect(self):
        if self.container is None: raise RuntimeError('container missing')
        return copy.deepcopy(self.container)
    def verify_baseline_source(self, revision): pass  # Separate real source-drift boundary test below.
    def health(self):
        if self.failure == 'health' and self.container['Image'] == NEW: raise RuntimeError('unhealthy')
    def smoke(self):
        if self.failure == 'smoke': raise RuntimeError('public page failed')
    def command(self, args, **kwargs):
        self.calls.append(args)
        if args[:2] == ['docker', 'ps']: return self.container['Id'] if self.container else ''
        if args[:2] == ['git','status']: return ' M app.py' if self.failure == 'dirty' else ''
        if args[:2] == ['git','rev-parse']: return 'c'*40 if self.failure == 'stale' else SHA
        if args[:2] == ['docker','build']:
            if self.failure == 'build': raise RuntimeError('build failed')
        if args[:3] == ['docker','image','inspect']: return NEW
        if 'config' in args and '--hash' in args: return 'web ' + ('changed' if self.failure == 'config_drift' else 'config-hash')
        if 'config' in args and '--format' in args:
            configfile = Path(args[args.index('-f')+1])
            return configfile.read_text()
        if 'migrate' in args and self.failure == 'migration': raise RuntimeError('pending migrations')
        if 'collectstatic' in args:
            (self.static / 'staticfiles.json').write_text('new manifest')
            if self.failure == 'static': raise RuntimeError('static failed')
        if 'up' in args:
            image = OLD if 'rollback.compose.json' in ' '.join(args) else NEW
            if self.container is None: self.container = copy.deepcopy(self.original)
            self.container['Image'] = image
            self.container['Id'] = 'replacement'
            if image == NEW and self.failure == 'missing':
                self.original = copy.deepcopy(self.container)
                self.container = None
                raise RuntimeError('create failed after removing old container')
            if image == NEW and self.failure == 'activate': raise RuntimeError('activation failed')
        return ''

class DeployRecoveryTests(unittest.TestCase):
    def fixture(self, failure=None):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        return DockerFixture(Path(temp.name), failure)
    def test_pre_activation_failures_leave_original_container_and_static_untouched(self):
        for failure in ('dirty', 'stale', 'config_drift', 'build', 'migration'):
            with self.subTest(failure=failure):
                release = self.fixture(failure)
                with self.assertRaises(RuntimeError):
                    release.prepare(SHA); release.activate()
                self.assertEqual(release.container['Id'], 'old-container')
                self.assertEqual((release.static / 'staticfiles.json').read_text(), 'old manifest')
                self.assertFalse(any('up' in args for args in release.calls))
    def test_activation_failures_restore_previous_image_and_manifest(self):
        for failure in ('static', 'activate', 'missing', 'health', 'smoke'):
            with self.subTest(failure=failure):
                release = self.fixture(failure); release.prepare(SHA)
                with self.assertRaises(RuntimeError): release.activate()
                self.assertIsNotNone(release.container, 'Rollback must recreate a missing web container')
                self.assertEqual(release.container['Image'], OLD)
                self.assertEqual((release.static / 'staticfiles.json').read_text(), 'old manifest')
                self.assertEqual(json.loads((release.directory / 'state.json').read_text())['phase'], 'rolled_back')
                for args in release.calls:
                    if 'up' in args: self.assertIn('--no-deps', args); self.assertIn('--no-build', args)
    def test_success_activates_immutable_candidate_without_database_mutations(self):
        release = self.fixture(); release.prepare(SHA); release.activate()
        self.assertEqual(release.container['Image'], NEW)
        self.assertEqual(release.state['phase'], 'complete')
        self.assertEqual((release.static / 'staticfiles.json').read_text(), 'new manifest')
        self.assertFalse(any('pg_restore' in args or 'sync_site_defaults' in args for args in release.calls))
        self.assertTrue(all('--check' in args for args in release.calls if 'migrate' in args))
    def test_concurrent_replacement_stops_before_static_mutation(self):
        release = self.fixture(); release.prepare(SHA); release.container['Id'] = 'another-release'
        with self.assertRaises(RuntimeError): release.activate()
        self.assertEqual((release.static / 'staticfiles.json').read_text(), 'old manifest')
    def test_failed_static_recovery_still_attempts_original_image_and_records_failure(self):
        release = self.fixture(); release.prepare(SHA); release.container['Image'] = NEW
        with patch('scripts.deploy_server.shutil.copytree', side_effect=OSError('disk failed')):
            with self.assertRaises(RuntimeError): release.rollback()
        self.assertEqual(release.container['Image'], OLD)
        self.assertEqual(release.state['phase'], 'rollback_failed')
    def test_bind_order_is_ignored_but_path_changes_are_not(self):
        release = self.fixture(); a = release.inspect(); b = copy.deepcopy(a)
        a['HostConfig']['Binds'] += ['second:/second:rw']; b['HostConfig']['Binds'] = list(reversed(a['HostConfig']['Binds']))
        self.assertEqual(fingerprint(a), fingerprint(b))
        b['Mounts'][0]['Source'] = '/wrong/static'
        self.assertNotEqual(fingerprint(a), fingerprint(b))

    def test_explicit_recovery_cannot_replace_an_unrelated_newer_release(self):
        release = self.fixture(); release.prepare(SHA)
        release.container['Image'] = 'sha256:' + '3'*64
        with self.assertRaises(RuntimeError): release.rollback()
        self.assertEqual(release.container['Image'], 'sha256:' + '3'*64)

class BaselineSourceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / 'src').mkdir()
        directory = self.root / 'release'
        directory.mkdir()
        self.git('init', '-q')
        self.release = Release(self.root, directory)
        command = self.release.command

        def boundary(args, **kwargs):
            if args[:2] == ['docker', 'exec']:
                probe = args[-1].replace("pathlib.Path('/app',name)", f"pathlib.Path({str(self.root)!r},name)")
                return subprocess.check_output([sys.executable, '-c', probe], input=kwargs['input']).decode()
            return command(args, **kwargs)

        self.release.command = boundary

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'user.name=Fixture', '-c',
                                        'user.email=fixture@example.invalid', *args], cwd=self.root)

    def test_real_git_blob_comparison_detects_live_overlay(self):
        source = self.root / 'src/app.py'
        source.write_text('value = 1\n')
        self.git('add', 'src')
        self.git('commit', '-qm', 'fixture')
        self.release.verify_baseline_source('HEAD')
        source.write_text('value = 2\n')
        with self.assertRaisesRegex(RuntimeError, 'uncommitted overlays'):
            self.release.verify_baseline_source('HEAD')
        self.assertEqual(json.loads((self.release.directory / 'baseline-source-drift.json').read_text()),
                         ['src/app.py'])

    def test_archived_revision_must_match_the_running_commit_exactly(self):
        path = 'src/catalog/services/deploy_revision.txt'
        marker = self.root / path
        marker.parent.mkdir(parents=True)
        marker.write_bytes(b'$Format:%H$\n')
        (self.root / '.gitattributes').write_text(f'/{path} export-subst\n')
        self.git('add', 'src', '.gitattributes')
        self.git('commit', '-qm', 'running release')
        baseline = self.git('rev-parse', 'HEAD').decode().strip()
        self.git('commit', '--allow-empty', '-qm', 'next release')
        with tarfile.open(fileobj=io.BytesIO(self.git('archive', baseline, '--', path))) as archive:
            archived = archive.extractfile(path).read()
        self.assertEqual(archived, baseline.encode() + b'\n')
        marker.write_bytes(archived)
        self.release.verify_baseline_source(baseline)

        for wrong in (self.git('rev-parse', 'HEAD'), b'$Format:%H$\n', archived.rstrip(b'\n')):
            with self.subTest(wrong=wrong):
                marker.write_bytes(wrong)
                with self.assertRaisesRegex(RuntimeError, 'uncommitted overlays'):
                    self.release.verify_baseline_source(baseline)
                self.assertEqual(json.loads((self.release.directory / 'baseline-source-drift.json').read_text()),
                                 [path])
