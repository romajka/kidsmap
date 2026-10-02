#!/usr/bin/env python3
"""One-shot disposable QA; never reuse project services, env or production DB."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def clean_environment(run_root):
    return {'PATH':'/usr/bin:/bin:/snap/bin','HOME':str(run_root/'home'),'TMPDIR':str(run_root/'temp'),'LANG':'C.UTF-8','PYTHONPATH':str(HERE)+os.pathsep+str(ROOT/'src'),'PYTHONDONTWRITEBYTECODE':'1','DJANGO_SETTINGS_MODULE':'settings','DJANGO_TESTING':'1','DJANGO_DEBUG':'1','DJANGO_SECRET_KEY':'task33-isolated-synthetic-secret-not-for-production','DATABASE_URL':'','LEGACY_DATABASE_URL':'','REDIS_URL':'','EMAIL_BACKEND':'django.core.mail.backends.locmem.EmailBackend','GOOGLE_APPLICATION_CREDENTIALS':'','TASK33_QA_ROOT':str(run_root)}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['all','discovery','probe'],default='all');parser.add_argument('--output',required=True);parser.add_argument('--label',action='append',default=[]);options=parser.parse_args()
    if options.label and (options.mode!='all' or any(not label.startswith('catalog.testcases.')for label in options.label)):parser.error('Labels require all mode and canonical catalog.testcases prefix')
    raw_output=Path(options.output)
    if raw_output.is_symlink():raise RuntimeError('Symlink output forbidden')
    output=raw_output.resolve()
    if not str(output).startswith('/tmp/')or output.is_symlink():raise RuntimeError('Raw QA outputs must be in /tmp, never repository')
    if output.exists()and any(output.iterdir()):raise RuntimeError('Use a new empty QA output directory; stale results forbidden')
    output.mkdir(parents=True,exist_ok=True)
    python=ROOT/'.venv/bin/python'
    if not python.is_file():raise RuntimeError('Existing project .venv required; no dependency installation')
    docker=shutil.which('docker')
    if not docker:raise RuntimeError('Docker unavailable; PostgreSQL baseline NOT_RUN')
    run_root=Path(tempfile.mkdtemp(prefix='kidsmap-task33-qa04-'));(ROOT/'.tmp').mkdir(exist_ok=True)
    socket_root=Path(tempfile.mkdtemp(prefix='kidsmap-task33-qa04-socket-',dir=ROOT/'.tmp'))
    socket_dir=socket_root/'socket';socket_dir.mkdir();socket_dir.chmod(0o777)
    nonce=uuid.uuid4().hex;name='kidsmap-task33-qa04-'+nonce[:12]
    for p in ['socket','media','home','temp']:(run_root/p).mkdir()
    (run_root/'socket').chmod(0o777)
    env=clean_environment(run_root);env['TASK33_QA_OUTPUT']=str(output);env['TASK33_QA_SOCKET']=str(socket_dir)
    if len(str(socket_dir)+ '/.s.PGSQL.5432')>=104:raise RuntimeError('Unix socket path exceeds safe limit')
    record={'mode':options.mode,'selected_labels':options.label,'status':'RUNNING','container_name':name,'ownership_nonce':nonce,'commands':[],'cleanup':'NOT_RUN'}
    container_id=None
    def command(args,**kwargs):
        done=subprocess.run(args,env=env,cwd=ROOT,capture_output=True,text=True,**kwargs)
        record['commands'].append({'argv':args,'exit':done.returncode})
        return done
    def own():
        result=command([docker,'inspect',name,'--format','{{json .}}'],timeout=15)
        if result.returncode:raise RuntimeError('Owned QA container unavailable')
        info=json.loads(result.stdout)
        if info['Config']['Labels'].get('kidsmap.task33.owner')!=nonce:raise RuntimeError('Container ownership mismatch')
        assert info['HostConfig']['NetworkMode']=='none'and not info['HostConfig']['PortBindings']
        assert '/var/lib/postgresql/data'in info['HostConfig']['Tmpfs']
        binds=[x for x in info['Mounts']if x['Type']=='bind']
        assert len(binds)==1 and binds[0]['Source']==str(socket_dir)and binds[0]['Destination']=='/qa-socket'
        return info
    try:
        safety=command([str(python),str(HERE/'test_safety.py')],timeout=30)
        (output/'safety.log').write_text(safety.stdout+safety.stderr)
        if safety.returncode:raise RuntimeError('Safety tests failed; no database started')
        result=command([docker,'run','--detach','--pull=never','--name',name,'--label','kidsmap.task33.owner='+nonce,'--network','none','--tmpfs','/var/lib/postgresql/data:rw','--mount','type=bind,src='+str(socket_dir)+',dst=/qa-socket','--env','POSTGRES_USER=qa_stage04','--env','POSTGRES_DB=qa_stage04','--env','POSTGRES_HOST_AUTH_METHOD=trust','--env','PGHOST=/qa-socket','postgres:17-alpine','postgres','-c','listen_addresses=','-c','unix_socket_directories=/qa-socket,/var/run/postgresql'],timeout=60)
        if result.returncode:
            (output/'docker-launch.log').write_text(result.stdout+result.stderr)
            raise RuntimeError('Disposable PostgreSQL container launch failed')
        container_id=result.stdout.strip();info=own();record['image_id']=info['Image'];record['network']='none';record['ports_published']=False;record['postgres_data']='tmpfs';record['mounted_checkout']=False
        ready=False
        for _ in range(40):
            p=command([docker,'exec',name,'sh','-c','test "$(cat /proc/1/comm)" = postgres && pg_isready -h /qa-socket -U qa_stage04 -d qa_stage04'],timeout=10)
            if p.returncode==0:ready=True;break
            time.sleep(.25)
        if not ready:
            logs=command([docker,'logs','--tail','30',name],timeout=15)
            (output/'postgres-bootstrap.log').write_text(logs.stdout+logs.stderr)
            raise RuntimeError('Disposable PostgreSQL readiness failed')
        own()
        code="import sys;sys.path.insert(0,"+repr(str(ROOT/"src"))+");import commands,json;sys.exit(commands.main(sys.argv[1],json.loads(sys.argv[2])))"
        with (output/'django.log').open('w')as log:
            process=subprocess.Popen([str(python),'-c',code,options.mode,json.dumps(options.label)],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            try:result_code=process.wait()
            except BaseException:process.terminate();process.wait(timeout=15);raise
        record['commands'].append({'argv':[str(python),'-c','commands.main(mode,labels)',options.mode,json.dumps(options.label)],'exit':result_code})
        record['status']='PASS' if result_code==0 else ('BASELINE_FAILURE' if (output/'suite-results.json').exists() else 'ENVIRONMENT_FAILURE');record['child_exit']=result_code
        print(json.dumps({'mode':options.mode,'child_exit':result_code,'status':record['status'],'output':str(output)}))
    except BaseException as e:
        record['status']='ENVIRONMENT_FAILURE';record['exception']=type(e).__name__;print('QA environment failure; sanitized summary saved',file=sys.stderr);result_code=2
    finally:
        if container_id:
            try:
                own();removed=command([docker,'rm','--force',container_id],timeout=30);record['cleanup']='PASS'if removed.returncode==0 else'FAILED'
            except Exception:record['cleanup']='OWNERSHIP_GUARD_BLOCKED'
        if record['cleanup']=='PASS' or not container_id:
            shutil.rmtree(run_root);shutil.rmtree(socket_root)
        record['run_root_removed']=not run_root.exists();record['socket_root_removed']=not socket_root.exists()
        (output/'run.json').write_text(json.dumps(record,indent=2)+'\n')
    return result_code

if __name__=='__main__':sys.exit(main())
