import ast,collections,hashlib,json,os,struct,subprocess,sys,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name;P=R/'docs/qa/mod-qa02-recheck-2026-10-15-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=read(H/'entry.json');a=read(H/'approval.json');checks=[]
def gate(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
git=lambda *args:subprocess.check_output(['git',*args],cwd=R,text=True).strip()
gate('root HEAD branch active_run unchanged',str(R)==e['root']and git('rev-parse','HEAD')==e['head']and git('branch','--show-current')==e['branch']and [x for x in(R/'docs/task33/implementation-status.md').read_text().splitlines()if x.startswith('active_run:')]==e['active_run'])
gate('user approved exact plan and diff hashes unchanged',sha(P/'IMPLEMENTATION_PLAN.md')==a['plan_sha256']and sha(P/'proposed-MOD-QA-02.diff')==a['diff_sha256'])
changed=[];missing=[]
for path,digest in e['files'].items():
 p=R/path
 if not p.is_file():missing.append(path)
 elif sha(p)!=digest:changed.append(path)
allowed={'docs/qa/continuation-and-repair-prompts-2026-10-11.md',*[r['target']for r in a['scope']if r['action']=='modify']}
gate('30310entry files preserved except two approved sources and currentguide',len(e['files'])==30310 and set(changed)==allowed and not missing,{'changed':changed,'missing':missing})
g=read(H/'guide-edits.json');s=(R/g['path']).read_text();inverse=s.replace('\n'+g['added_note'],'',1).replace(g['new_table_row'],g['old_table_row'],1)
gate('exact inverse two currentguide edits preserves history',s.count(g['added_note'])==1 and s.count(g['new_table_row'])==1 and hashlib.sha256(inverse.encode()).hexdigest()==g['before_sha256']==e['files'][g['path']])
paths=subprocess.check_output(['git','ls-files','-c','-o','--exclude-standard','-z'],cwd=R).decode().split('\0');new={p for p in paths if p and p not in e['files']and '.env'not in Path(p).name and (R/p).is_file()and not p.startswith('docs/qa/'+H.name+'/')};expectednew={r['target']for r in a['scope']if r['action']=='create'}
gate('only five approved new application files outside ownQA',new==expectednew,sorted(new))
gate('all seven application files byte-identical to approved proposal',len(a['scope'])==7 and all(sha(R/r['target'])==r['proposal_sha256']==sha(P/r['proposal'])for r in a['scope']))
expectedstatus=set(e['status'].splitlines())|{'?? '+p for p in expectednew}|{' M '+r['target']for r in a['scope']if r['action']=='modify'};status=subprocess.check_output(['git','status','--short'],cwd=R,text=True)
gate('all foreign dirty entries retained only approved app additions',set(status.splitlines())==expectedstatus)
gate('shared MO unchanged',all(sha(p)==e['files'][str(p.relative_to(R))]for p in R.glob('locale/*/LC_MESSAGES/*.mo')))
containers=[{k:c[k]for k in('ID','Names','Ports','State')}for c in[json.loads(x)for x in subprocess.check_output(['docker','ps','-a','--format','json'],text=True).splitlines()]];ids={c['ID']:c for c in containers};diff=[c['Names']for c in e['containers']if ids.get(c['ID'])!=c];newcontainers=[c['Names']for c in containers if c['ID']not in{r['ID']for r in e['containers']}];cfg=read(S/'config.json')
gate('67foreign containers identity ports state retained only own addition',len(e['containers'])==67 and not diff and newcontainers==[cfg['container']],diff)
procs=[]
for p in e['foreign_processes']:
 try:proc=Path('/proc')/str(p['pid']);ok=proc.joinpath('cmdline').read_bytes().split(b'\0')[:-1]==[x.encode()for x in p['args']]and str((proc/'cwd').resolve())==p['cwd']
 except OSError:ok=False
 procs.append({'pid':p['pid'],'identity_unchanged':ok})
gate('six known foreign HTTP identities retained without restarts',len(procs)==6 and all(x['identity_unchanged']for x in procs),procs)
m=read(H/'server.json');proc=Path('/proc')/str(m['pid']);gate('actual own process argv cwd',proc.joinpath('cmdline').read_bytes().split(b'\0')[:-1]==[x.encode()for x in m['argv']]and (proc/'cwd').resolve()==R)
src=json.load(urllib.request.urlopen(m['url']+'/qa/source/',timeout=15));pins=read(H/'runtime-source-baseline.json');gate('953current sources actual startup equal pinned disk',len(pins)==953 and src['source']==pins and src['startup_matches_disk']and all(sha(R/p)==v for p,v in pins.items()))
gate('actual cached patched hub template and app origins',src['pid']==m['pid']and src['root']==str(R)and src['template_origin']==str(R/'src/catalog/templates/admin/volunteer/hub_detail.html')and src['loaded_template_sha256']==sha(R/'src/catalog/templates/admin/volunteer/hub_detail.html')and src['loaded_module_paths']=={'views':str(R/'src/catalog/domain_admin/volunteer.py'),'service':str(R/'src/catalog/services/moderation_hub.py')})
ri=read(H/'runtime-info.json');gate('own isolated testing DB cache media private email interpreter',ri['testing']and ri['database']==cfg['database']and ri['database_user']==cfg['user']and ri['interpreter']==m['argv'][0]and ri['cache']['BACKEND']=='django.core.cache.backends.locmem.LocMemCache'and all(Path(ri[k]).is_relative_to(S)for k in('media','private_media','email_path'))and ri['migrations']==175 and not ri['base_code_default_retention_active'])
mo=sorted(str(p.resolve())for p in(S/'locales').rglob('*.mo'));gate('sole own current three locales actually opened',len(mo)==3 and all(p in src['actual_opened_MO']for p in mo)and src['sole_locale_paths']==ri['sole_locale_paths']==[read(H/'locale-manifest.json')['locale_root']])
# Locale builder independent verify is read-only and verifies source/content hashes.
locale=subprocess.run([m['argv'][0],'scripts/build_isolated_locales.py','verify','--manifest',str(S/'locales/manifest.json')],cwd=R,capture_output=True,text=True);gate('current source PO to own MO manifest still verifies',locale.returncode==0,{'exit':locale.returncode})
gate('exact own dependency bytes and interpreter origins',all(sha(S/'python-deps'/p)==v for p,v in read(H/'dependency-manifest.json').items())and Path(ri['pypdf_origin']).is_relative_to(S/'python-deps'))
red=(H/'regression-RED.output.txt').read_text();green=(H/'target-GREEN.output.txt').read_text();gate('fresh permanent seven-method12assertion RED before apply',read(H/'regression-RED.status.json')['exit']==1 and 'Ran 7 tests'in red and 'FAILED (failures=12)'in red and '\nERROR:'not in red)
gate('13target methods GREEN with unchanged assertions',read(H/'target-GREEN.status.json')['exit']==0 and 'Ran 13 tests'in green and '\nOK\n'in green and sha(R/'src/catalog/testcases/test_mod_qa02_hub_media.py')==sha(P/'proposed/test_mod_qa02_hub_media.py'))
accepted=read(H/'accepted-observations.json');rows=accepted['rows'];gate('797accepted observations all PASS',len(rows)==797 and accepted['counts']=={'PASS':797}and all(r['status']=='PASS'for r in rows))
main=read(H/'native-main.js.result.json');edges=read(H/'native-edges.js.result.json');dec=read(H/'native-decisions.js.result.json');auth=read(H/'native-authors.js.result.json');owner=read(H/'native-owner-recheck.js.result.json');security=read(H/'native-security.js.result.json')
cells={(r['role'],r['lang'],r['width'])for r in main['rows']if r['id']=='eight current candidate images decoded'};gate('36role actual locale width cells with decoding and geometry',len(cells)==36 and sum(r['id']=='comparison and each photo fit viewport without horizontal clipping'and r['status']=='PASS'for r in main['rows'])==36 and sum(r['id']=='native menu selects actual locale'and r['status']=='PASS'for r in main['rows'])==6)
for obs in('native Tab reaches visible thumbnail focus','native Enter opens exact full image in new tab','closing image keeps original thumbnail focus','native ShiftTab returns to moderation back link','reload preserves all eight decoded comparisons','gallery follows saved order on both sides'):
 selected=[r for r in main['rows']if r['id']==obs];gate(obs,len(selected)==36 and all(r['status']=='PASS'for r in selected))
gate('main readonly domain unchanged',main['rows'][-1]['detail']['before']==main['rows'][-1]['detail']['after'])
gate('24edge cells six HTTP200corrupt decode failures with hidden broken link',len({(r['lang'],r['width'],r['edge'])for r in edges['rows']if r['id']=='native edge detail in actual locale'})==24 and sum(r['id']=='corrupt existing HTTP200 image fails decode and link is hidden'and r['status']=='PASS'for r in edges['rows'])==6 and len(edges['responses'])==6 and all(r['status']==200 for r in edges['responses'])and not edges['dialogs'])
gate('24edge keyboard paths no GET mutation',sum(r['id']=='native Tab skips unavailable image links and reaches reason'and r['status']=='PASS'for r in edges['rows'])==24 and edges['rows'][-1]['detail']['before']==edges['rows'][-1]['detail']['after'])
gate('12native decisions six approve six reject all locales widths',len(dec['outcomes'])==12 and collections.Counter(x['fixture']['action']for x in dec['outcomes'])=={'approve':6,'reject':6}and len({(x['fixture']['lang'],x['fixture']['width'],x['fixture']['action'])for x in dec['outcomes']})==12)
valid=True
for x in dec['outcomes']:
 b=x['before'];v=x['after'];action=x['fixture']['action']
 if action=='approve':valid &= v['revision_status']=='approved'and v['live_photo']==b['candidate_photo']and v['live_cover']==b['candidate_cover']and [(p['image'],p['caption'],p['order'])for p in v['live_gallery']]==[(p['image'],p['caption'],p['order'])for p in sorted(b['candidate_gallery'],key=lambda y:y['order'])]
 else:valid &= v['revision_status']=='declined'and v['live_photo']==b['live_photo']and v['live_cover']==b['live_cover']and v['live_gallery']==b['live_gallery']
gate('native decision readback follows existing live media contract',valid)
gate('12anonymous public card gallery native decoded readbacks',sum(r['id']=='public readback loads expected main and gallery after reload'and r['status']=='PASS'for r in dec['rows'])==12 and sum(r['id']=='anonymous public gallery exposes main and saved gallery order'and r['status']=='PASS'for r in dec['rows'])==12)
gate('native invalid reason409 retains8photos data and error focus',sum(r['id']=='native invalid reason preserves candidate and eight decoded previews with visible error'and r['status']=='PASS'for r in dec['rows'])==1 and sum(r['id']=='server error receives keyboard focus'and r['status']=='PASS'for r in dec['rows'])==1)
flows=auth['outcomes']+owner['outcomes'];valid=len(flows)==2 and {f['role']for f in flows}=={'owner','volunteer'}
for f in flows:
 b=f['before'];d=f['draft'];p=f['pending'];valid &= b['revision_id']is None and d['revision_status']=='draft'and f['reloaded']['domain_sha256']==d['domain_sha256']and p['revision_status']=='pending'and p['candidate_photo']==d['candidate_photo']!=b['live_photo']and p['candidate_cover']==d['candidate_cover']and p['candidate_gallery']==d['candidate_gallery']and p['live_photo']==b['live_photo']and p['live_cover']==b['live_cover']and p['live_gallery']==b['live_gallery']
gate('two native author uploads draft reload submit real pending readback',valid)
gate('native owner ready reorder and actual reviewer gallery order',all(any(r['id']==name and r['status']=='PASS'for r in owner['rows'])for name in('native owner main and two gallery uploads finish ready','native gallery earlier button reorders proposed additions','reviewer gallery order matches native author reorder')))
gate('retained owner QA NOTRUN superseded by owner-only selector correction',len(auth['rows'])==10 and sum(r['status']=='NOT RUN'for r in auth['rows'])==1 and len(owner['rows'])==10 and all(r['status']=='PASS'for r in owner['rows'])and len(read(H/'excluded-harness-observations.json'))==2 and read(H/'author-harness-correction.json')['owner_before_rerun_has_no_revision'])
gate('unsupported editor control boundaries explicit without source extension',read(H/'author-coverage-boundary.json')['NOT_RUN']==['owner cover upload control (not present)','volunteer gallery upload control (not present)']and not read(H/'author-coverage-boundary.json')['source_scope_extended'])
gate('six native role denials two monitored author reviews three shared text consumers',sum(r['id']=='reviewer surface respects actual account role'and r['status']=='PASS'for r in security['rows'])==6 and sum(r['id']=='native author candidate review with console network monitoring'and r['status']=='PASS'for r in security['rows'])==2 and sum(r['id']=='shared non-media comparison retains escaped text and no thumbnails'and r['status']=='PASS'for r in security['rows'])==3)
gate('existing private fixture not downloadable to content reviewer',read(H/'private-fixture-proof.json')['private_file_count']==1 and any(r['id']=='content reviewer without document permission cannot download private document'and r['status']=='PASS'and r['detail']['status']==404 for r in security['rows']))
gate('diagnostics all explained only expected denials409external blocks',not read(H/'diagnostics-classification.json')['unexplained']and read(H/'diagnostics-classification.json')['expected_counts']['native whitespace reason validation409']==1 and read(H/'diagnostics-classification.json')['expected_counts']['expected access-denial status']==3)
state=json.load(urllib.request.urlopen(m['url']+'/qa/state/',timeout=10));gate('expected own final state21revisions9pending19places38gallery',state==read(H/'state-final.json')and all(state[k]==v for k,v in{'revisions':21,'pending':9,'places':19,'live_gallery':38}.items()))
images=read(H/'png-manifest.json');bad=[]
for row in images:
 p=H/row['path'];b=p.read_bytes()
 if sha(p)!=row['sha256']or len(b)!=row['bytes']or b[:8]!=b'\x89PNG\r\n\x1a\n'or struct.unpack('>II',b[16:24])!=(row['width'],row['height']):bad.append(row['path'])
gate('131native PNG hashes dimensions and phase counts',len(images)==131 and not bad and dict(collections.Counter(r['phase']for r in images))=={'MAIN':48,'EDGE':24,'DECISION':37,'AUTHOR_INITIAL_SUPPORT':2,'AUTHOR_FLOW':8,'SECURITY_SHARED':12},bad)
gate('honest four-frame manual visual review',len(read(H/'visual-review.json')['manually_viewed'])==4 and all((H/p).is_file()for p in read(H/'visual-review.json')['manually_viewed']))
secrets=read(S/'credentials.json').values();leaks=[]
for p in H.rglob('*'):
 if p.is_file()and p.suffix in{'.py','.js','.json','.jsonl','.md','.txt','.html','.diff'}and any(v in p.read_text()for v in secrets):leaks.append(str(p.relative_to(H)))
gate('no own credentials in public artifacts',not leaks,leaks)
syntax=[]
for p in list(H.glob('*.py'))+[R/r['target']for r in a['scope']if r['target'].endswith('.py')]:
 try:compile(p.read_text(),str(p),'exec')
 except SyntaxError:syntax.append(str(p))
for p in list(H.glob('*.js'))+[R/'static/admin/js/moderation_media.js']:
 if subprocess.run(['node','--check',str(p)],capture_output=True).returncode:syntax.append(str(p))
gate('ownQA and approved source Python JS syntax',not syntax,syntax)
whitespace=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True);gate('git diff whitespace check',whitespace.returncode==0,{'exit':whitespace.returncode})
gate('report plan next prompt links present',all(p.is_file()for p in(H/'REPORT.md',H/'next-prompt.txt',P/'IMPLEMENTATION_PLAN.md',P/'proposed-MOD-QA-02.diff')))
result={'decision':'MOD-QA-02 SCOPED LOCAL PASS'if all(r['pass']for r in checks)else'MOD-QA-02 VERIFICATION INCOMPLETE','all_checks_pass':all(r['pass']for r in checks),'closed_ids':['MOD-QA-02']if all(r['pass']for r in checks)else[],'module08_full_accepted':False,'other_MOD_IDs_closed':[],'snapshot':{k:e[k]for k in('root','head','branch','active_run')},'dirty_WORKTREE':True,'target_methods':13,'accepted_native_observations':797,'main_cells':36,'PNG':131,'checks':checks,'NOT_RUN':['full08/global/module09','unsupported owner cover and volunteer gallery controls','remote storage/real external integrations','cross-browser/screen reader/full WCAG','production/commit/push/deploy'],'continuity_limit':'Current67entry containers/6knownHTTP verified; older disappeared HTTP continuity remains NOT VERIFIED, foreign processes not restarted or used as current-source proof'}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'decision':result['decision'],'checks':len(checks),'failed':[r['name']for r in checks if not r['pass']]}));sys.exit(0 if result['all_checks_pass']else 1)
