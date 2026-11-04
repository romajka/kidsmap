"""Bounded production overlay; secrets remain in server-only rollback files."""
import fcntl,hashlib,json,os,shutil,subprocess,time,urllib.request
from pathlib import Path
os.umask(0o077)
R=Path('/opt/kidsmap-releases/20261104-image-seo')
BASE='kidsmap:release-20261102-945db451455e'
BASE_ID='sha256:45410c646e3aaec4a0c7476377fbffeb96efa830d7694e7730e515d31196430c'
lock=open('/run/lock/kidsmap-release.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def output(args):return subprocess.check_output(args,text=True).strip()
def inspect():return json.loads(output(['docker','inspect','kidsmap-web']))[0]
def run(args,name):
 with (R/name).open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
def envhash(w):return hashlib.sha256(json.dumps(sorted(w['Config']['Env'])).encode()).hexdigest()
def mounts(w):return sorted([{k:m.get(k) for k in ('Type','Source','Destination','RW')} for m in w['Mounts']],key=lambda m:m['Destination'])
def get(path):
 req=urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Host':'kidsmap.az','X-Forwarded-Proto':'https'})
 with urllib.request.urlopen(req,timeout=8) as r:return r.read().decode()
def health():
 for _ in range(45):
  try:
   if json.loads(get('/healthz'))['status']=='ok':return
  except Exception:pass
  time.sleep(1)
 raise RuntimeError('Health check failed')
def escape(v):
 if isinstance(v,str):return v.replace('$','$$')
 if isinstance(v,list):return [escape(x) for x in v]
 if isinstance(v,dict):return {k:escape(x) for k,x in v.items()}
 return v
before=inspect();assert before['Image']==BASE_ID
assert output(['docker','image','inspect',BASE,'--format','{{.Id}}'])==BASE_ID
health()
labels=before['Config']['Labels'];project=labels['com.docker.compose.project']
active=labels['com.docker.compose.project.config_files'].split(',')
compose=['docker','compose','--project-directory',labels['com.docker.compose.project.working_dir'],'-p',project]
for f in active:compose+=['-f',f]
previous=json.loads(output(compose+['config','--format','json']))
(R/'previous.compose.json').write_text(json.dumps(previous))
(R/'container.before.json').write_text(json.dumps(before))
shutil.copy2('/opt/kidsmap/staticfiles/staticfiles.json',R/'staticfiles.before.json')
manifest=json.loads((R/'manifest.json').read_text())
# The source baseline must still be exactly the inspected release.
verify="import hashlib,json,pathlib; rows=json.loads("+repr(json.dumps(manifest))+"); print(json.dumps({r['path']:hashlib.sha256(pathlib.Path('/app',r['path']).read_bytes()).hexdigest() if pathlib.Path('/app',r['path']).exists() else None for r in rows}))"
actual=json.loads(output(['docker','exec','kidsmap-web','python','-c',verify]))
assert all(actual[r['path']]==r['before'] for r in manifest),'Source baseline drift'
patchhash=hashlib.sha256((R/'manifest.json').read_bytes()).hexdigest()
tag='kidsmap:image-seo-20261104-'+patchhash[:12]
(R/'Dockerfile').write_text('FROM '+BASE+'\nCOPY overlay/ /app/\nLABEL io.kidsmap.patch.sha256="'+patchhash+'"\nLABEL io.kidsmap.release="20261104-image-seo"\n')
(R/'.dockerignore').write_text('*\n!Dockerfile\n!overlay/\n!overlay/**\n')
run(['docker','build','-t',tag,str(R)],'build.log')
imageid=output(['docker','image','inspect',tag,'--format','{{.Id}}'])
candidate=json.loads(json.dumps(previous));candidate['services']['web'].pop('build',None);candidate['services']['web']['image']=tag
for name,cfg in [('candidate.compose.json',candidate),('rollback.compose.json',previous)]:
 (R/name).write_text(json.dumps(escape(cfg)));os.chmod(R/name,0o600)
def command(cfg,*args):return ['docker','compose','--project-directory','/opt/kidsmap','-p',project,'-f',str(R/cfg),*args]
resolved=json.loads(output(command('candidate.compose.json','config','--format','json')))
for key in set(previous['services']['web'])|set(resolved['services']['web']):
 if key not in {'image','build'}:assert previous['services']['web'].get(key)==resolved['services']['web'].get(key),'Changed service property '+key
for key in ('networks','volumes'):assert previous.get(key)==resolved.get(key)
run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','check'),'check.log')
run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','migrate','--check'),'migrations.log')
# Nothing in this release mutates application records or schema.
others=output(['docker','ps','--format','{{.ID}} {{.Names}}'])
(R/'services.before.txt').write_text(others)
changed=False;switched=False
try:
 assert inspect()['Id']==before['Id'],'Concurrent activation'
 changed=True
 run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','collectstatic','--noinput'),'collectstatic.log')
 switched=True
 run(command('candidate.compose.json','up','-d','--no-deps','--no-build','web'),'activation.log')
 health();current=inspect();assert current['Image']==imageid
 assert envhash(current)==envhash(before),'Environment changed'
 assert mounts(current)==mounts(before),'Mounts changed'
 for prop in ('Cmd','User','Entrypoint'):assert current['Config'][prop]==before['Config'][prop]
 assert current['HostConfig']['PortBindings']==before['HostConfig']['PortBindings']
 actual=json.loads(output(['docker','exec','kidsmap-web','python','-c',verify]))
 assert all(actual[r['path']]==r['after'] for r in manifest),'Source hash mismatch'
 for prefix in ('','/ru','/en'):
  home=get(prefix+'/');assert 'primaryImageOfPage' in home
  guide=get(prefix+'/parents/baku-with-kids/');assert 'og:image:width' in guide and 'primaryImageOfPage' in guide and '1536' in guide
  get(prefix+'/catalog/')
 result={'status':'PASS','image':tag,'image_id':imageid,'base_image':BASE,'base_revision':labels.get('org.opencontainers.image.revision'),'patch_sha256':patchhash,'changed_files':len(manifest),'health':'ok','environment_preserved':True,'mounts_preserved':True,'ports_preserved':True,'schema_migrations_applied':False,'rollback_directory':str(R)}
 (R/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
except BaseException as error:
 failures=[]
 try:
  if changed:shutil.copy2(R/'staticfiles.before.json','/opt/kidsmap/staticfiles/staticfiles.json')
 except Exception:failures.append('static_manifest')
 try:
  if switched:run(command('rollback.compose.json','up','-d','--no-deps','--no-build','web'),'rollback.log')
  health();assert inspect()['Image']==BASE_ID
 except Exception:failures.append('previous_image_health')
 (R/'rollback-result.json').write_text(json.dumps({'errors':failures,'error_type':type(error).__name__}))
 print(json.dumps({'status':'FAILED','error_type':type(error).__name__,'rollback_errors':failures}),flush=True)
 raise SystemExit(1)
