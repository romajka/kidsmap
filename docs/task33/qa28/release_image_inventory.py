"""Enumerate every copied image /app file, including unexpected members/symlinks."""
import json
from pathlib import Path
import artifact

root=Path('/mnt/c/kidsmap/docs/task33/reports')
candidate=json.loads((root/'28-artifact.json').read_text())
image=json.loads((root/'28-release-image-verification.json').read_text())
assert candidate['identity']==image['artifact_identity']
manifest=json.loads(Path(candidate['archive']).with_name('manifest.json').read_text())
copied=Path('/root/task33-evidence/stage28-local-image-verify-release3-20261003/app')
expected={e['path']:e['sha256'] for e in manifest['files']}
actual={p.relative_to(copied).as_posix():artifact.digest(p.read_bytes())
        for p in copied.rglob('*') if p.is_file() and not p.is_symlink()}
symlinks=sorted(p.relative_to(copied).as_posix() for p in copied.rglob('*') if p.is_symlink())
result={'status':'PASS' if expected==actual and not symlinks else 'FAIL',
        'artifact_identity':candidate['identity'],'image_id':image['image_id'],
        'expected_file_count':len(expected),'actual_regular_file_count':len(actual),
        'extra_files':sorted(set(actual)-set(expected)),
        'missing_files':sorted(set(expected)-set(actual)),
        'changed_files':sorted(p for p in set(expected)&set(actual) if expected[p]!=actual[p]),
        'symlinks':symlinks,'source':'actual stopped image /app copy from owned network-none verification container',
        'production':'NOT_CONTACTED'}
(root/'28-release-image-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
assert result['status']=='PASS'
