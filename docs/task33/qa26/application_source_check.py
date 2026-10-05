"""Verify the executed source snapshot against workspace without copying contents."""
import hashlib,json,sys
from pathlib import Path
run=Path(sys.argv[1]);workspace=Path('/mnt/c/kidsmap')
manifest=json.loads((run/'source-sha256.json').read_text())
changed=[];checked=0;generated=[];new_application_files=[]
for name,digest in manifest.items():
 if name.endswith('.mo'):
  generated.append(name);continue
 p=workspace/name
 if p.suffix=='.pyc':continue
 checked+=1
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
for domain in ['src','templates','static','locale','config','scripts']:
 for p in (workspace/domain).rglob('*'):
  if p.is_file()and p.suffix not in {'.pyc','.mo'}and '__pycache__'not in p.parts:
   name=str(p.relative_to(workspace))
   if name not in manifest:new_application_files.append(name)
record={'checked_source_files':checked,'mismatches':changed,'new_application_files':new_application_files,'generated_runtime_locale_files':generated,'source_manifest_sha256':hashlib.sha256((run/'source-sha256.json').read_bytes()).hexdigest()}
(run/'source-current-check.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
if changed or new_application_files:raise SystemExit(1)
