from pathlib import Path
import subprocess,json,shutil,os
S=Path(__file__).parent;R=S.parents[1];N='kidsmap-place-acceptance-20261009-8792';Q=Path('/tmp/kidsmap-task33-qa04-place-acceptance-20261009-8792');K=R/'.tmp/kidsmap-task33-qa04-socket-place-acceptance-20261009-8792'
count=subprocess.check_output(['docker','exec',N,'psql','-h','/qa-socket','-U','qa_stage04','-d','qa_stage04','-Atc',"select count(*) from information_schema.tables where table_schema='public'"],text=True).strip();assert count=='0',count
a=subprocess.Popen(['docker','exec','kidsmap-reacceptance-20261009','pg_dump','-h','/qa-socket','-U','qa_stage04','--no-owner','--no-acl','qa_stage04'],stdout=subprocess.PIPE)
b=subprocess.run(['docker','exec','-i',N,'psql','-h','/qa-socket','-U','qa_stage04','-d','qa_stage04','-v','ON_ERROR_STOP=1'],stdin=a.stdout,stdout=subprocess.DEVNULL);a.stdout.close();assert a.wait()==0 and b.returncode==0
oldq=Path('/tmp/kidsmap-task33-qa04-reacceptance-20261009')
for folder in ('media','private-media'):shutil.copytree(oldq/folder,Q/folder,dirs_exist_ok=True)
shutil.copy(oldq/'fixtures.json',Q/'fixtures.json')
env={'PATH':'/usr/bin:/bin:/snap/bin','LANG':'C.UTF-8','PYTHONDONTWRITEBYTECODE':'1','DJANGO_TESTING':'1','DJANGO_SETTINGS_MODULE':'place_qa_settings','DJANGO_SECRET_KEY':'place-qa-synthetic-only','DATABASE_URL':'','LEGACY_DATABASE_URL':'','REDIS_URL':'','GOOGLE_APPLICATION_CREDENTIALS':'','TASK33_QA_ROOT':str(Q),'TASK33_QA_SOCKET':str(K),'TASK33_QA_OUTPUT':str(Q),'KIDSMAP_MANUAL_PORTABLE':'1','KIDSMAP_PREVIEW_PORT':'8792','PYTHONPATH':os.pathsep.join([str(S.resolve()),str(R/'docs/task33/manual-check/qa'),str(R/'docs/task33/qa04'),str(R/'src')])}
(S/'env.json').write_text(json.dumps(env))
with (S/'server.log').open('w') as f:child=subprocess.Popen([str(R/'.venv/bin/python'),str(S/'serve.py')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
(S/'server.pid').write_text(str(child.pid));print({'pid':child.pid,'port':8792})
