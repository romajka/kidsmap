"""Scoped evidence gate for the explicitly approved MOD-QA-01 repair."""
import collections,datetime,hashlib,importlib.util,json,re,struct,subprocess,sys,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;O=R/'docs/qa/mod-qa01-recheck-2026-10-15-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();checks=[]
def gate(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
def cmd(argv):return subprocess.check_output(argv,cwd=R,text=True)
e=read(H/'entry.json');g=read(H/'guide-edits.json');approval=read(H/'approval.json');template='src/catalog/templates/admin/volunteer/hub_index.html';test='src/catalog/testcases/test_mod_qa01_hub_pagination.py'
head=cmd(['git','rev-parse','HEAD']).strip();branch=cmd(['git','branch','--show-current']).strip();active=[x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]
gate('root HEAD branch active_run unchanged',str(R.resolve())==e['root']and head==e['head']and branch==e['branch']and active==e['active_run'],{'root':str(R),'head':head,'branch':branch,'active_run':active})
changed=[];missing=[]
for p,d in e['files'].items():
 if not(R/p).is_file():missing.append(p)
 elif sha(R/p)!=d:changed.append(p)
gate('30000entry project files preserved except approved template/current08 status',len(e['files'])==30000 and set(changed)=={template,g['path']}and not missing,{'changed':changed,'missing':missing})
lines=(R/template).read_text().splitlines(True);start=next(i for i,x in enumerate(lines)if x=='{% if page.has_other_pages %}\n');inverse=''.join(lines[:start]+lines[start+7:]);gate('exact approved template seven lines inverse and75line test byte match',hashlib.sha256(inverse.encode()).hexdigest()==e['files'][template]==sha(H/'hub-before.html')and(R/template).read_bytes()==(O/'proposed-hub_index.html').read_bytes()and(R/test).read_bytes()==(O/'proposed-test_mod_qa01_hub_pagination.py').read_bytes()and len((R/test).read_text().splitlines())==75)
gate('approved plan/diff hashes still exact',sha(O/'IMPLEMENTATION_PLAN.md')==approval['plan_sha256']and sha(O/'proposed-MOD-QA-01.diff')==approval['diff_sha256'])
text=(R/g['path']).read_text()
for edit in reversed(g['edits']):assert text.count(edit['after'])==1;text=text.replace(edit['after'],edit['before'],1)
gate('exact inverse two guide status edits preserves history',len(g['edits'])==2 and hashlib.sha256(text.encode()).hexdigest()==e['files'][g['path']]==g['before_sha256'])
paths=cmd(['git','ls-files','-c','-o','--exclude-standard','-z']).split('\0');now={p for p in paths if p and '.env'not in Path(p).name and(R/p).is_file()and not p.startswith('docs/qa/'+H.name+'/')};now.update(str(p.relative_to(R))for p in R.glob('locale/*/LC_MESSAGES/*.mo'))
gate('sole new application file is approved regression',now-set(e['files'])=={test}and not(set(e['files'])-now),{'new':sorted(now-set(e['files']))})
status=set(cmd(['git','status','--short']).splitlines());beforestatus=set(e['status'].splitlines());gate('dirty entries retained with only approved app additions',status==beforestatus|{' M '+template,'?? '+test})
shared=[p for p in e['files']if p.startswith('locale/')and p.endswith('.mo')];gate('shared MO untouched',len(shared)>=3 and all(sha(R/p)==e['files'][p]for p in shared))
process=[]
for b in e['foreign_processes']:
 p=Path('/proc')/str(b['pid'])
 try:a={'pid':b['pid'],'args':[x.decode()for x in(p/'cmdline').read_bytes().split(b'\0')if x],'cwd':str((p/'cwd').resolve())};ok=a==b
 except OSError:ok=False
 process.append({'pid':b['pid'],'identity_unchanged':ok})
gate('four known foreign HTTP identities retained',len(process)==4 and all(p['identity_unchanged']for p in process),process)
containers=[json.loads(x)for x in cmd(['docker','ps','-a','--format','json']).splitlines()];byid={x['ID']:x for x in containers};bad=[]
for b in e['containers']:
 a={k:byid.get(b['ID'],{}).get(k)for k in('ID','Names','Ports','State')}
 if a!=b:bad.append({'before':b,'after':a})
new=[c['Names']for c in containers if c['ID']not in{b['ID']for b in e['containers']}]
gate('65foreign container ID name ports state preserved only own addition',len(e['containers'])==65 and not bad and new==[H.name+'-pg'],{'changes':bad,'new':new})
meta=read(H/'server.json');proc=Path('/proc')/str(meta['pid']);argv=[x.decode()for x in(proc/'cmdline').read_bytes().split(b'\0')if x];gate('actual own current interpreter argv cwd',argv==meta['argv']and argv[0]==str(S/'venv/bin/python')and(proc/'cwd').resolve()==R,meta)
source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=15));(H/'runtime-source-final.json').write_text(json.dumps(source,ensure_ascii=False,indent=2));pins=read(H/'runtime-source-baseline.json')
gate('944current application sources equal actual startup and pinned disk',len(pins)==944 and pins==source['source']and source['startup_matches_disk']and source['pid']==meta['pid']and all(sha(R/p)==d for p,d in pins.items())and all(d==e['files'][p]for p,d in pins.items()if p not in{template,test}))
gate('actual cached patched hub template and app module origins',source['template_origin']==str(R/template)and source['loaded_template_sha256']==sha(R/template)and source['loaded_module_paths']=={'views':str(R/'src/catalog/domain_admin/volunteer.py'),'service':str(R/'src/catalog/services/moderation_hub.py')})
spec=importlib.util.spec_from_file_location('isolated_builder_verify',R/'scripts/build_isolated_locales.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);manifest=builder.verify(S/'locales/manifest.json',R/'locale')
gate('fresh current RU AZ EN sole locales and actual own MO opened',manifest==read(H/'locale-manifest.json')and manifest['locales']==['ru','az','en']and source['sole_locale_paths']==[manifest['locale_root']]and all(str(Path(manifest['locale_root'])/l/'LC_MESSAGES/django.mo')in source['actual_opened_MO']for l in('ru','az','en')))
info=read(H/'runtime-info.json');gate('own testing DB cache media email clean env inactive default retention',info['testing']and source['testing']and not source['env_loaded']and info['database']==info['database_user']=='mod01_fix_r1'and info['cache']['LOCATION']==H.name and info['email_backend']=='qa_mail.EmailBackend'and all(Path(info[k]).is_relative_to(S)for k in('media','private_media','email_path'))and info['base_code_default_retention_active']is False and(S.stat().st_mode&0o777)==0o700 and((S/'credentials.json').stat().st_mode&0o777)==0o600)
gate('own exact dependency bytes and interpreter',source['dependency_pypdf']=={'version':'6.20.1','origin':str(S/'python-deps/pypdf/__init__.py')}and info['interpreter']==str(S/'venv/bin/python')and all(sha(S/'python-deps'/p)==d for p,d in read(H/'dependency-manifest.json').items()))
red=(H/'regression-RED.output.txt').read_text();nred=read(H/'native-RED.js.result.json');green=(H/'target-GREEN.output.txt').read_text();gate('fresh four-method6subtest sourceRED and native absent pager before patch',read(H/'regression-RED.status.json')['exit']==1 and 'Ran 4 tests'in red and 'FAILED (failures=6)'in red and red.count('\nFAIL: ')==6 and '\nERROR:'not in red and dict(collections.Counter(r['status']for r in nred['rows']))=={'PASS':4,'FAIL':2})
gate('same four methods plus existing hub filters test5GREEN',read(H/'target-GREEN.status.json')['exit']==0 and 'Ran 5 tests'in green and '\nOK\n'in green)
raw=read(H/'native-GREEN.js.result.json');az=read(H/'native-AZ-recheck.js.result.json');accepted=read(H/'accepted-observations.json');oldaz=[r for r in raw['rows']if r.get('lang')=='az'];others=[r for r in raw['rows']if r.get('lang')!='az']
gate('original locale QA mismatch preserved without false AZ coverage',dict(collections.Counter(r['status']for r in raw['rows']))=={'PASS':573,'FAIL':24}and len(oldaz)==198 and all(r['status']=='PASS'for r in others)and len(read(H/'excluded-locale-observations.json')['original_rows_retained'])==198 and read(H/'locale-setup-correction.json')['existing_assertions_changed']is False)
gate('native language menu plus actual html AZ checks complete targeted subset',len(az['rows'])==219 and all(r['status']=='PASS'for r in az['rows'])and sum(r['id']=='actual AZ language before pager traversal'for r in az['rows'])==12 and sum(r['id']=='native language menu selects actual AZ'for r in az['rows'])==2 and sum(r['id']=='actual AZ language after edge states'for r in az['rows'])==4)
expected={(role,l,w)for role in('admin','reviewer')for l in('ru','az','en')for w in(360,390,768,1024,1280,1440)};main=[r for r in accepted['rows']if r['id']=='reload keeps filters order and32pending counter']
gate('618accepted PASS observations complete36main actual locale cells',accepted['counts']=={'PASS':618}and len(accepted['rows'])==618 and all(r['status']=='PASS'for r in accepted['rows'])and len(main)==36 and{(r['role'],r['lang'],r['width'])for r in main}==expected)
for obs in('native Tab reaches visible next focus','native ShiftTab returns to visible previous focus','native Enter opens seven distinct page2rows','native Enter returns to same ordered page1','first-page pager and text fit viewport','last-page pager and text fit viewport'):
 rows=[r for r in accepted['rows']if r['id']==obs];gate(obs,len(rows)==36 and all(r['status']=='PASS'for r in rows))
for obs,n in [('empty queue has no broken pagination',12),('single-page queue has3rows and no pager',12),('out-of-range uses page2and valid previous1',12),('invalid filter remains400with visible alert and no pager',12),('duplicate author preserved while old page values replaced',3),('duplicate-filter native link still renders seven rows',3)]:
 rows=[r for r in accepted['rows']if r['id']==obs];gate(obs,len(rows)==n and all(r['status']=='PASS'for r in rows))
issues=[]
for d in(raw,az):issues.extend(x for x in d['diagnostics']if x['kind']=='pageerror'or x['kind']=='requestfailed'and x['local']or x['kind']=='console'and x['local']and not x['expected400'])
gate('no unexpected local console network or page errors',not issues,issues)
state=json.load(urllib.request.urlopen(meta['url']+'/qa/state/',timeout=15));domain=[r for r in accepted['rows']if r['id']=='candidate and live domain unchanged'];gate('live candidate domain unchanged across both browser passes',state==read(H/'state-final.json')and len(domain)==2 and all(state==r['detail']['before']==r['detail']['after']for r in domain)and state['organizations']==state['revisions']==35 and state['pending']==32)
images=read(H/'png-manifest.json');badimages=[]
for row in images:
 b=(H/row['path']).read_bytes()
 if not(b[:8]==b'\x89PNG\r\n\x1a\n'and len(b)==row['bytes']and hashlib.sha256(b).hexdigest()==row['sha256']and struct.unpack('>II',b[16:24])==(row['width'],row['height'])):badimages.append(row['path'])
gate('146PNG SHA sizes dimensions with honest phase labels',len(images)==146 and not badimages and dict(collections.Counter(x['phase']for x in images))=={'RED':2,'QA_LOCALE_SETUP':36,'RU_EN_GREEN':72,'TRUE_AZ_GREEN':36}and len(read(H/'visual-review.json')['accepted_viewed'])==4,badimages)
secrets=[v for v in read(S/'credentials.json').values()if isinstance(v,str)and len(v)>10];leaks=[];count=0
for p in H.rglob('*'):
 if p.is_file()and p.suffix in{'.py','.js','.json','.jsonl','.txt','.md','.html','.csv','.diff'}:
  count+=1
  if any(v in p.read_text()for v in secrets):leaks.append(str(p.relative_to(H)))
gate('own generated credentials absent from public artifacts',not leaks,{'scanned':count,'hit_paths_only':leaks})
syntax=[]
for p in H.glob('*.py'):
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax.append(p.name)
for p in H.glob('*.js'):
 if subprocess.run(['node','--check',str(p)],capture_output=True).returncode:syntax.append(p.name)
gate('own QA/proposal Python JS syntax',not syntax,syntax)
white=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True);gate('git diff whitespace check',white.returncode==0,{'exit':white.returncode})
(H/'verification.json').write_text(json.dumps({'status':'GATE_RUNNING','fixed':False}));broken=[]
for target in re.findall(r'\]\(([^)]+)\)',(H/'REPORT.md').read_text()):
 if target.startswith(('http:','https:','#')):continue
 if not(H/target.split('#',1)[0]).exists():broken.append(target)
gate('report evidence next prompt links exist',not broken and(H/'next-prompt.txt').is_file(),broken)
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'decision':'MOD-QA-01 SCOPED LOCAL PASS'if all(x['pass']for x in checks)else'VERIFICATION FAILED','all_checks_pass':all(x['pass']for x in checks),'closed_ids':['MOD-QA-01']if all(x['pass']for x in checks)else[],'other_MOD_IDs_closed':[],'module08_full_accepted':False,'scope':[template,test],'snapshot':{'root':str(R),'head':head,'branch':branch,'dirty_worktree':True,'active_run':active},'target_methods':5,'new_methods':4,'accepted_browser_PASS':618,'main_cells':36,'PNG':146,'retained_QA_locale_rows_excluded':198,'checks':checks,'NOT_RUN':['full08/other MOD IDs','module07/global corpus rerun','production/commit/push/deploy','cross-browser/screen-reader/full WCAG','module09'],'continuity_limit':'65entry containers/4knownHTTP checked; older4absent HTTP continuity remains NOT VERIFIED. Foreign processes not restarted, their cached templates are not current-source evidence.'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'decision':result['decision'],'checks':len(checks),'all_checks_pass':result['all_checks_pass'],'failed':[c['name']for c in checks if not c['pass']]}));sys.exit(0 if result['all_checks_pass']else 1)
