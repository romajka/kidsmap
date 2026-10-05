"""Exhaustive actual standby entries, including files outside artifact allowlist."""
import hashlib
import json
from pathlib import Path

root=Path('/mnt/c/kidsmap')
metadata=json.loads((root/'docs/task33/reports/28-artifact.json').read_text())
manifest=json.loads((Path(metadata['archive']).parent/'manifest.json').read_text())
standby=Path(metadata['standby'])
expected={e['path']:e['sha256'] for e in manifest['files']}
actual={};symlinks=[]
for path in standby.rglob('*'):
    relative=path.relative_to(standby).as_posix()
    if path.is_symlink():symlinks.append(relative)
    elif path.is_file():actual[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
extra=sorted(set(actual)-set(expected));missing=sorted(set(expected)-set(actual))
changed=sorted(p for p in actual.keys()&expected.keys() if actual[p]!=expected[p])
result={'status':'PASS' if not(extra or missing or changed or symlinks) else 'FAIL',
        'standby':str(standby),'artifact_identity':metadata['identity'],'expected_count':len(expected),
        'actual_regular_file_count':len(actual),'extra_files':extra,'missing_files':missing,
        'changed_files':changed,'symlinks':symlinks,'application_started':False,'production':'NOT_CONTACTED'}
(root/'docs/task33/reports/28-release-context.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
