import hashlib,json,re,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
entry=read(O/'source-entry.json');sources=read(O/'source-applied.json')['sources'];assert len(sources)==1033 and all(sha(R/p)==h for p,h in sources.items())
assert [p for p,h in entry['sources'].items() if sha(R/p)!=h]==['static/admin/css/pages/kidsmap_settings_forms.css']
count=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);count+=1
assert len(entry['prior_packages'])==35 and count==7127
assert sha(R/'.cbmignore')==entry['cbmignore'] and all(sha(R/p)==h for p,h in entry['shared_mo'].items())
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
reverse=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert reverse.returncode==0,reverse.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
css=(R/'static/admin/css/pages/kidsmap_settings_forms.css').read_bytes();assert all(line.endswith(b'\r\n') for line in css.splitlines(keepends=True)) and all(not line.endswith((b' ',b'\t')) for line in css.splitlines())
result={'sources':1033,'changed_source_files':['static/admin/css/pages/kidsmap_settings_forms.css'],'other_sources_unchanged':1032,'prior_packages':35,'prior_files':count,'shared_MO':True,'cbmignore':True,'HEAD_branch_task33_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'own_container_verified':True,'reverse_exact_diff_check_exit':reverse.returncode,'native_git_diff_check_exit':diff.returncode,'CRLF_and_no_trailing_spaces_tabs':True}
(O/'evidence/preservation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
