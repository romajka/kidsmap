from pathlib import Path
import os,json,subprocess,time,hashlib,urllib.request,yaml
r=Path('/opt/kidsmap');stage=Path('/opt/kidsmap-releases/module08-20261016-r1');backup=Path('/opt/kidsmap-release-backups/module08-20261016-r1');primary=r/'.tmp/production-release.override.yml';extra=r/'.tmp/module08-20261016-r1.override.json';tag='kidsmap:module08-cfef63e3';image='sha256:1f2d56ca252808d941c7f0514c268cdcc8d68d0ecacbe3ad5a151132302ede73'
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
old=inspect('kidsmap-web');assert old['Image']=='sha256:e02868b8dbe837425330743a2fc987a2957f3787fd7430a988f75cdc71c1e376'
protected={c['Name']:c['Id']for c in json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-q'],text=True).split()],text=True))if c['Name']!='/kidsmap-web'}
original=primary.read_bytes();assert hashlib.sha256(original).hexdigest()=='edfe912b59bb48a099cd0341fd7151410259e70278e218faf97ef6f9219a7da8';(backup/'production-release.override.yml').write_bytes(original);(backup/'production-release.override.yml').chmod(0o600)
env_sha=hashlib.sha256((r/'.env').read_bytes()).hexdigest();old_env=dict(x.split('=',1)for x in old['Config']['Env'])
compose=['docker','compose','-p','kidsmap','-f',str(r/'docker-compose.yml'),'-f',str(primary)]
def run(name,args):
 started=time.monotonic()
 with(stage/(name+'.log')).open('wb')as out:p=subprocess.run(args,cwd=r,stdout=out,stderr=subprocess.STDOUT)
 return {'name':name,'exit':p.returncode,'seconds':round(time.monotonic()-started,3)}
def health():
 req=urllib.request.Request('http://127.0.0.1:8000/healthz',headers={'Host':'kidsmap.az','X-Forwarded-Proto':'https'})
 try:return urllib.request.urlopen(req,timeout=3).status==200
 except Exception:return False
steps=[];result={}
try:
 steps.append(run('collectstatic',compose+['-f',str(extra),'run','--rm','--no-deps','-T','web','python','manage.py','collectstatic','--noinput']));assert steps[-1]['exit']==0
 cfg=yaml.safe_load(original);cfg['services']['web']['image']=tag;cfg['services']['web']['build']={'context':str(stage/'build-context')}
 replacement=primary.with_name(primary.name+'.module08-new');replacement.write_text(json.dumps(cfg,indent=2));replacement.chmod(0o600);replacement.replace(primary)
 effective=json.loads(subprocess.check_output(compose+['config','--format','json'],cwd=r,text=True))['services']['web']
 assert not[k for k,v in effective['environment'].items()if old_env.get(k)!=str(v)]
 assert {(x['source'],x['target'])for x in effective['volumes']}=={(x['Source'],x['Destination'])for x in old['Mounts']}
 steps.append(run('activate-web',compose+['up','-d','--no-deps','--no-build','web']));assert steps[-1]['exit']==0
 start=time.monotonic()
 for _ in range(90):
  if health():break
  time.sleep(1)
 else:raise RuntimeError('health deadline')
 current=inspect('kidsmap-web');assert current['Image']==image
 assert hashlib.sha256((r/'.env').read_bytes()).hexdigest()==env_sha
 assert all(inspect(n)['Id']==v for n,v in protected.items())
 new_env=dict(x.split('=',1)for x in current['Config']['Env']);assert new_env==old_env
 assert {(x['Source'],x['Destination'])for x in current['Mounts']}=={(x['Source'],x['Destination'])for x in old['Mounts']}
 result={'status':'ACTIVATED','web_id':current['Id'],'image_id':current['Image'],'code_commit':'cfef63e3dbc93e971ac0e2ae963a17a3821ae27c','healthz':200,'readiness_seconds':round(time.monotonic()-start,3),'environment_unchanged':True,'env_file_unchanged':True,'mounts_unchanged':True,'DB_Redis_other_container_IDs_preserved':protected,'schema_data_tasks':'SKIPPED: no model/migration changes, zero pending; no sync_site_defaults','rollback_needed':False,'persistent_compose_files':[str(r/'docker-compose.yml'),str(primary)],'steps':steps}
except BaseException as error:
 primary.write_bytes(original);primary.chmod(0o600)
 steps.append(run('rollback-static',['tar','-xzf',str(backup/'static.tar.gz'),'-C',str(r)]))
 steps.append(run('rollback-web',compose+['up','-d','--no-deps','--no-build','web']))
 result={'status':'ROLLED BACK','error_class':type(error).__name__,'rollback_health':health(),'old_image':old['Image'],'steps':steps,'database_restored':False,'reason':'same schema; current production data preserved'}
(stage/'activation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='ACTIVATED' else 1)
