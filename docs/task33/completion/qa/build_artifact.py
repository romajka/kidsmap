"""Freeze a new data-free local artifact/image; old image and history untouched."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--stamp',required=True)
args=parser.parse_args()
assert re.fullmatch(r'[a-z0-9-]+',args.stamp)
root=Path('/mnt/c/kidsmap')
spec=importlib.util.spec_from_file_location('artifact',root/'docs/task33/completion/qa/artifact.py')
artifact=importlib.util.module_from_spec(spec);spec.loader.exec_module(artifact)
source=Path('/root/km-completion-release-'+args.stamp)
standby=Path('/root/km28-release-completion-'+args.stamp)
out=Path('/root/task33-evidence/completion-artifact-'+args.stamp)
assert not source.exists() and not standby.exists() and not out.exists()
source.mkdir();out.mkdir(parents=True)
paths=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard',
    '--',*artifact.SCOPES,*artifact.ROOT_FILES],cwd=root).split(b'\0')
input_manifest=[]
for raw in sorted(set(paths)):
    if not raw:continue
    name=raw.decode();src=root/name
    if not src.exists():continue
    assert artifact.permitted(name) and src.is_file() and not src.is_symlink()
    target=source/name;target.parent.mkdir(parents=True,exist_ok=True)
    content=src.read_bytes();target.write_bytes(content)
    target.chmod(0o755 if name.endswith('.sh') else 0o644)
    input_manifest.append({'path':name,'sha256':hashlib.sha256(content).hexdigest()})
metadata=artifact.freeze(source,out,standby)
document='docs/product/analytics-event-taxonomy.md'
assert (root/document).is_file()
qa_document=out/'qa-input'/document
qa_document.parent.mkdir(parents=True);qa_document.write_bytes((root/document).read_bytes())
metadata['qa_document']={'path':str(qa_document),'relative_path':document,
    'sha256':hashlib.sha256(qa_document.read_bytes()).hexdigest(),'mount_mode':'read-only'}
home=out/'client-home';home.mkdir()
env={'PATH':'/usr/bin:/bin','HOME':str(home),'DOCKER_BUILDKIT':'0'}
tag='kidsmap-task33-completion:'+metadata['identity'].removeprefix('r2-local-sha256-')
command=['docker','build','--iidfile',str(out/'image.id'),'-t',tag,str(standby)]
with (out/'build.log').open('w') as log:
    build=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
metadata.update(build_exit=build.returncode,tag=tag,source_input_manifest=input_manifest,
    production='NOT_CONTACTED',pushed=False,old_image_preserved=True)
if build.returncode==0:
    info=json.loads(subprocess.check_output(['docker','image','inspect',tag],env=env))[0]
    metadata['image_id']=info['Id']
    assert metadata['image_id']==(out/'image.id').read_text().strip()
artifact.verify(standby,json.loads((Path(metadata['archive']).parent/'manifest.json').read_text()))
(out/'completion-build.json').write_text(json.dumps(metadata,indent=2)+'\n')
(root/'docs/task33/completion/artifact.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({key:metadata.get(key) for key in ('identity','file_count','build_exit','image_id','archive')}))
raise SystemExit(build.returncode)
