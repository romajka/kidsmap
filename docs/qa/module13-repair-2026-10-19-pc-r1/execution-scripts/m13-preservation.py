import json,hashlib,re,subprocess,ast,difflib
from pathlib import Path
from datetime import datetime
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';Q=R/'.tmp/m13-full-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();entry=read(O/'source-entry.json');current=read(Q/'expected-source.json')['sources'];assert all(sha(R/p)==h for p,h in current.items())
assert current==read(R/'.tmp/m13-qa04-r5/profile/source-entry.json')['sources']
new={'src/catalog/testcases/test_module13_event_projection.py','src/catalog/testcases/test_module13_discovery.py','scripts/run_isolated_quality.py','scripts/tests/test_quality_profile.py','.gitattributes'}
fixtures={'src/catalog/testcases/test_admin_review_workflow_fix.py','src/catalog/testcases/test_moderation_sla.py','src/catalog/testcases/test_content_entry_final.py','scripts/tests/test_build_isolated_locales.py'}
initial_sources=entry['sources'];qualified=dict(initial_sources);supplement={}
for path in set(current)-set(initial_sources)-new:
 found=sorted((O/'stages').glob('*/entry-source/'+path),key=lambda p:p.stat().st_mtime_ns);assert found,path
 original=found[0];qualified[path]=sha(original);supplement[path]={'before_first_edit_sha256':sha(original),'record':original.relative_to(O).as_posix(),'qualification':'Existing CI/shell source not covered by the inherited1066-file manifest; exact bytes captured before this task first edited it.'}
assert set(supplement)=={'.github/workflows/deploy.yml','scripts/backup-db.sh','scripts/run_kidsmap_tests.sh'}
(O/'source-supplemental-entry.json').write_text(json.dumps(supplement,indent=2));entry={**entry,'sources':qualified}
approved=set(new)
for patch in (O/'stages').rglob('implemented.diff'):approved.update(re.findall(r'^\+\+\+ b/(.+)$',patch.read_text(),re.M))
changed={p:{'before':entry['sources'].get(p),'after':h} for p,h in current.items() if entry['sources'].get(p)!=h};assert set(changed)<=approved
assert all(current[p]==h for p,h in entry['sources'].items() if ('testcases/' in p or p.startswith('scripts/tests/')) and p not in fixtures)
assertions=lambda text:[ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Assert) or (isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert'))]
proof={};diff='';(O/'final-candidate').mkdir(exist_ok=True)
for path,meta in changed.items():
 after=(R/path).read_bytes();before=b''
 if meta['before']:
  found=[p for p in (O/'stages').glob('*/entry-source/'+path) if sha(p)==meta['before']];assert found,path;before=found[0].read_bytes()
 if path in fixtures:
  assert assertions(before.decode())==assertions(after.decode()),path
  proof[path]={'all_existing_assertions_identical':True,'count':len(assertions(after.decode()))}
 target=O/'final-candidate'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(after)
 diff+=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+path if before else '/dev/null',tofile='b/'+path))
(O/'application.diff').write_text(diff,newline='');(O/'evidence/all-existing-assertions-preserved.json').write_text(json.dumps(proof,indent=2))
for package,files in entry['prior_packages'].items():
 folder=R/'docs/qa'/package;assert {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}==set(files),package;assert all(sha(folder/p)==h for p,h in files.items()),package
git=lambda *args:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*args],text=True).strip();g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert g==entry['git'] and not git('diff','--cached','--name-only');assert sha(R/'.cbmignore')==entry['cbmignore'];assert all(sha(R/p)==h for p,h in entry['shared_mo'].items());assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
assert all(sha(R/p)==h for p,h in read(O/'document-current.json').items());containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();actual={line.split()[1]:line.split() for line in containers};transitions=[]
for previous in entry['containers']:
 fields=previous.split();now=actual[fields[1]];assert now[:2]==fields[:2]
 if now[2]!=fields[2]:
  meta=json.loads(subprocess.check_output(['docker','inspect',fields[1],'--format','{"exit":{{.State.ExitCode}},"oom":{{.State.OOMKilled}},"started":{{json .State.StartedAt}},"finished":{{json .State.FinishedAt}},"entry":{{json .Config.Entrypoint}},"cmd":{{json .Config.Cmd}}}'],text=True))
  duration=(datetime.fromisoformat(meta['finished'].replace('Z','+00:00'))-datetime.fromisoformat(meta['started'].replace('Z','+00:00'))).total_seconds();natural=fields[2]=='running' and now[2]=='exited' and meta['exit']==0 and not meta['oom'] and meta['entry'] in [['python'],['python3']] and len(meta['cmd'])==2 and meta['cmd'][0]=='-c' and re.fullmatch(r'import time;\s*time.sleep\(86400\)',meta['cmd'][1]) and duration>=86400
  assert natural,fields[1];transitions.append({'name':fields[1],'identity_preserved':True,'transition':'running→exited','exit':0,'OOM':False,'duration_seconds':duration,'configured_lifetime_seconds':86400,'explanation':'Natural completion of existing sleep(86400); no task restart/stop/recreate.'})
(O/'evidence/foreign-runtime-transitions.json').write_text(json.dumps(transitions,indent=2))
p=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check','--',*changed],capture_output=True,text=True);assert p.returncode==0,p.stderr
for path in changed:
 if path.endswith('.py'):compile((R/path).read_text(),path,'exec')
(O/'source-current.json').write_text(json.dumps({'sources':current,'changes':changed,'git':g},indent=2));result={'status':'PASS source/artifact preservation','sources_checked':len(current),'original_sources':len(initial_sources),'qualified_existing_source_baseline':len(qualified),'new_files':len(new),'changed_or_added':len(changed),'all_changes_planned':True,'all_other_original_test_bytes_unchanged':True,'maintained_fixture_files':len(fixtures),'all_original_assertions_preserved':True,'original_assertion_count':sum(v['count'] for v in proof.values()),'prior_packages':len(entry['prior_packages']),'prior_files':sum(map(len,entry['prior_packages'].values())),'prior_hashes_and_sets_unchanged':True,'git':g,'entry_refs_index_empty_staging_preserved':True,'shared_MO_cbmignore_active_run_preserved':True,'foreign_container_identities_preserved':True,'foreign_states_unchanged':not transitions,'documented_natural_expirations':len(transitions),'python_syntax':'PASS','whitespace_exit':p.returncode,'production':'NOT TOUCHED'};(O/'evidence/preservation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
