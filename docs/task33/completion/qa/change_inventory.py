"""Separate this completion's APP delta from pre-existing dirty WORKTREE edits."""
import hashlib,json,subprocess
from pathlib import Path
root=Path('/mnt/c/kidsmap');out=root/'docs/task33/completion'
entry=json.loads((out/'entry.json').read_text())
backup=root/'scratch'/Path(entry['snapshot'].replace('\\','/')).name/'files'
app=json.loads(Path('/root/task33-evidence/completion-browser-targeted-c4/source.json').read_text())['application']
tracked=set(subprocess.check_output(['git','ls-tree','-r','--name-only',entry['head']],cwd=root,text=True).splitlines())
dirty=set((subprocess.check_output(['git','-c','core.autocrlf=true','diff','--name-only','HEAD','-z'],cwd=root,stderr=subprocess.DEVNULL)+subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=root)).decode().split('\0'))-{''}
rows=[]
for name in sorted(dirty&set(app)):
    saved=backup/name
    before=saved.read_bytes() if saved.exists() else (subprocess.check_output(['git','show',entry['head']+':'+name],cwd=root) if name in tracked else None)
    after=(root/name).read_bytes()
    if before==after:continue
    if before is not None and not saved.exists() and b'\0' not in before and before.replace(b'\r\n',b'\n')==after.replace(b'\r\n',b'\n'):continue
    rows.append({'path':name,'change':'added' if before is None else 'modified',
        'before_sha256':hashlib.sha256(before).hexdigest() if before is not None else None,
        'after_sha256':hashlib.sha256(after).hexdigest(),
        'baseline':'saved dirty entry' if saved.exists() else 'LOCAL HEAD' if before is not None else 'absent at entry'})
(out/'change-inventory.json').write_text(json.dumps({'run':entry['run'],'application_changes':rows,'count':len(rows),'production':'NOT_CONTACTED'},indent=2)+'\n')
print(json.dumps({'completion_APP_changes':len(rows),'added':sum(r['change']=='added' for r in rows)}))
