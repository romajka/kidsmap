"""Server-only activation. All raw configuration stays inside mode0700 release directory."""
import fcntl, hashlib, json, os, shutil, subprocess, time, urllib.request
from pathlib import Path
ROOT=Path('/opt/kidsmap-releases/20261102-home-auth')
BEFORE=json.loads((ROOT/'before.json').read_text())
BUILD=json.loads((ROOT/'build.json').read_text())
lock=open('/run/lock/kidsmap-release.lock','w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def output(args):return subprocess.check_output(args,text=True).strip()
def inspect():return json.loads(output(['docker','inspect','kidsmap-web']))[0]
def env(web):return dict(x.split('=',1) for x in web['Config']['Env'])
def envhash(web):return hashlib.sha256(json.dumps(sorted(web['Config']['Env'])).encode()).hexdigest()
def command(cfg,*args):return ['docker','compose','--project-directory','/opt/kidsmap','-p',BEFORE['compose_project'],'-f',str(ROOT/cfg),*args]
def run(args,name):
 with (ROOT/name).open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
def get(path):
 req=urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Host':'kidsmap.az','X-Forwarded-Proto':'https'})
 with urllib.request.urlopen(req,timeout=8) as r:return r.read().decode()
def health():
 for _ in range(45):
  try:
   if json.loads(get('/healthz'))['status']=='ok':return
  except Exception:pass
  time.sleep(1)
 raise RuntimeError('Health unavailable')
web=inspect();assert web['Image']==BEFORE['image_id'];assert envhash(web)==BEFORE['env_hash'];health()
manifest_before=ROOT/'staticfiles.before.json'
assert manifest_before.is_file(), 'Missing rollback static manifest'
manifest_data=json.loads(manifest_before.read_text());assert isinstance(manifest_data.get('paths'),dict) and manifest_data['paths']
assert manifest_before.read_bytes()==Path('/opt/kidsmap/staticfiles/staticfiles.json').read_bytes(), 'Static manifest changed since snapshot'
oldenv=env(web)
assert output(['docker','image','inspect',BUILD['tag'],'--format','{{.Id}}'])==BUILD['image_id']
config=json.loads((ROOT/'previous.compose.json').read_text())
config['services']['web'].pop('build',None)
config['services']['web']['image']=BUILD['tag']
config['services']['web'].setdefault('labels',{})['org.opencontainers.image.revision']=BUILD['revision']
config['services']['web']['ports']=[{'target':8000,'published':'8000','host_ip':'127.0.0.1','protocol':'tcp'}]
config['services']['web'].setdefault('environment',{})['AUTH_THROTTLE_TRUSTED_PROXIES']='172.18.0.1/32'
# Compose interpolates even resolved JSON; escape literals, including secrets containing $.
def escape(value):
 if isinstance(value,str):return value.replace('$','$$')
 if isinstance(value,list):return [escape(x) for x in value]
 if isinstance(value,dict):return {k:escape(v) for k,v in value.items()}
 return value
for name,data in [('candidate.compose.json',config),('rollback.compose.json',json.loads((ROOT/'previous.compose.json').read_text()))]:
 path=ROOT/name;path.write_text(json.dumps(escape(data)));os.chmod(path,0o600)
# Confirm interpolation has preserved every existing environment value.
resolved=json.loads(output(command('candidate.compose.json','config','--format','json')))
oldconfig=json.loads((ROOT/'previous.compose.json').read_text())
expected=dict(oldconfig['services']['web']['environment']);expected['AUTH_THROTTLE_TRUSTED_PROXIES']='172.18.0.1/32'
assert resolved['services']['web']['environment']==expected
for key in set(oldconfig['services']['web']) | set(resolved['services']['web']):
 if key not in {'image','build','ports','environment','labels'}:
  assert resolved['services']['web'].get(key)==oldconfig['services']['web'].get(key), 'Unexpected service change: '+key
expected_labels=dict(oldconfig['services']['web'].get('labels',{}));expected_labels['org.opencontainers.image.revision']=BUILD['revision']
assert resolved['services']['web']['labels']==expected_labels
assert resolved['networks']==oldconfig['networks']
run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','check'),'candidate-check.log')
run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','migrate','--check'),'candidate-migrations.log')
snapshot="""import os,json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from catalog.models import SiteSettings
from django.db import transaction,connection
fields=['home_title_ru','home_title_en','home_title_az','home_subtitle_ru','home_subtitle_en','home_subtitle_az']
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY')
 print(json.dumps(list(SiteSettings.objects.values('id',*fields)),ensure_ascii=False))
"""
copy_before=subprocess.check_output(['docker','exec','-i','kidsmap-web','python','-'],input=snapshot,text=True)
(ROOT/'homepage.before.json').write_text(copy_before)
restore="""import os,json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.db import transaction
from catalog.models import SiteSettings
from catalog.homepage_copy import HOME_COPY_DEFAULTS
rows=json.loads(%r)
with transaction.atomic():
 for row in rows:
  site=SiteSettings.objects.select_for_update().get(pk=row['id']);changed=[]
  for field,new in HOME_COPY_DEFAULTS.items():
   if getattr(site,field)==new and row[field]!=new:setattr(site,field,row[field]);changed.append(field)
  if changed:site.save(update_fields=[*changed,'updated_at'])
""" % copy_before
(ROOT/'restore_homepage.py').write_text(restore)
# Copy update/collection can succeed before a later step fails: mark first.
changed=False;switched=False
try:
 changed=True
 run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','update_homepage_copy'),'homepage-update.log')
 run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','manage.py','collectstatic','--noinput'),'collectstatic.log')
 switched=True
 run(command('candidate.compose.json','up','-d','--no-deps','--no-build','web'),'activation.log')
 health();current=inspect();assert current['Image']==BUILD['image_id']
 assert current['Config']['Labels']['org.opencontainers.image.revision']==BUILD['revision']
 newenv=env(current);expectedenv=dict(oldenv);expectedenv['AUTH_THROTTLE_TRUSTED_PROXIES']='172.18.0.1/32';assert newenv==expectedenv
 mounts=[{k:m.get(k) for k in ('Type','Source','Destination','RW')} for m in current['Mounts']]
 assert sorted(mounts,key=lambda m:m['Destination'])==sorted(BEFORE['mounts'],key=lambda m:m['Destination'])
 assert current['HostConfig']['PortBindings']=={'8000/tcp':[{'HostIp':'127.0.0.1','HostPort':'8000'}]}
 assert current['Config']['Cmd']==BEFORE['command'] and current['Config']['User']==BEFORE['user']
 assert current['NetworkSettings']['Networks']['kidsmap_default']['Gateway']=='172.18.0.1'
 checks=[('/ru/','Места и занятия для детей в Азербайджане'),('/en/','Places and activities for children in Azerbaijan'),('/','Azərbaycanda uşaqlar üçün məkanlar və məşğələlər'),('/ru/catalog/?category=ZOO','Найдено мест: 2'),('/ru/catalog/?category=parks-playgrounds','Найдено мест: 17')]
 for path,text in checks:assert text in get(path),path
 result={'status':'PASS','revision':BUILD['revision'],'image':BUILD['tag'],'image_id':BUILD['image_id'],'health':'ok','http_checks':len(checks),'mounts_preserved':True,'existing_environment_preserved':True,'backend_loopback_only':True,'previous_image':BEFORE['image']}
 (ROOT/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
except BaseException:
 rollback_errors=[]
 if changed:
  try:
   with (ROOT/'restore_homepage.py').open('rb') as source, (ROOT/'rollback-copy.log').open('wb') as log:
    subprocess.run(command('candidate.compose.json','run','--rm','--no-deps','-T','web','python','-'),stdin=source,stdout=log,stderr=subprocess.STDOUT,check=True)
  except Exception:
   rollback_errors.append('homepage_restore')
 try:
  if (ROOT/'staticfiles.before.json').exists():shutil.copy2(ROOT/'staticfiles.before.json','/opt/kidsmap/staticfiles/staticfiles.json')
 except Exception:
  rollback_errors.append('static_manifest_restore')
 try:
  if switched:run(command('rollback.compose.json','up','-d','--no-deps','--no-build','web'),'rollback.log')
 except Exception:
  rollback_errors.append('previous_image_activation')
 try:
  health();assert inspect()['Image']==BEFORE['image_id']
 except Exception:
  rollback_errors.append('previous_image_health')
 (ROOT/'rollback-result.json').write_text(json.dumps({'errors':rollback_errors,'previous_image':BEFORE['image']},indent=2))
 print('ROLLBACK_PASS' if not rollback_errors else 'ROLLBACK_REQUIRES_ATTENTION: '+','.join(rollback_errors))
 raise
