"""Extract verified artifact into a new exhaustive data-free image context."""
import json
from pathlib import Path
import tarfile
import artifact
import sys

root=Path('/mnt/c/kidsmap')
metadata=json.loads((root/'docs/task33/reports/28-artifact.json').read_text())
archive=Path(metadata['archive']);manifest=json.loads(archive.with_name('manifest.json').read_text())
assert artifact.digest(archive.read_bytes())==metadata['archive_sha256']
target=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/root/km28-image-context')
assert target.is_absolute() and target.parent == Path('/root') and target.name.startswith('km28-image-context')
assert not target.exists();target.mkdir()
expected={e['path']:e for e in manifest['files']};found=set()
with tarfile.open(archive,'r:gz') as tar:
    for member in tar:
        assert member.isfile() and member.name in expected and artifact.permitted(member.name)
        assert member.name not in found;found.add(member.name)
        path=target/member.name;assert path.resolve().is_relative_to(target)
        content=tar.extractfile(member).read();assert artifact.digest(content)==expected[member.name]['sha256']
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);path.chmod(member.mode)
assert found==set(expected)
artifact.verify(target,manifest)
actual={p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}
assert actual==set(expected) and not any(p.is_symlink() for p in target.rglob('*'))
previous=root/'docs/task33/reports/28-release-context.json'
version=sys.argv[2] if len(sys.argv)>2 else 'v1'
assert version in {'v1','v2'}
preserved=root/('docs/task33/reports/28-release-context-'+version+'.json')
assert not preserved.exists();preserved.write_bytes(previous.read_bytes())
result={'status':'PASS','context':str(target),'artifact_identity':metadata['identity'],
        'expected_count':len(expected),'actual_regular_file_count':len(actual),'extra_files':[],
        'missing_files':[],'changed_files':[],'symlinks':[],'verified_before_build':True,
        'original_standby_preserved':True,'production':'NOT_CONTACTED'}
previous.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
