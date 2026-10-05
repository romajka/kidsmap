"""Freeze only safe current source to an owned native mirror; require exact artifact."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stamp',required=True)
    parser.add_argument('--artifact',required=True)
    options=parser.parse_args()
    if not re.fullmatch('[a-zA-Z0-9-]+',options.stamp):parser.error('Safe stamp required')
    metadata=Path(options.artifact).resolve()
    if not metadata.is_file() or not metadata.is_relative_to(Path('/root/task33-evidence/completion-artifact-c2')):
        parser.error('Exact completion artifact required')
    source=Path('/mnt/c/kidsmap');target=Path('/root/km-completion-recovery')
    output=Path('/tmp/task33-completion-'+options.stamp)
    retained=Path('/root/task33-evidence/completion-'+options.stamp)
    assert not output.exists() and not retained.exists(),'Fresh evidence required'
    target.mkdir(exist_ok=True);lock=target/'.completion-lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
    try:
        scopes=['src','config','catalog','static','templates','locale','docs/task33/qa04','docs/task33/qa23',
            'docs/task33/qa28','docs/task33/completion/qa','manage.py','requirements.txt']
        raw=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard','--',*scopes],cwd=source)
        manifest=[]
        for name in sorted(set(x.decode() for x in raw.split(b'\0') if x)):
            original,destination=source/name,target/name
            if not original.exists():continue
            assert original.is_file() and not original.is_symlink() and destination.resolve().is_relative_to(target.resolve())
            data=original.read_bytes();destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(data)
            manifest.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
        if not (target/'.venv').exists():(target/'.venv').symlink_to('/root/kidsmap-task33/.venv',target_is_directory=True)
        (target/'staticfiles').mkdir(exist_ok=True)
        clean={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
        subprocess.run([str(target/'.venv/bin/python'),'-m','django','compilemessages','--locale','az','--locale','ru','--locale','en','--ignore','.venv'],cwd=target,env=clean,check=True,capture_output=True)
        command=[str(target/'.venv/bin/python'),'docs/task33/completion/qa/domain_recovery_run.py','--mode','probe','--output',str(output)]
        clean['TASK33_COMPLETION_ARTIFACT_JSON']=str(metadata)
        result=subprocess.run(command,cwd=target,env=clean)
        changed=[row['path'] for row in manifest if hashlib.sha256((target/row['path']).read_bytes()).hexdigest()!=row['sha256']]
        retained.parent.mkdir(exist_ok=True)
        if output.exists():shutil.copytree(output,retained)
        else:retained.mkdir()
        (retained/'source.json').write_text(json.dumps({'files':manifest,'frozen_source_changed':changed,'command':command,'artifact':str(metadata)},indent=2)+'\n')
        summary={'evidence':str(retained),'exit':result.returncode,'frozen_source_changed':changed,'source_count':len(manifest)}
        for name in ('run','r2-rehearsal'):
            path=retained/(name+'.json')
            if path.exists():
                data=json.loads(path.read_text())
                summary[name]={k:data[k] for k in ('status','child_exit','cleanup','tables_compared_count','private_files_compared','media_files_compared','compatible_standby_read') if k in data}
        print(json.dumps(summary,indent=2))
        return result.returncode if not changed else 3
    finally:lock.unlink()
if __name__=='__main__':raise SystemExit(main())
