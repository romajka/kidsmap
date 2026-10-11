"""Fresh preservation/runtime/artifact verification; no app/stand mutation."""
from pathlib import Path
import json,hashlib,subprocess,ast,re,urllib.request,datetime,struct
P=Path(__file__).resolve().parent;R=P.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
snapshot=json.loads((P/'snapshot.json').read_text());prior=json.loads((P/'preservation-entry.json').read_text())
changed=[k for k,v in prior.items() if not (R/k).is_file() or sha(R/k)!=v]
src=[k for k,v in snapshot['source_files'].items() if not (R/k).is_file() or sha(R/k)!=v]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();branch=subprocess.check_output(['git','branch','--show-current'],cwd=R,text=True).strip()
active=next(x.split(':',1)[1].strip() for x in (R/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
runtime={}
for port in [8827,8828]:runtime[str(port)]=json.load(urllib.request.urlopen(f'http://localhost:{port}/qa/version/',timeout=15))
(P/'runtime-final.json').write_text(json.dumps(runtime,indent=2),encoding='utf-8')
rows=json.loads((P/'matrix.json').read_text());badstatuses=[i for i,x in enumerate(rows) if x['status'] not in ['PASS','FAIL','NOT RUN']]
counts={s:sum(x['status']==s for x in rows) for s in ['PASS','FAIL','NOT RUN']};assert counts==json.loads((P/'counts.json').read_text())['accepted_observations']
shots=json.loads((P/'screenshots-manifest.json').read_text());badshots=[x['file'] for x in shots if not (P/x['file']).is_file() or sha(P/x['file'])!=x['sha256']]
missingEvidence=[]
for row in rows:
 for key in ['evidence','shot']:
  if row.get(key) and not (P/row[key]).is_file():missingEvidence.append(row[key])
syntax=[];jsonerrors=[];json_count=0;ast_count=0
for file in P.glob('*.py'):
 ast_count+=1
 try:ast.parse(file.read_text(encoding='utf-8'),filename=str(file))
 except Exception as e:syntax.append({'file':file.name,'error':str(e)})
for file in P.rglob('*.json'):
 json_count+=1
 try:json.loads(file.read_text(encoding='utf-8'))
 except Exception as e:jsonerrors.append({'file':file.name,'error':str(e)})
credential=(R/'.tmp/module11-20261011-r1/credential').read_text();secretHits=[]
for file in P.rglob('*'):
 if not file.is_file() or file.suffix=='.png':continue
 text=file.read_text(encoding='utf-8',errors='replace')
 if credential in text:secretHits.append({'file':file.relative_to(P).as_posix(),'type':'known own credential'})
 if re.search(r'csrfmiddlewaretoken[^<>]{0,120}value=["\'][A-Za-z0-9]{64}',text):secretHits.append({'file':file.relative_to(P).as_posix(),'type':'unredacted CSRF64'})
brokenLinks=[]
for file in P.rglob('*.md'):
 for target in re.findall(r'\]\(([^)]+)\)',file.read_text(encoding='utf-8')):
  if target.startswith(('http:','https:','#','codex:')) or '<each' in target:continue
  path=target.split('#',1)[0].split(':',1)[0] if ':' in target and not re.match(r'^[A-Za-z]:',target) else target
  if not (file.parent/path).exists():brokenLinks.append({'file':file.relative_to(P).as_posix(),'target':target})
entryLines=(P/'journal-entry.txt').read_bytes().splitlines(keepends=True);nowLines=(R/'docs/qa/module-acceptance-prompts.md').read_bytes().splitlines(keepends=True)
jdiff=[i+1 for i,(a,b) in enumerate(zip(entryLines,nowLines)) if a!=b]
journal_ok=len(entryLines)==len(nowLines) and (not jdiff or len(jdiff)==1 and entryLines[jdiff[0]-1].startswith(b'| 11 |'))
# Foreign manifest permits exactly the requested row11 mutation.
allowedChanged=[]
if 'docs/qa/module-acceptance-prompts.md' in changed and journal_ok:
 changed.remove('docs/qa/module-acceptance-prompts.md');allowedChanged=['docs/qa/module-acceptance-prompts.md:row11']
diffcheck=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace')
js=subprocess.run(['C:/Program Files/nodejs/node.exe',str(P/'check-js.cjs')],cwd=R,capture_output=True,text=True)
definitions=['.agents/agents/kidsmap-orchestrator/agent.md','.agents/agents/seo-reviewer/agent.md','.agents/agents/integration-reviewer/agent.md','.agents/agents/browser-qa/agent.md']
missingDocs=[x for x in json.loads((P/'documents.json').read_text())['checked']+definitions if not (R/x).is_file()]
newfiles=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
unownedNew=[f for f in newfiles if f not in prior and (R/f).is_file() and P not in (R/f).parents and not Path(f).name.startswith('.env') and '__pycache__' not in f]
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkout':str(R),'head':head,'branch':branch,'head_unchanged':head==snapshot['head'],'branch_unchanged':branch==snapshot['branch'],'active_run':active,'active_run_unchanged':active==snapshot['active_run'],'source_files':len(snapshot['source_files']),'source_drift':src,'foreign_files_at_entry':len(prior),'foreign_changed_unallowed':changed,'foreign_new_unowned':unownedNew,'allowed_changes':allowedChanged,'journal_changed_lines':jdiff,'journal_only_row11':journal_ok,'runtime':runtime,'missing_documents':missingDocs,'counts':counts,'bad_status_rows':badstatuses,'PNG':len(shots),'bad_screenshots':badshots,'missing_evidence':missingEvidence,'python_AST_files':ast_count,'python_AST_errors':syntax,'JSON_files':json_count,'JSON_errors':jsonerrors,'broken_local_links':brokenLinks,'known_secret_hits':secretHits,'git_diff_check_exit':diffcheck.returncode,'git_diff_check_output':diffcheck.stdout+diffcheck.stderr,'JS_syntax_exit':js.returncode,'JS_syntax_output':js.stdout,'production':'NOT RUN','application_changes_by_audit':False,'stand_profile':'own main DEBUGFalse, same WORKTREE and isolated DB; supplemental DEBUGFalse'}
ok=all([result['head_unchanged'],result['branch_unchanged'],result['active_run_unchanged'],journal_ok,not src,not changed,not unownedNew,not badstatuses,not badshots,not missingEvidence,not syntax,not jsonerrors,not brokenLinks,not secretHits,not missingDocs,diffcheck.returncode==0,js.returncode==0,all(v['entry_matches_startup'] and v['startup_matches_disk'] and v['testing'] for v in runtime.values())])
result['verified']=ok;result['exit_code']=0 if ok else 1
(P/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ['verified','exit_code','source_drift','foreign_changed_unallowed','foreign_new_unowned','journal_changed_lines','PNG','counts','python_AST_errors','JSON_errors','broken_local_links','known_secret_hits','missing_evidence','git_diff_check_exit']}));raise SystemExit(result['exit_code'])
