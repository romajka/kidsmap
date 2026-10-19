import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa22-recheck-2026-10-18-pc-r1';O=R/'docs/qa/site-qa22-plan-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-plan-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not O.exists();O.mkdir()
origin=(P/'IMPLEMENTATION_PLAN.md').read_text();assert origin.count(chr(27))==1
clean=origin.replace(chr(27),'e');assert not [c for c in clean if ord(c)<32 and c not in '\r\n\t']
clean=re.sub(r'\]\((?!\.\./|https?:|#)([^)]+)\)',lambda m:'](../'+P.name+'/'+m.group(1)+')',clean)
(O/'IMPLEMENTATION_PLAN.md').write_text(clean)
entry=read(P/'source-entry.json');sources=read(P/'source-final.json')['sources'];assert all(sha(R/p)==h for p,h in sources.items())
prior=entry['prior_packages'];pm=read(P/'artifact-manifest.json');assert len(pm)==131 and all(sha(P/p)==h for p,h in pm.items());prior[P.name]={**pm,'artifact-manifest.json':sha(P/'artifact-manifest.json')};assert len(prior)==37 and sum(map(len,prior.values()))==7568
for pkg,files in prior.items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
docs={p:sha(R/p) for p in entry['documents']};old_containers={s.split()[1]:(s.split()[0],s.split()[2]) for s in entry['containers']};current=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();current_map={s.split()[1]:(s.split()[0],s.split()[2]) for s in current};assert all(current_map.get(k)==v for k,v in old_containers.items())
write('source-entry.json',{'sources':sources,'prior_packages':prior,'shared_mo':entry['shared_mo'],'cbmignore':entry['cbmignore'],'git':entry['git'],'containers':current,'documents':docs});write('source-final.json',{'sources':sources,'application_changes':0,'git':entry['git']})
candidate=read(P/'candidate-manifest.json');assert candidate['diff_sha256']=='e60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97' and candidate['not_applied'] and len(candidate['files'])==3
write('editorial-correction.json',{'original_package':P.name,'original_plan_sha256':sha(P/'IMPLEMENTATION_PLAN.md'),'corrected_plan_sha256':sha(O/'IMPLEMENTATION_PLAN.md'),'correction':'One accidental ESC introduced by PowerShell quoting in prose describing email fixture replaced with e; relative evidence links adjusted for sibling directory. Original sealed package unchanged. No code/test/expectation/candidate diff changes.','original_source_report':'../'+P.name+'/REPORT.md','exact_candidate_diff_sha256_unchanged':candidate['diff_sha256']})
note='\n\n## SITE22 — чистовая копия плана, 2026-10-18 pc-r1\n\n[Актуальный PLAN]({prefix}{name}/IMPLEMENTATION_PLAN.md), [прежний exact3file diff]({prefix}{origin}/proposed.diff), [provenance]({prefix}{name}/editorial-correction.json). В prose email fixture исправлен один случайный управляющий ESC от shell quoting; evidence links перенесены для sibling directory. Исходный sealed пакет131entries сохранён без изменений. Code/test/assertions/diffSHAe60661fd... неизменны; APP0changes/source1033unchanged. SITE22/P3 OPEN/approvalpending, module10 остаётся14OPEN(9P2/5P3), SITE08/прочиеLOCALclosures retained. BackendRED9/3failed/6PASS/20observations/0errors и labelled destination prototype162controls из первоначального пакета; actual-sourceGREEN NOTRUN.37priorpackages/7568files/MO/.cbmignore/refs-index/activeNONE/foreignruntimes preserved.\n'
preservation={}
for rel,h in docs.items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h;backup=Q/'plan-documents'/rel;backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before);p.write_bytes(before+note.format(prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '',name=O.name,origin=P.name).encode());assert p.read_bytes().startswith(before);preservation[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',preservation)
check=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert check.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in sources.items())
write('verification.json',{'status':'SITE22 exact3file PLAN READY; approvalpending; application0changes','candidate_diff_package':P.name,'candidate_diff_sha256':candidate['diff_sha256'],'corrected_plan_no_control_characters':True,'prior_packages':37,'prior_files':7568,'source1033unchanged':True,'refs_index_MO_cbmignore_activeNONE_preserved':True,'foreign_runtimes_preserved':True,'native_git_diff_check_exit':0,'backend_and_prototype_evidence':'Reused original sealed PLAN run; no new application tests needed for prose correction','GREEN':'NOTRUN','module10':'14OPEN(9P2/5P3)'})
(O/'prepare.py').write_bytes(Path(__file__).read_bytes())
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items());print(json.dumps({'status':'Clean approval plan saved; sealed original unchanged','plan':str(O/'IMPLEMENTATION_PLAN.md'),'candidate_files':3,'sealed_entries':len(manifest),'prior_packages':37,'prior_files':7568,'source1033unchanged':True},indent=2))
