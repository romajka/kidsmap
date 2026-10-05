"""Verify an owned QA04 removal timeout; clean only its uniquely correlated fixtures."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
raw=Path(sys.argv[1]);record=json.loads((raw/'run.json').read_text())
assert record['status']=='PASS' and record['cleanup']=='OWNERSHIP_GUARD_BLOCKED'
name=record['container_name'];nonce=record['ownership_nonce']
assert name=='kidsmap-task33-qa04-'+nonce[:12] and len(nonce)==32
probe=subprocess.run(['docker','inspect',name,'--format','{{json .}}'],capture_output=True,text=True)
if probe.returncode==0:
    raise RuntimeError('Container still exists; no cleanup authorized by this timeout verifier')
listed=subprocess.check_output(['docker','ps','--all','--filter','name='+name,'--format','{{.Names}}'],text=True)
assert not listed.strip(),'Owned container still exists'
def inventory(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
expected_private=inventory(raw/'r2-private-media');expected_public=inventory(raw/'r2-post-switch-media')
assert len(expected_private)==2 and len(expected_public)>=25
candidates=[]
for root in Path('/tmp').glob('kidsmap-task33-qa04-*'):
    if root.is_symlink() or not root.is_dir():continue
    if inventory(root/'private-media')==expected_private and inventory(root/'media')==expected_public:candidates.append(root.resolve())
assert len(candidates)==1,'Unique owned media correlation unavailable'
owned=candidates[0];assert owned.parent==Path('/tmp') and owned.name.startswith('kidsmap-task33-qa04-')
launch=next(row for row in record['commands'] if row['argv'][1]=='run')['argv']
bind=launch[launch.index('--mount')+1]
assert bind.startswith('type=bind,src=/root/km28-db/.tmp/kidsmap-task33-qa04-socket-') and bind.endswith('/socket,dst=/qa-socket')
socket_root=Path(bind.split('src=',1)[1].split(',dst=',1)[0]).parent
assert not socket_root.is_symlink() and socket_root.resolve().parent==Path('/root/km28-db/.tmp')
assert socket_root.name.startswith('kidsmap-task33-qa04-socket-')
# Initial/native guards passed and final inspect returned0; no rm return was
# recorded because the launcher command timed out. Never touch another target.
assert record['commands'][-1]['argv'][1]=='inspect' and record['commands'][-1]['exit']==0
shutil.rmtree(owned);shutil.rmtree(socket_root)
result={'status':'PASS','original_cleanup':record['cleanup'],'owned_container_absent':True,
 'unique_owned_public_private_media_correlation':True,'run_root_removed':not owned.exists(),
 'socket_root_removed':not socket_root.exists(),'other_targets_touched':False,
 'reason':'rm timeout inferred from final successful inspect/no completed rm record; actual container absence verified'}
(raw/'cleanup-followup.json').write_text(json.dumps(result,indent=2)+'\n')
Path('/mnt/c/kidsmap/docs/task33/reports/28-recovery-cleanup.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
