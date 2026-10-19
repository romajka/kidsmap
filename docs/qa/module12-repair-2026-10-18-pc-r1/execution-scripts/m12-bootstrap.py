import hashlib,json,re,socket,subprocess,time
from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/module11-repair-2026-10-18-pc-r1';O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';Q=R/'.tmp/m12-full-r1';old=R/'.tmp/m11-full-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());run=lambda a:subprocess.check_output(a,text=True).strip()
assert not O.exists() and not Q.exists()
current=read(P/'source-current.json');assert all(sha(R/p)==h for p,h in current['sources'].items())
manifest=read(P/'artifact-manifest.json')['files'];assert all(sha(P/p)==h for p,h in manifest.items())
prior=read(P/'source-entry.json')['prior_packages'];prior[P.name]={**manifest,'artifact-manifest.json':sha(P/'artifact-manifest.json')}
git=lambda *a:run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a]);g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert all(g[k]==current['git'][k] for k in ['head','branch','task33_ref']) and not git('diff','--cached','--name-only')
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
containers=run(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}']).splitlines();assert not any(x.split()[1] in ['m12full-r1-app','m12-full-r1-pg'] for x in containers)
with socket.socket() as sock:sock.bind(('127.0.0.1',33780))
O.mkdir();Q.mkdir()
for folder in ['evidence','stages','png','execution-scripts']:(O/folder).mkdir()
for folder in ['assets','tmp','media','private-media','test-media','test-private-media']:(Q/folder).mkdir()
snapshot={'sources':current['sources'],'prior_packages':prior,'git':g,'shared_mo':{p.relative_to(R).as_posix():sha(p) for p in (R/'locale').rglob('*.mo')},'cbmignore':sha(R/'.cbmignore'),'containers':containers,'documents':{p:sha(R/p) for p in ['docs/qa/continuation-and-repair-prompts-2026-10-11.md','docs/agent-audits/MASTER_AUDIT.md']}}
(O/'source-entry.json').write_text(json.dumps(snapshot,indent=2));(O/'document-current.json').write_text(json.dumps(snapshot['documents'],indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':current['sources']},indent=2))
(O/'evidence/entry-index-note.json').write_text(json.dumps({'previous_module_index_sha256':current['git']['index_sha256'],'current_entry_index_sha256':g['index_sha256'],'same_refs':True,'empty_staging':True,'all1058_source_bytes_match_module11':True,'note':'Binary index differs at initial bootstrap gate before any application or infrastructure write. Metadata/stat refresh possible; exact cause unproven. Current index is the module12 preservation baseline; previous package unchanged.'},indent=2))
(O/'authorization.json').write_text(json.dumps({'request':'Полностью проверить, проанализировать и исправить модуль12, включая новые связанные дефекты, завершить с приёмкой.','scope':'Analytics ingress/access/identity/privacy/storage resilience/periods/reporting/localization and affected public, owner, admin UI. Eight historical findings are checklist, not fresh failures. Concrete stages RED→fix→GREEN within existing authorization.','limits':'No production, real GA access, commit/push/deploy/destructive cleanup. Preserve initial worktree/tests/refs/index/43prior packages and foreign runtimes.','execution':'Root inline, no independent-agent claim.','graph':'C-kidsmap51523nodes280457edges, indexed2026-10-16T18:56:53Z, coverage_unavailable/metadata_changed. Relevant source verified.'},ensure_ascii=False,indent=2))
def adapt(t):
 for a,b in [('m11-full-r1','m12-full-r1'),('m11full-r1','m12full-r1'),('m11full_r1','m12full_r1'),('m11_','m12_'),('M11','M12'),('module11','module12'),('33710','33780')]:t=t.replace(a,b)
 return t
for name in ['proxy.py','playwright.json','seed.py','qa_urls.py']:(Q/name).write_text(adapt((old/name).read_text()))
(O/'browser_driver.py').write_text(adapt((P/'browser_driver.py').read_text()))
t=adapt((old/'qa_settings.py').read_text()).replace("'USER': 'm09full_r1'","'USER': 'm12_guard'").replace("'HOST': 'm09full-r1-pg', 'PORT': '5432'","'HOST': '127.0.0.1', 'PORT': '55493'")
t+="\nMEDIA_ROOT=QA_ROOT/'media'\nLOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=True\nANALYTICS_IDENTITY_HASH_KEY='fictional-module12-disposable-identity-key'\nCSRF_TRUSTED_ORIGINS=[]\nif len(__import__('sys').argv)>1 and __import__('sys').argv[1]=='test':\n MEDIA_ROOT=QA_ROOT/'test-media'\n PRIVATE_MEDIA_ROOT=QA_ROOT/'test-private-media'\n LOCAL_ANALYTICS_STORAGE_ENABLED=OWNER_ANALYTICS_ENABLED=False\n PUBLIC_BASE_URL=''\n ROOT_URLCONF='config.urls'\n"
(Q/'qa_settings.py').write_text(t);(Q/'stage.json').write_text(json.dumps({'locales':'locales-current','test_db':'test_m12full_initial_r1'}))
t=adapt((old/'runtime.py').read_text()).replace("settings.DATABASES['default']['HOST'] == 'm09full-r1-pg'","settings.DATABASES['default']['HOST'] == '127.0.0.1'").replace("str(settings.MEDIA_ROOT)=='/tmp/m12-full-r1-test-media'","str(settings.MEDIA_ROOT)==str(QA/'test-media')")
(Q/'runtime.py').write_text(t)
app='m12full-r1-app';pg='m12-full-r1-pg';volume='m12-full-r1-data';image=run(['docker','inspect','m11full-r1-app','--format','{{.Config.Image}}']);assert volume not in run(['docker','volume','ls','--format','{{.Name}}']).splitlines()
cid=run(['docker','run','-d','--name',app,'--network','m09full-r1-net','--mount',f'type=bind,source={R},target={R},readonly','--mount',f'type=bind,source={Q},target={Q}','--tmpfs','/tmp:rw,size=100663296','--entrypoint','python',image,'-c','import time;time.sleep(86400)'])
pgimage=run(['docker','inspect','m09full-r1-pg','--format','{{.Config.Image}}']);pgid=run(['docker','run','-d','--name',pg,'--network','container:'+app,'--mount','type=volume,source='+volume+',target=/var/lib/postgresql/data','-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_USER=m12_guard','-e','POSTGRES_DB=m12full_r1',pgimage,'postgres','-p','55493','-c','listen_addresses=127.0.0.1'])
for _ in range(110):
 if subprocess.run(['docker','exec',pg,'pg_isready','-h','127.0.0.1','-p','55493','-U','m12_guard','-d','m12full_r1'],capture_output=True).returncode==0:break
 time.sleep(.5)
else:raise AssertionError('Owned PostgreSQL not ready')
(Q/'config.json').write_text(json.dumps({'container':pg,'database':'m12full_r1','pg_port':55493,'user':'m12_guard'}))
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-current'),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);(Q/'locales.log').write_text(p.stdout+p.stderr);assert p.returncode==0
wheel=old/'pypdf-6.20.1-py3-none-any.whl';assert wheel.exists();(O/'evidence/dependency-reference.json').write_text(json.dumps({'declared':'requirements.txt pypdf==6.20.1','wheel_sha256':sha(wheel),'previous_verification':'module11-repair-2026-10-18-pc-r1/evidence/dependency-repair.json'},indent=2))
p=subprocess.run(['docker','exec',app,'python','-m','pip','install','--no-index','--no-deps',str(wheel)],capture_output=True,text=True);(Q/'dependency.log').write_text(p.stdout+p.stderr);assert p.returncode==0
(O/'evidence/setup.json').write_text(json.dumps({'container_id':cid,'pg_container_id':pgid,'app':app,'pg':pg,'normal_db':'m12full_r1','port':33780,'source_count':len(current['sources']),'prior_packages':len(prior),'prior_files':sum(map(len,prior.values())),'locales_command':cmd,'source_RO_own_scratch_RW':True,'PG_loopback_app_namespace_only':True},indent=2))
p=subprocess.run(['docker','exec',app,'python',str(Q/'runtime.py'),'migrate'],capture_output=True,text=True);(Q/'migrate.log').write_text(p.stdout+p.stderr);assert p.returncode==0
print('Module12 fresh isolated app/PG/locales ready; entry1058sources and43prior packages preserved.')
