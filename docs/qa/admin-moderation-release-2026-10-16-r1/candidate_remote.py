from pathlib import Path
import json,subprocess
manifest = MANIFEST
root=Path('/opt/kidsmap');stage=Path('/opt/kidsmap-releases/admin-moderation-20261016-r1')
extra=stage/'candidate.override.json'
extra.write_text(json.dumps({'services':{'web':{'image':manifest['tag'],'build':{'context':str(stage/'build-context')}}}}));extra.chmod(0o600)
compose=['docker','compose','-p','kidsmap','-f',str(root/'docker-compose.yml'),'-f',str(root/'.tmp/production-release.override.yml'),'-f',str(extra)]
active=json.loads(subprocess.check_output(['docker','inspect','kidsmap-web']))[0]
effective=json.loads(subprocess.check_output(compose+['config','--format','json'],cwd=root,stderr=subprocess.PIPE))['services']['web']
env=dict(x.split('=',1)for x in active['Config']['Env'])
assert all(env.get(k)==str(v)for k,v in effective['environment'].items())
assert {(x['source'],x['target'])for x in effective['volumes']}=={(x['Source'],x['Destination'])for x in active['Mounts']}
program='''
from pathlib import Path
import os,json,hashlib,io,contextlib,gettext
expected=EXPECTED
assert all(hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest()==h for n,h in expected.items())
assert not Path('/app/.env').exists()
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.conf import settings
from django.db import connection,transaction
from django.db.migrations.executor import MigrationExecutor
from django.core.management import call_command
assert not settings.DEBUG and not settings.TESTING
with transaction.atomic():
 with connection.cursor()as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
 ex=MigrationExecutor(connection)
 assert not ex.migration_plan(ex.loader.graph.leaf_nodes())
 with contextlib.redirect_stdout(io.StringIO()):call_command('check',verbosity=0)
translations={};mo={}
for lang in ['ru','az','en']:
 p=Path('/app/locale')/lang/'LC_MESSAGES/django.mo'
 with p.open('rb')as f:t=gettext.GNUTranslations(f)
 translations[lang]={n:t.gettext(n) for n in ['Открыть','Низкая оценка','Риски']}
 mo[str(p.relative_to('/app'))]=hashlib.sha256(p.read_bytes()).hexdigest()
assert translations['en']=={'Открыть':'Open','Низкая оценка':'Low rating','Риски':'Risks'}
print('SAFE_RESULT='+json.dumps({'source_files_match':len(expected),'MO':mo,'translations':translations,'pending_migrations':0,'system_check':True,'production':True,'DEBUG':False,'env_in_image':False,'database_read_only':True}))
'''.replace('EXPECTED',repr(manifest['files']))
p=subprocess.run(compose+['run','--rm','--no-deps','-T','web','python','-'],cwd=root,input=program,capture_output=True,text=True)
(stage/'candidate.stdout').write_text(p.stdout);(stage/'candidate.stderr').write_text(p.stderr)
lines=[x for x in p.stdout.splitlines()if x.startswith('SAFE_RESULT=')]
assert p.returncode==0 and len(lines)==1, 'Candidate preflight failed; restricted output retained'
result=json.loads(lines[0].removeprefix('SAFE_RESULT='));result.update(image=manifest['tag'],env_unchanged=True,mounts_unchanged=True)
(stage/'candidate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
