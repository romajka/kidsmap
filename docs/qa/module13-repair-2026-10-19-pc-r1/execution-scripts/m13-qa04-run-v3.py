import json,subprocess,sys,time,re
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';revision=sys.argv[1];kind=sys.argv[2];assert kind in ['targeted','full'];assert re.fullmatch('r[0-9]+',revision)
S=R/('.tmp/m13-qa04-'+revision);assert not S.exists();S.mkdir();profile=S/'profile';profile.mkdir();socketroot=R/('.tmp/kidsmap-task33-qa04-socket-m13-'+revision);assert not socketroot.exists();socket=(socketroot/'socket');socket.mkdir(parents=True)
root='/tmp/kidsmap-task33-qa04-module13-'+revision;app='m13qa04-'+revision+'-app';pg='m13qa04-'+revision+'-pg';sockvol='m13-qa04-'+revision+'-socket';datavol='m13-qa04-'+revision+'-data'
run=lambda a:subprocess.check_output(a,text=True).strip()
names=run(['docker','ps','-a','--format','{{.Names}}']).splitlines();vols=run(['docker','volume','ls','--format','{{.Name}}']).splitlines();assert app not in names and pg not in names and sockvol not in vols and datavol not in vols
image=run(['docker','inspect','m13full-r1-app','--format','{{.Config.Image}}']);pgimage=run(['docker','inspect','m13-full-r1-pg','--format','{{.Config.Image}}'])
cid=run(['docker','run','-d','--name',app,'--network','none','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={profile},target={root}','--mount',f'type=volume,source={sockvol},target={socket}','--entrypoint','python',image,'-c','import time;time.sleep(86400)'])
subprocess.run(['docker','exec',app,'python','-c','import os,sys;os.chmod(sys.argv[1],0o777)',str(socket)],check=True)
pgid=run(['docker','run','-d','--name',pg,'--network','none','--mount',f'type=volume,source={datavol},target=/var/lib/postgresql/data','--mount',f'type=volume,source={sockvol},target={socket}','-e','PGHOST='+str(socket),'-e','POSTGRES_USER=qa_stage04','-e','POSTGRES_DB=qa_stage04','-e','POSTGRES_HOST_AUTH_METHOD=trust',pgimage,'postgres','-p','55494','-c','listen_addresses=','-c','unix_socket_directories=/var/run/postgresql,'+str(socket)])
for _ in range(110):
 if subprocess.run(['docker','exec',pg,'pg_isready','-h',str(socket),'-p','55494','-U','qa_stage04','-d','qa_stage04'],capture_output=True).returncode==0:break
 time.sleep(.5)
else:raise RuntimeError('Owned socket PostgreSQL not ready')
p=subprocess.run(['docker','exec',app,'python','-m','pip','install','--no-index','--no-deps',str(R/'.tmp/m11-full-r1/pypdf-6.20.1-py3-none-any.whl')],capture_output=True,text=True);assert p.returncode==0
labels=[]
if kind=='targeted':
 d=json.loads((O/'evidence/full-backend-r1.json').read_text());labels=[x.split('(',1)[1].rstrip(')') for x in d['failures']+d['errors']]
cmd=['docker','exec',app,'python',str(R/'scripts/run_isolated_quality.py'),'--profile-root',root,'--socket-dir',str(socket),'--port','55494','--source-manifest',str(Q/'expected-source.json'),*labels]
meta={'app':app,'app_id':cid,'pg':pg,'pg_id':pgid,'socket_volume':sockvol,'data_volume':datavol,'root':root,'socket':str(socket),'actual_fresh_resources':True,'network':'none for both containers','labels':labels,'command':cmd}
(S/'setup.json').write_text(json.dumps(meta,indent=2));(O/'evidence'/('qa04-'+revision+'-setup.json')).write_text(json.dumps(meta,indent=2));started=time.monotonic()
with (S/'test.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,text=True)
raw=(S/'test.log').read_text();ids=set(re.findall(r'test_\S+ \((catalog\.[^)]+)\)',raw));result={'command':cmd,'exit':p.returncode,'seconds':round(time.monotonic()-started,3),'unique_methods':len(ids),'ids':sorted(ids),'failures':re.findall(r'^FAIL: ([^\n]+)',raw,re.M),'errors':re.findall(r'^ERROR: ([^\n]+)',raw,re.M),'summary':[l for l in raw.splitlines() if re.match(r'^(Found \d+ test|Ran \d+ tests|FAILED \(|OK$|System check|No changes detected)',l)]}
(O/'evidence'/('qa04-'+revision+'-backend.json')).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['command','ids']},indent=2))
