"""Verify the portable payload and actual Git blobs; no Django/runtime access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
parser = argparse.ArgumentParser()
parser.add_argument('--committed', action='store_true')
parser.add_argument('--staged', action='store_true')
args = parser.parse_args()
if args.committed and args.staged:
    parser.error('choose one Git snapshot')
O = Path(__file__).resolve().parent
R = O.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
payload = read(O/'payload-manifest.json')['files']
sources = read(O/'source-current.json')['sources']
expected = dict(payload)
for p, h in sources.items():
    if p in expected:
        assert expected[p] == h, 'conflicting expected source: '+p
    expected[p] = h
for p, h in expected.items():
    assert hashlib.sha256((R/p).read_bytes()).hexdigest() == h, 'file mismatch: '+p
manifest = read(O/'artifact-manifest.json')['files']
assert {p.relative_to(O).as_posix() for p in O.rglob('*') if p.is_file()} == set(manifest)|{'artifact-manifest.json'}
for p, h in manifest.items():
    assert hashlib.sha256((O/p).read_bytes()).hexdigest() == h, 'handoff mismatch: '+p
git = lambda *a: subprocess.check_output(['git','-C',str(R),*a])
assert git('rev-parse','--show-object-format').strip() == b'sha1'
git_files = {}
if args.committed:
    for raw in git('ls-tree','-r','-z','HEAD').split(b'\0'):
        if raw:
            meta, path = raw.split(b'\t',1)
            git_files[path.decode()] = meta.split()[2].decode()
elif args.staged:
    for raw in git('ls-files','--stage','-z').split(b'\0'):
        if raw:
            meta, path = raw.split(b'\t',1)
            assert meta.split()[2] == b'0', 'unmerged index'
            git_files[path.decode()] = meta.split()[1].decode()
if args.committed or args.staged:
    for p in set(expected)|{'docs/qa/'+O.name+'/'+p for p in manifest}|{'docs/qa/'+O.name+'/artifact-manifest.json'}:
        b = (R/p).read_bytes()
        oid = hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
        assert git_files.get(p) == oid, 'Git blob mismatch/missing: '+p
print(json.dumps({'status':'PASS portable Git transfer', 'payload_files':len(payload),
    'source_files':len(sources), 'unique_payload_and_sources':len(expected),
    'handoff_manifest_entries':len(manifest),
    'git_snapshot':'HEAD' if args.committed else 'INDEX' if args.staged else 'not_checked'},indent=2))
