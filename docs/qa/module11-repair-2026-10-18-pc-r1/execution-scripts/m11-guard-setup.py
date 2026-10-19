"""Own PostgreSQL loopback profile satisfying retained schema-test safety guards."""
import json,subprocess,time
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m11-full-r1';G=Q/'m11-dbguard-r1';O=R/'docs/qa/module11-repair-2026-10-18-pc-r1';run=lambda a:subprocess.check_output(a,text=True).strip();setup=json.loads((O/'evidence/setup.json').read_text());assert run(['docker','inspect','m11full-r1-app','--format','{{.Id}}'])==setup['container_id'];container=G.name+'-pg';volume=G.name+'-data';port=55492;database='m11dbguard_r1';user='m11_guard';assert not G.exists() and container not in run(['docker','ps','-a','--format','{{.Names}}']).splitlines() and volume not in run(['docker','volume','ls','--format','{{.Name}}']).splitlines()
code='import socket;s=socket.socket();s.bind(("127.0.0.1",'+str(port)+'));s.close()';assert subprocess.run(['docker','exec','m11full-r1-app','python','-c',code],capture_output=True).returncode==0
G.mkdir();image=run(['docker','inspect','m09full-r1-pg','--format','{{.Config.Image}}']);cid=run(['docker','run','-d','--name',container,'--network','container:m11full-r1-app','--mount','type=volume,source='+volume+',target=/var/lib/postgresql/data','-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_USER='+user,'-e','POSTGRES_DB='+database,image,'postgres','-p',str(port),'-c','listen_addresses=127.0.0.1'])
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 if subprocess.run(['docker','exec',container,'pg_isready','-h','127.0.0.1','-p',str(port),'-U',user,'-d',database],capture_output=True).returncode==0:break
 time.sleep(.5)
else:raise AssertionError('Owned PostgreSQL readiness timeout; inspect before retry')
config={'container':container,'database':database,'pg_port':port,'user':user};(G/'config.json').write_text(json.dumps(config))
t="""from qa_settings import *
QA_ROOT=__import__('pathlib').Path(%r)
ROOT_URLCONF='config.urls'
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':%r,'USER':%r,'PASSWORD':'','HOST':'127.0.0.1','PORT':%r,'OPTIONS':{'options':'-c statement_timeout=20000 -c lock_timeout=2000'},'TEST':{'NAME':%r}}}
MEDIA_ROOT=QA_ROOT/'test-media'
PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'
CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'m11-dbguard-r1-test'}}
"""%(str(G),database,user,str(port),'test_'+database);(Q/'qa_guard_settings.py').write_text(t)
(O/'evidence/guard-profile-setup.json').write_text(json.dumps({'container':container,'container_id':cid,'volume':volume,'app_network_namespace_only':True,'listens_only127_0_0_1':True,'host_port_published':False,'fresh_database':database,'QA_ROOT':str(G),'independent_media_private_cache':True,'historical_guard_assertions_unchanged':True},indent=2));print('Own loopback PostgreSQL profile ready; retained safety assertions unchanged.')
