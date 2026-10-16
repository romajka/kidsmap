from pathlib import Path
import json,subprocess,hashlib,os
r=Path('/opt/kidsmap');stage=Path('/opt/kidsmap-releases/module08-20261016-r1');tag='kidsmap:module08-cfef63e3';override=r/'.tmp/module08-20261016-r1.override.json';override.write_text(json.dumps({'services':{'web':{'image':tag,'build':{'context':str(stage/'build-context')}}}},indent=2));override.chmod(0o600)
files=[str(r/'docker-compose.yml'),str(r/'.tmp/production-release.override.yml'),str(override)];compose=['docker','compose','-p','kidsmap']
for f in files:compose+=['-f',f]
cfg=json.loads(subprocess.check_output(compose+['config','--format','json'],cwd=r,text=True));active=json.loads(subprocess.check_output(['docker','inspect','kidsmap-web'],text=True))[0];env=dict(x.split('=',1)for x in active['Config']['Env']);new=cfg['services']['web'];delta=[k for k,v in new['environment'].items()if env.get(k)!=str(v)]
assert not delta,delta
expected_mounts={(x['Source'],x['Destination'])for x in active['Mounts']};mounts={(x['source'],x['target'])for x in new['volumes']};assert mounts==expected_mounts
expected=json.loads((stage/'expected-source.json').read_text())
program="""
import os,json,hashlib,contextlib,io
from pathlib import Path
expected=EXPECTED
assert all(hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest()==v for n,v in expected['files'].items())
assert all(hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest()==v for n,v in expected['MO'].items())
assert not Path('/app/.env').exists()
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
import pypdf
from django.conf import settings
from django.utils.translation import override,gettext
from django.db import connection,transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder
from django.core.management import call_command
assert not settings.TESTING and not settings.DEBUG
with transaction.atomic():
 with connection.cursor()as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 ex=MigrationExecutor(connection);pending=ex.migration_plan(ex.loader.graph.leaf_nodes());applied=MigrationRecorder.Migration.objects.count()
 assert not pending
 out=io.StringIO()
 with contextlib.redirect_stdout(out):call_command('check',verbosity=0)
checks={}
for lang in ['ru','az','en']:
 with override(lang):checks[lang]={m:gettext(m)for m in ['Найдено %(count)s карточек','Снятие с публикации...','Публикация карточки...','«%(name)s» опубликована и видна на сайте.','Причина решения']}
print('RELEASE_RESULT='+json.dumps({'source_files_match':len(expected['files']),'MO_files_match':len(expected['MO']),'production':not settings.TESTING,'DEBUG':settings.DEBUG,'django':django.get_version(),'pypdf':pypdf.__version__,'applied_migrations':applied,'pending_migrations':0,'system_check_pass':True,'translations':checks,'private_media_root':str(settings.PRIVATE_MEDIA_ROOT),'private_media_mounted':Path(settings.PRIVATE_MEDIA_ROOT).is_dir(),'env_file_in_image':False}))
""".replace('EXPECTED',repr(expected))
p=subprocess.run(compose+['run','--rm','--no-deps','-T','web','python','-'],cwd=r,input=program,capture_output=True,text=True)
lines=[x for x in p.stdout.splitlines()if x.startswith('RELEASE_RESULT=')]
assert p.returncode==0 and len(lines)==1,('image preflight exit',p.returncode,'result_count',len(lines))
data=json.loads(lines[0].removeprefix('RELEASE_RESULT='));data.update(image=tag,environment_values_unchanged=True,media_private_static_mounts_unchanged=True,compose_files=files)
(stage/'image-preflight.json').write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
