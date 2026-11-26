import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'weekly_cleanup.py'


class WeeklyCleanupTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), 'weekly cleanup entry point is missing')
        spec = importlib.util.spec_from_file_location('weekly_cleanup', SCRIPT)
        self.job = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.job)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / 'releases'
        self.root.mkdir()
        self.current = 'sha256:' + '1' * 64
        self.rollback = 'sha256:' + '2' * 64
        self.paths = []
        for i in range(1, 9):
            revision = f'{i:040x}'[::-1]
            p = self.root / (revision[:12] + '-abcdefgh')
            p.mkdir()
            for dirname in ('source', 'static.before'):
                (p / dirname).mkdir()
            for name in ('source.tar', 'commands.log', 'baseline-source-drift.json'):
                (p / name).touch()
            for name in ('candidate.compose.json', 'rollback.compose.json'):
                (p / name).write_text(json.dumps({'services': {'web': {'image': 'kidsmap:release'}}}))
            state = {'phase': 'complete', 'revision': revision,
                     'candidate_image': {1: self.current, 2: self.rollback}.get(i, 'sha256:' + 'a'*64),
                     'baseline_image': self.rollback}
            (p / 'state.json').write_text(json.dumps(state))
            os.utime(p / 'state.json', (1000+i, 1000+i))
            os.utime(p, (1000+i, 1000+i))
            self.paths.append(p)
        self.web = {'Name': '/kidsmap-web', 'Image': self.current, 'State': {'Running': True}, 'Mounts': [],
                    'Config': {'Labels': {'com.docker.compose.project.config_files':
                                         str(self.paths[0] / 'candidate.compose.json')}}}

    def plan(self, extra=(), mounts=()):
        return self.job.release_plan(self.root, [self.web, *extra], mounts)

    def test_old_current_rollback_and_latest_three_survive(self):
        candidates, images, pair = self.plan()
        self.assertEqual(set(candidates), set(self.paths[2:5]))
        self.assertEqual(pair, (self.current, self.rollback))
        self.assertIn('kidsmap:release', images)

    def test_stopped_mount_nested_backup_and_retained_compose_reference(self):
        (self.paths[3] / 'source' / 'database.dump').touch()
        doc = self.paths[6] / 'rollback.compose.json'
        doc.write_text(json.dumps({'services': {'worker': {'volumes': [str(self.paths[2]) + '/source:/app']}}}))
        other = {'Name': '/old', 'Image': 'old', 'Mounts': [{'Source': str(self.paths[4] / 'static.before')}],
                 'Config': {'Labels': {}}, 'State': {'Running': False}}
        self.assertEqual(self.plan([other])[0], [])

    def test_mountpoints_nonstandard_layout_and_hidden_env(self):
        (self.paths[3] / 'source' / '.env').touch()
        (self.paths[4] / 'snapshot.tar').touch()
        self.assertEqual(self.plan(mounts=[self.paths[2] / 'source' / 'mount'])[0], [])

    def test_default_and_explicit_dry_run_cannot_apply(self):
        for args, env in [([], {}), ([], {'DRY_RUN': '1'}), (['--dry-run'], {'DRY_RUN':'0'})]:
            with self.subTest(args=args, env=env):
                with patch.dict(os.environ, env, clear=True):
                    self.assertFalse(self.job.apply_requested(args))

    def test_dry_run_never_mutates(self):
        candidates, images, pair = self.plan()
        with patch.object(self.job, 'command') as command, contextlib.redirect_stdout(io.StringIO()):
            self.job.perform(False, candidates, pair, images)
        command.assert_not_called()
        self.assertTrue(all(p.exists() for p in self.paths))

    def test_dangling_image_by_digest_or_short_id_is_protected(self):
        digest = 'sha256:' + 'd'*64
        img = {'Id': self.rollback, 'RepoDigests': ['kidsmap@'+digest]}
        for refs in ({self.rollback}, {self.rollback[7:19]}, {'kidsmap@'+digest}):
            with self.subTest(refs=refs):
                self.assertTrue(self.job.compose_uses(img, refs))
        self.assertFalse(self.job.compose_uses(img, {'kidsmap:release'}))

    def test_apply_removes_only_candidates_and_runs_prunes_in_order(self):
        candidates, images, pair = self.plan()
        self.enterContext(patch.object(self.job, 'docker_containers', return_value=[self.web]))
        self.enterContext(patch.object(self.job, 'image_candidates', return_value=[]))
        with patch.object(self.job, 'command',return_value='') as command, \
                patch.object(self.job, 'protect_tags'), patch.object(self.job, 'disk'), \
                contextlib.redirect_stdout(io.StringIO()):
            self.job.perform(True, candidates, pair, images)
        self.assertEqual([x.args for x in command.call_args_list], [
            ('journalctl', '--vacuum-time=14d'), ('docker','image','prune'), ('docker','builder','prune')])
        self.assertTrue(all(not p.exists() for p in candidates))
        self.assertTrue(all(p.exists() for p in set(self.paths)-set(candidates)))

    def test_recovery_compose_at_release_root_protects_relative_path_and_image(self):
        image = 'sha256:' + 'd'*64
        (self.root/'recovery.compose.json').write_text(json.dumps({'services': {
            'restore': {'image': image, 'volumes': ['./'+self.paths[2].name+'/source:/app']}}}))
        candidates, refs, _ = self.plan()
        self.assertNotIn(self.paths[2], candidates)
        self.assertIn(image, refs)

    def test_protection_tags_the_image_then_rechecks_tags(self):
        current, rollback = self.current, self.rollback
        state = {current: ['kidsmap:stable'], rollback: []}
        def docker(*args):
            if args[:3] == ('docker','image','inspect'):
                return json.dumps(state[args[-1]])
            if args[:3] == ('docker','image','ls'):
                return ''
            if args == ('docker','tag',rollback,'kidsmap:keep-rollback'):
                state[rollback].append(args[-1])
                return ''
            raise AssertionError(args)
        with patch.object(self.job, 'command', side_effect=docker):
            self.job.protect_tags((current,rollback))
        self.assertEqual(state[rollback], ['kidsmap:keep-rollback'])
        self.assertEqual(state[current], ['kidsmap:stable'])

    def test_catch_a_compose_image_losing_its_tag_before_prune(self):
        paths, refs, pair = self.plan()
        def docker(*args, **kwargs):
            if args[:3] == ('docker','image','ls'):
                return self.rollback
            if args[:3] == ('docker','image','inspect'):
                return json.dumps([{'Id': self.rollback, 'RepoDigests': []}])
            if args == ('journalctl', '--vacuum-time=14d'):
                return ''
            raise AssertionError(f'Unexpected command {args!r}')
        pair = (self.current, 'sha256:' + '3'*64)
        with patch.object(self.job, 'docker_containers', return_value=[self.web]), \
                patch.object(self.job, 'protect_tags'), patch.object(self.job, 'disk'), \
                patch.object(self.job, 'command',side_effect=docker):
            with self.assertRaisesRegex(RuntimeError, 'Compose'):
                self.job.perform(True, [], pair, {self.rollback})

    def test_busy_deploy_lock_skips_all_work(self):
        import fcntl
        lockfile = self.root/'existing.lock'
        with lockfile.open('wb') as lock, patch.object(self.job,'LOCK',lockfile), \
                patch.object(self.job,'run', side_effect=AssertionError('lock was ignored')), \
                contextlib.redirect_stdout(io.StringIO()):
            fcntl.flock(lock,fcntl.LOCK_EX)
            self.assertEqual(self.job.main(['--dry-run']), 0)

    def test_nested_media_archive_and_private_draft_directory_are_preserved(self):
        (self.paths[2] / 'source' / 'media-before.tgz').touch()
        (self.paths[3] / 'source' / 'private_media_drafts').mkdir()
        candidates, _, _ = self.plan()
        self.assertEqual(candidates, [self.paths[4]])

    def test_dry_run_env_rejects_apply_even_if_cli_requests_it(self):
        with patch.dict(os.environ, {'DRY_RUN': '1'}), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                self.job.apply_requested(['--apply'])
        self.assertEqual(result.exception.code, 2)

    def test_keep_tag_collision_is_reported_without_retagging(self):
        def docker(*args):
            if args[:3] == ('docker','image','inspect'):
                return '[]'
            if args[:3] == ('docker','image','ls'):
                return self.rollback
            self.fail(f'Unexpected command {args!r}')
        with patch.object(self.job,'command',side_effect=docker):
            with self.assertRaisesRegex(RuntimeError, 'Conflicting protection tag'):
                self.job.protect_tags((self.current,self.rollback))

    def test_release_archive_with_tracked_empty_media_placeholder_can_age_out(self):
        for path in self.paths[2:4]:
            media = path / 'source' / 'media'
            media.mkdir()
            (media / '.gitkeep').touch()
        (self.paths[3] / 'source' / 'media' / 'real-photo.jpg').write_bytes(b'preserve')
        candidates, _, _ = self.plan()
        self.assertIn(self.paths[2], candidates)
        self.assertNotIn(self.paths[3], candidates)

    def test_shipped_media_icons_in_source_and_collected_static_can_age_out(self):
        path = self.paths[2]
        for base in (path/'source'/'static', path/'static.before'):
            icons = base/'img'/'icon'/'coolicons PNG'/'Black'/'Media'
            icons.mkdir(parents=True)
            (icons/'Airplay.png').touch()
        self.assertIn(path, self.plan()[0])

    def test_apply_flag_must_be_spelled_out(self):
        with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                self.job.apply_requested(['--a'])
