from pathlib import Path
import os,json,subprocess,time,hashlib,urllib.request,yaml,gzip
manifest = MANIFEST
preflight = PREFLIGHT
os.umask(0o077)
r=Path('/opt/kidsmap');stage=Path('/opt/kidsmap-releases/admin-moderation-20261016-r2');backup=Path('/opt/kidsmap-release-backups/admin-moderation-20261016-r2');primary=r/'.tmp/production-release.override.yml';extra=stage/'candidate.override.json';tag=manifest['tag']
built=json.loads((stage/'build.json').read_text());image=built['image_id']
assert json.loads((stage/'candidate.json').read_text())['system_check']
backup.mkdir(parents=True,exist_ok=False)
with (backup/'database.dump').open('wb') as out:
 p=subprocess.run(['docker','exec','kidsmap-postgres','sh','-c','exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom'],stdout=out,stderr=subprocess.PIPE)
assert p.returncode==0,'Backup failed'
with (backup/'database.dump').open('rb') as data:
 p=subprocess.run(['docker','exec','-i','kidsmap-postgres','pg_restore','--list'],stdin=data,capture_output=True)
assert p.returncode==0,'Backup metadata unreadable'
with (backup/'static.tar.gz').open('wb')as out:
 p=subprocess.run(['tar','-czf','-','-C',str(r),'staticfiles'],stdout=out,stderr=subprocess.PIPE)
assert p.returncode==0,'Static backup failed'
with gzip.open(backup/'static.tar.gz','rb')as data:
 while data.read(1024*1024):pass
(backup/'backup.json').write_text(json.dumps({'database_dump_bytes':(backup/'database.dump').stat().st_size,'database_archive_list_readable':True,'static_gzip_integrity':True,'restore_drill':False,'media_modified':False}))
verification_program='\nfrom pathlib import Path\nimport os,json,hashlib,io,contextlib,gettext\nexpected=EXPECTED\nassert all(hashlib.sha256((Path(\'/app\')/n).read_bytes()).hexdigest()==h for n,h in expected.items())\nassert not Path(\'/app/.env\').exists()\nos.environ.setdefault(\'DJANGO_SETTINGS_MODULE\',\'config.settings\')\nimport django;django.setup()\nfrom django.conf import settings\nfrom django.db import connection,transaction\nfrom django.db.migrations.executor import MigrationExecutor\nfrom django.core.management import call_command\nassert not settings.DEBUG and not settings.TESTING\nwith transaction.atomic():\n with connection.cursor()as c:\n  c.execute(\'SET TRANSACTION READ ONLY\');c.execute("SET LOCAL statement_timeout=\'10s\'");c.execute("SET LOCAL lock_timeout=\'2s\'")\n ex=MigrationExecutor(connection)\n assert not ex.migration_plan(ex.loader.graph.leaf_nodes())\n with contextlib.redirect_stdout(io.StringIO()):call_command(\'check\',verbosity=0)\ntranslations={};mo={}\nfor lang in [\'ru\',\'az\',\'en\']:\n p=Path(\'/app/locale\')/lang/\'LC_MESSAGES/django.mo\'\n with p.open(\'rb\')as f:t=gettext.GNUTranslations(f)\n translations[lang]={n:t.gettext(n) for n in [\'Открыть\',\'Низкая оценка\',\'Риски\']}\n mo[str(p.relative_to(\'/app\'))]=hashlib.sha256(p.read_bytes()).hexdigest()\nassert translations[\'en\']=={\'Открыть\':\'Open\',\'Низкая оценка\':\'Low rating\',\'Риски\':\'Risks\'}\nassert mo == EXPECTED_MO\nprint(\'SAFE_RESULT=\'+json.dumps({\'source_files_match\':len(expected),\'MO\':mo,\'translations\':translations,\'pending_migrations\':0,\'system_check\':True,\'production\':True,\'DEBUG\':False,\'env_in_image\':False,\'database_read_only\':True}))\n'.replace('EXPECTED_MO',repr(json.loads((stage/'candidate.json').read_text())['MO'])).replace('EXPECTED',repr(manifest['files']))
def inspect(name):return json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
old=inspect('kidsmap-web');assert old['Image']==preflight['image_id'] and old['Id']==preflight['web_id']
protected={c['Name']:c['Id']for c in json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-q'],text=True).split()],text=True))if c['Name']!='/kidsmap-web'}
original=primary.read_bytes();assert hashlib.sha256(original).hexdigest()==preflight['override_sha256'];(backup/'production-release.override.yml').write_bytes(original);(backup/'production-release.override.yml').chmod(0o600)
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
 replacement=primary.with_name(primary.name+'.admin-moderation-new');replacement.write_text(json.dumps(cfg,indent=2));replacement.chmod(0o600);replacement.replace(primary)
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
 verification=subprocess.run(['docker','exec','-i','kidsmap-web','python','-'],input=verification_program,capture_output=True,text=True)
 (stage/'activation-verification.stdout').write_text(verification.stdout);(stage/'activation-verification.stderr').write_text(verification.stderr)
 assert verification.returncode==0 and 'SAFE_RESULT=' in verification.stdout,'Running source/MO/schema verification failed'
 result={'status':'ACTIVATED','web_id':current['Id'],'image_id':current['Image'],'base_commit':manifest['base_commit'],'patch_sha256':manifest['patch_sha256'],'healthz':200,'readiness_seconds':round(time.monotonic()-start,3),'environment_unchanged':True,'env_file_unchanged':True,'mounts_unchanged':True,'DB_Redis_other_container_IDs_preserved':protected,'schema_data_tasks':'SKIPPED: no model/migration changes, zero pending; no sync_site_defaults','running_source_MO_schema_check':True,'rollback_needed':False,'persistent_compose_files':[str(r/'docker-compose.yml'),str(primary)],'steps':steps}
except BaseException as error:
 primary.write_bytes(original);primary.chmod(0o600)
 steps.append(run('rollback-static',['tar','-xzf',str(backup/'static.tar.gz'),'-C',str(r)]))
 steps.append(run('rollback-web',compose+['up','-d','--no-deps','--no-build','web']))
 rollback_health=False
 for _ in range(60):
  if health():rollback_health=True;break
  time.sleep(1)
 restored=inspect('kidsmap-web')
 rollback_verified=all(x['exit']==0 for x in steps[-2:]) and rollback_health and restored['Image']==old['Image'] and dict(x.split('=',1)for x in restored['Config']['Env'])==old_env and all(inspect(n)['Id']==v for n,v in protected.items()) and hashlib.sha256((r/'.env').read_bytes()).hexdigest()==env_sha and {(x['Source'],x['Destination'])for x in restored['Mounts']}=={(x['Source'],x['Destination'])for x in old['Mounts']}
 result={'status':'ROLLED BACK VERIFIED' if rollback_verified else 'ROLLBACK FAILED','error_class':type(error).__name__,'rollback_health':rollback_health,'old_image':old['Image'],'rollback_verified':rollback_verified,'steps':steps,'database_restored':False,'reason':'same schema; production data preserved'}
(stage/'activation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='ACTIVATED' else 1)
