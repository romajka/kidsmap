import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');sources=read(O/'source-applied.json')['sources'];candidate=read(O/'approved-candidate-manifest.json');assert len(sources)==1034 and all(sha(R/p)==h for p,h in sources.items())
changed=[p for p,h in entry['sources'].items() if sha(R/p)!=h];assert set(changed)=={'src/catalog/domain_admin/site.py','static/admin/css/pages/kidsmap_site_settings.css'} and set(sources)-set(entry['sources'])=={'src/catalog/testcases/test_site_qa22_save_exit.py'}
for p,d in candidate['files'].items():assert sha(R/p)==d['candidate_sha256']
count=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);count+=1
assert len(entry['prior_packages'])==38 and count==7576 and all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={s.split()[1]:(s.split()[0],s.split()[2]) for s in entry['containers']};now={s.split()[1]:(s.split()[0],s.split()[2]) for s in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
reverse=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert reverse.returncode==0,reverse.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
d={'source_count':1034,'approved_application_files':list(candidate['files']),'changed_existing':2,'new_test':1,'other_existing_sources_unchanged':1031,'exact_candidate_hashes':True,'prior_packages':38,'prior_files':count,'shared_MO_cbmignore':True,'HEAD_branch_task33_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'own_container_verified':True,'reverse_exact_diff_check_exit':0,'native_git_diff_check_exit':0};(O/'evidence/preservation.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
