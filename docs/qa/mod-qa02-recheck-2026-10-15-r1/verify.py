import ast,collections,hashlib,json,os,struct,subprocess,sys,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=read(H/'entry.json');checks=[]
def gate(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
git=lambda *a:subprocess.check_output(['git',*a],cwd=R,text=True).strip()
active=[x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]
gate('actual root HEAD branch active_run unchanged',str(R)==e['root']and git('rev-parse','HEAD')==e['head']and git('branch','--show-current')==e['branch']and active==e['active_run'])
changed=[];missing=[]
for path,digest in e['files'].items():
 p=R/path
 if not p.is_file():missing.append(path)
 elif sha(p)!=digest:changed.append(path)
gate('30216entry file hashes preserved except one guide note',len(e['files'])==30216 and changed==['docs/qa/continuation-and-repair-prompts-2026-10-11.md']and not missing,{'changed':changed,'missing':missing})
g=read(H/'guide-edits.json');text=(R/g['path']).read_text();old=text.replace('\n'+g['added_note'],'',1)
gate('exact inverse guide note restores baseline',text.count(g['added_note'])==1 and hashlib.sha256(old.encode()).hexdigest()==g['before_sha256']==e['files'][g['path']])
status=subprocess.check_output(['git','status','--short'],cwd=R,text=True)
gate('dirty entries retained only own QA directory added',set(status.splitlines())==set(e['status'].splitlines())|{'?? docs/qa/'+H.name+'/'})
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0');new=[p for p in paths if p and p not in e['files']and '.env'not in Path(p).name and (R/p).is_file()and not p.startswith('docs/qa/'+H.name+'/')]
gate('no new application or foreign files',not new,new)
containers=[{k:c[k]for k in('ID','Names','Ports','State')}for c in[json.loads(x)for x in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]];byid={c['ID']:c for c in containers};delta=[c['Names']for c in e['containers']if byid.get(c['ID'])!=c];own=[c for c in containers if c['ID']not in {x['ID']for x in e['containers']}]
cfg=read(S/'config.json');gate('66foreign container identities ports states retained only own addition',len(e['containers'])==66 and not delta and [c['Names']for c in own]==[cfg['container']],delta)
procs=[]
for p in e['foreign_processes']:
 try:ok=(Path('/proc')/str(p['pid'])/'cmdline').read_bytes().split(b'\0')[:-1]==[a.encode()for a in p['args']]and str((Path('/proc')/str(p['pid'])/'cwd').resolve())==p['cwd']
 except OSError:ok=False
 procs.append({'pid':p['pid'],'unchanged':ok})
gate('five known foreign HTTP identities retained',len(procs)==5 and all(x['unchanged']for x in procs),procs)
m=read(H/'server.json');proc=Path('/proc')/str(m['pid']);gate('actual own process argv cwd',proc.joinpath('cmdline').read_bytes().split(b'\0')[:-1]==[a.encode()for a in m['argv']]and str((proc/'cwd').resolve())==str(R))
src=json.load(urllib.request.urlopen(m['url']+'/qa/source/',timeout=10));(H/'runtime-source-final.json').write_text(json.dumps(src,indent=2))
pinned=read(H/'runtime-source-baseline.json');gate('actual846bounded source paths equal startup disk pins',len(pinned)==846 and src['source']==pinned and src['startup_matches_disk']and all(sha(R/p)==v for p,v in pinned.items()))
gate('actual authorized module and cached hub detail template origins',src['pid']==m['pid']and src['root']==str(R)and src['template_origin']==str(R/'src/catalog/templates/admin/volunteer/hub_detail.html')and src['loaded_template_sha256']==sha(R/'src/catalog/templates/admin/volunteer/hub_detail.html')and src['loaded_module_paths']=={'views':str(R/'src/catalog/domain_admin/volunteer.py'),'service':str(R/'src/catalog/services/moderation_hub.py')})
manifest=read(H/'locale-manifest.json');ownmo=sorted(str(p.resolve())for p in(S/'locales').rglob('*.mo'));opened=src['actual_opened_MO'];gate('three own locales used and opened by actual process',len(ownmo)==3 and all(p in opened for p in ownmo)and src['sole_locale_paths']==[manifest['locale_root']])
ri=read(H/'runtime-info.json');gate('isolated testing DB cache media private email interpreter',ri['testing']and ri['database']==cfg['database']and ri['database_user']==cfg['user']and ri['interpreter']==m['argv'][0]and ri['migrations']==175 and ri['cache']['BACKEND']=='django.core.cache.backends.locmem.LocMemCache'and all(Path(ri[k]).is_relative_to(S)for k in('media','private_media','email_path'))and not ri['base_code_default_retention_active'])
gate('verified own pypdf byte manifest',all(sha(S/'python-deps'/p)==v for p,v in read(H/'dependency-manifest.json').items())and Path(ri['pypdf_origin']).is_relative_to(S/'python-deps'))
proof=read(H/'fixture-media-proof.json');gate('eight valid synthetic local images',len(proof)==8 and all(x['decodable']and sha(S/'media'/x['name'])==x['sha256']for x in proof))
d=read(H/'native-recheck.js.result.json');counts=collections.Counter(x['status']for x in d['rows']);gate('189control PASS72expected sourceFAIL0NOTRUN',dict(counts)=={'PASS':189,'FAIL':72},dict(counts))
fails=[x for x in d['rows']if x['status']=='FAIL'];cells={(r['role'],r['lang'],r['width'])for r in fails};gate('36actual role locale width cells missing photos/gallery only',len(cells)==36 and set(r['id']for r in fails)=={'current and proposed photos render as eight images','gallery exposes ordered visual preview'}and all(r['detail'].get('actual_images',r['detail'].get('actual_gallery_images'))==0 for r in fails))
langs=[r for r in d['rows']if r['id']=='native language menu selects actual locale'];gate('six real menu locale switches and36actual locale detail assertions',len(langs)==6 and all(r['status']=='PASS'for r in langs)and sum(r['id']=='native queue link opens authorized detail in actual locale'and r['status']=='PASS'for r in d['rows'])==36)
issues=[x for x in d['diagnostics']if x['kind']=='pageerror'or x.get('local')];gate('no unexplained local console network page errors',not issues,issues)
state=json.load(urllib.request.urlopen(m['url']+'/qa/state/',timeout=10));obs=[r for r in d['rows']if r['id']=='read-only detail preserves candidate live and gallery'];gate('candidate live domain unchanged through native audit',len(obs)==1 and obs[0]['detail']['before']==obs[0]['detail']['after']==state==read(H/'state-final.json')and state['pending']==state['places']==state['revisions']==1 and state['live_gallery']==2)
t=(H/'proposed-RED-r2.output.txt').read_text();gate('7proposed methods12expected REDassertions0ERROR',read(H/'proposed-RED-r2.status.json')['exit']==1 and 'Ran 7 tests'in t and 'FAILED (failures=12)'in t and '\nERROR:'not in t and 'FAIL: test_detail_preserves'not in t and 'FAIL: test_anonymous'not in t)
gate('first QA failure retained and assertions not weakened',read(H/'proposed-RED.status.json')['exit']==1 and (H/'proposed-test-first-attempt.py').read_text().replace("        self.url=f'/ru/admin/volunteer/moderation/content/{self.revision.pk}/'","        self.place.refresh_from_db()\n        self.url=f'/ru/admin/volunteer/moderation/content/{self.revision.pk}/'")==(H/'proposed_test_mod_qa02_hub_media.py').read_text())
proposal=read(H/'proposal-manifest.json');bad=[]
for r in proposal:
 target=R/r['target'];p=H/r['proposal']
 if sha(p)!=r['proposal_sha256']or(r['action']=='create'and target.exists())or(r['action']=='modify'and sha(target)!=r['before_sha256']):bad.append(r['target'])
gate('exact seven-file proposed scope NOT APPLIED',len(proposal)==7 and not bad,bad)
gate('proposed permanent test identical to tested RED',sha(H/'proposed/test_mod_qa02_hub_media.py')==sha(H/'proposed_test_mod_qa02_hub_media.py'))
images=read(H/'png-manifest.json');bad=[]
for r in images:
 b=(H/r['path']).read_bytes()
 if sha(H/r['path'])!=r['sha256']or struct.unpack('>II',b[16:24])!=(r['width'],r['height'])or len(b)!=r['bytes']:bad.append(r['path'])
gate('36prepatch PNG hashes dimensions honest selected review',len(images)==36 and not bad and len(read(H/'visual-review.json')['manually_viewed'])==2,bad)
secrets=read(S/'credentials.json').values();leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in{'.py','.js','.json','.jsonl','.md','.txt','.html','.diff'}:
  if any(secret in p.read_text()for secret in secrets):leaks.append(str(p.relative_to(H)))
gate('no own credential strings in public artifacts',not leaks,leaks)
syntax=[]
for p in H.rglob('*.py'):
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax.append(str(p.relative_to(H)))
for p in H.rglob('*.js'):
 if subprocess.run(['node','--check',str(p)],capture_output=True).returncode:syntax.append(str(p.relative_to(H)))
gate('QA and proposed Python JS syntax',not syntax,syntax)
whitespace=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True);gate('worktree diff whitespace',whitespace.returncode==0)
gate('report plan next prompt and diff present',all((H/p).is_file()and (H/p).stat().st_size for p in('REPORT.md','IMPLEMENTATION_PLAN.md','next-prompt.txt','proposed-MOD-QA-02.diff')))
result={'decision':'PLAN COMPLETE / MOD-QA-02 CONFIRMED OPEN'if all(x['pass']for x in checks)else'PLAN VERIFICATION INCOMPLETE','all_checks_pass':all(x['pass']for x in checks),'confirmed_ids':['MOD-QA-02'],'closed_ids':[],'application_changes':[],'implementation_approval':'PENDING exact IMPLEMENTATION_PLAN.md seven-file scope','checks':checks,'native':dict(counts),'main_cells':36,'PNG':len(images),'NOT_RUN':['patch/GREEN','native author upload/approve/reject/public readback','postpatch broken/empty/corrupt/private-document download','full08/global/module09','production/commit/push/deploy']}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'decision':result['decision'],'checks':len(checks),'failed':[x['name']for x in checks if not x['pass']]}));sys.exit(0 if result['all_checks_pass']else 1)
