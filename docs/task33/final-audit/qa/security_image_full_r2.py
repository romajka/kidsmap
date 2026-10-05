"""Exact-image full explicit suite runtime, preserving unchanged QA04 launcher/guards."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import shutil

IMAGE='sha256:6566a67c0b3ab3da8ea040314b016908b1cbe17e09a50912fc5c80fe5228f5fd'
ROOT=Path('/root/km28-db')
SOURCE=Path('/mnt/c/kidsmap')
HERE=ROOT/'docs/task33/qa04'
files=['src/catalog/domain_admin/place.py','src/catalog/forms.py','src/catalog/testcases/test_task33_event_admin_precision.py',
       'docs/task33/qa04/run.py','docs/task33/qa04/commands.py','docs/task33/qa04/settings.py','docs/task33/qa04/guard.py']
safe_env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'}
preflight_code="import hashlib,json,sys;from pathlib import Path;print(json.dumps({'python':sys.version.split()[0],'files':{n:hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest() for n in "+repr(files)+"}}))"
probe=subprocess.run(['docker','run','--rm','--pull=never','--network','none','--read-only','--cap-drop=ALL',
    '--security-opt=no-new-privileges','--entrypoint','/usr/local/bin/python',IMAGE,'-c',preflight_code],
    env=safe_env,capture_output=True,text=True,check=True,timeout=60)
preflight=json.loads(probe.stdout)
for name in files:
    assert preflight['files'][name]==hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==hashlib.sha256((SOURCE/name).read_bytes()).hexdigest(),'Exact image/source drift'

spec=importlib.util.spec_from_file_location('image_precision_base',HERE/'run.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original_popen=subprocess.Popen
child_name='kidsmap-task33-image-full-audit-'+uuid.uuid4().hex[:12]
child_nonce=uuid.uuid4().hex
launched=[]
def image_popen(args,**kwargs):
    assert len(args)==5 and args[1]=='-c' and 'commands.main' in args[2], 'Unexpected wrapped child'
    assert args[3]=='all' and all(x.startswith('catalog.testcases.') for x in json.loads(args[4]))
    env=dict(kwargs.pop('env'));kwargs.pop('cwd')
    run=Path(env['TASK33_QA_ROOT']).resolve(strict=True)
    socket=Path(env['TASK33_QA_SOCKET']).resolve(strict=True)
    output=Path(env['TASK33_QA_OUTPUT']).resolve(strict=True)
    assert run.is_relative_to('/tmp') and run.name.startswith('kidsmap-task33-qa04-')
    assert socket.is_relative_to(ROOT/'.tmp') and socket.parent.name.startswith('kidsmap-task33-qa04-socket-')
    assert output.is_relative_to('/tmp') and output.name.startswith('task33-final-audit-image-r2-')
    assert not any(p.is_symlink() for p in (run,socket,output))
    image_socket=Path('/app/.tmp')/socket.parent.name/'socket'
    env.update(PATH='/usr/local/bin:/usr/bin:/bin',PYTHONPATH='/app/docs/task33/qa04:/app/src',TASK33_QA_SOCKET=str(image_socket))
    code="import sys,json;sys.path.insert(0,'/app/src');import commands;sys.exit(commands.main(sys.argv[1],json.loads(sys.argv[2])))"
    command=['docker','run','--rm','--pull=never','--name',child_name,'--label','kidsmap.task33.image-owner='+child_nonce,
        '--network','none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--workdir','/app',
        '--mount',f'type=bind,src={run},dst={run}',
        '--mount',f'type=bind,src={socket.parent},dst={image_socket.parent}',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=256m',
        '--mount',f'type=bind,src={output},dst={output}']
    for key,value in sorted(env.items()): command.extend(['--env',key+'='+value])
    command.extend(['--entrypoint','/usr/local/bin/python',IMAGE,'-c',code,args[3],args[4]])
    launched.append(True)
    return original_popen(command,env=safe_env,**kwargs)
subprocess.Popen=image_popen
# subprocess.run also uses Popen: route its ordinary owned PG/safety commands unchanged.
def dispatch(args,*a,**kw):
    if isinstance(args,list) and len(args)==5 and args[1]=='-c' and 'commands.main' in args[2]:return image_popen(args,**kw)
    return original_popen(args,*a,**kw)
subprocess.Popen=dispatch
try:
    result=base.main()
finally:
    subprocess.Popen=original_popen
    inspect=subprocess.run(['docker','inspect',child_name],env=safe_env,capture_output=True,text=True,timeout=15)
    absent=inspect.returncode!=0
    output=Path(sys.argv[sys.argv.index('--output')+1])
    (output/'image-runtime.json').write_text(json.dumps({'image_id':IMAGE,'source_sha256':preflight['files'],
        'python':preflight['python'],'source_only_image':True,'child_launched':bool(launched),'child_network':'none',
        'child_ports':False,'child_read_only':True,'child_capabilities_dropped':True,'child_daemon_mount':False,
        'child_checkout_mount':False,'owned_qa_binds_only':True,'writable_tmpfs':'/tmp rw,noexec,nosuid,size256m','socket_contract':'/app/.tmp/kidsmap-task33-qa04-socket-*/socket','child_removed':absent},indent=2)+'\n')
    assert absent,'Exact image child retained; no cleanup bypass'
    daemon=subprocess.run(['docker','ps','--all','--filter','label=kidsmap.task33.image-owner='+child_nonce,'--format','{{.ID}}'],env=safe_env,capture_output=True,text=True,check=True,timeout=15)
    assert not daemon.stdout.strip(),'Owned image child remains'
    retained=Path('/root/task33-evidence')/('final-audit-image-r2-preflight-20261004' if '--label' in sys.argv else 'final-audit-image-r2-20261004')
    assert not retained.exists()
    shutil.copytree(output,retained)
sys.exit(result)
