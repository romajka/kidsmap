"""One-time, audited transition from the 16 November overlay to a full Git image.

The ordinary runner continues to reject all uncommitted overlays. This recipe
accepts only one immutable image, its exact nine audited differences, and a
candidate retaining all three previously deployed analytics files byte-for-byte.
Run from the tested commit's extracted source tree, with the normal --root/SHA.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import deploy_server
from scripts.deploy_server import Release, require

BASE_IMAGE = 'sha256:f351ed0a3665a3862306ff80890ed113456749f98a9ef0b1aa3366e47df5d5bc'
BASE_REVISION = '66badd5370a0dc183c4884eae229890aca67b4c1'
DRIFT = json.loads(Path(__file__).with_name('baseline-drift.json').read_text())


class AttestedRelease(Release):
    def verify_baseline_source(self, revision):
        require(revision == BASE_REVISION and self.inspect()['Image'] == BASE_IMAGE,
                'Transition only accepts the audited immutable baseline')
        try:
            super().verify_baseline_source(revision)
        except RuntimeError as error:
            require(str(error) == 'Running image contains uncommitted overlays; reconcile them before release',
                    'Unexpected baseline verification failure')
        else:
            raise RuntimeError('Expected audited overlay is absent')
        differences = json.loads((self.directory / 'baseline-source-drift.json').read_text())
        require(set(differences) == set(DRIFT), 'Unlisted or missing baseline differences')
        probe = """import hashlib,json,pathlib,sys
result={}
for name in json.load(sys.stdin):
    path=pathlib.Path('/app',name)
    if not path.exists(): result[name]=None; continue
    data=path.read_bytes()
    result[name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\\0'+data).hexdigest()
print(json.dumps(result))
"""
        actual = json.loads(self.command(['docker', 'exec', '-i', 'kidsmap-web', 'python', '-c', probe],
                                         input=json.dumps(list(DRIFT)).encode()))
        for path, row in DRIFT.items():
            require(actual.get(path) == row['live'], 'Audited baseline bytes changed')
            require(self.command(['git', 'rev-parse', revision + ':' + path]) == row['git'],
                    'Baseline Git content changed')
            if row['live'] is not None:
                require(self.command(['git', 'rev-parse', self.target_revision + ':' + path]) == row['live'],
                        'Candidate would discard deployed analytics changes')

    def prepare(self, revision):
        self.target_revision = revision
        super().prepare(revision)
        # Validate the entire clean image before activation without DB/network access.
        verifier = Release(self.root, self.directory)
        def candidate_command(args, **kwargs):
            if args[:2] == ['docker', 'exec']:
                args = ['docker', 'run', '--rm', '--network', 'none', '-i',
                        '--entrypoint', 'python', self.state['candidate_image'], *args[5:]]
            return self.command(args, **kwargs)
        verifier.command = candidate_command
        verifier.verify_baseline_source(revision)

    def smoke(self):
        super().smoke()
        # Post-activation source parity becomes the next ordinary release's baseline.
        Release.verify_baseline_source(self, self.state['revision'])


if __name__ == '__main__':
    deploy_server.Release = AttestedRelease
    sys.exit(deploy_server.main())
