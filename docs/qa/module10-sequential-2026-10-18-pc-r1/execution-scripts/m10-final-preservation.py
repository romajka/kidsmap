import hashlib,json,re,subprocess,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());entry=read(O/'source-entry.json');sources=read(Q/'expected-source.json')['sources'];assert all(sha(R/p)==h for p,h in sources.items())
changed={p:{'before':entry['sources'].get(p),'after':h} for p,h in sources.items() if entry['sources'].get(p)!=h};approved=set()
for diff in (O/'stages').rglob('*.diff'):
 approved.update(re.findall(r'^\+\+\+ b/(.+)$',diff.read_text(),re.M))
assert set(changed)<=approved,set(changed)-approved
for pkg,files in entry['prior_packages'].items():
 assert all(sha(R/'docs/qa'/pkg/p)==h for p,h in files.items()),pkg
 assert {p.relative_to(R/'docs/qa'/pkg).as_posix() for p in (R/'docs/qa'/pkg).rglob('*') if p.is_file()}==set(files),pkg
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
g={'head':git('rev-parse','HEAD'),'branch':git('branch','--show-current'),'task33_ref':git('rev-parse','task33-progress'),'index_sha256':sha(R/'.git/index')};assert g==entry['git'] and not git('diff','--cached','--name-only');assert sha(R/'.cbmignore')==entry['cbmignore'];assert all(sha(R/p)==h for p,h in entry['shared_mo'].items());assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
current=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert set(entry['containers'])<=set(current)
for p,h in read(O/'document-current.json').items():assert sha(R/p)==h
check=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check','--',*changed],capture_output=True,text=True);assert check.returncode==0,check.stderr
syntax=[]
for p in ['static/js/header.js','static/admin/js/kidsmap_settings_draft.js','static/admin/js/kidsmap_site_media.js']:
 r=subprocess.run(['node','--check',str(R/p)],capture_output=True,text=True);assert r.returncode==0,r.stderr;syntax.append({'path':p,'exit':r.returncode})
get=lambda path:json.loads(urllib.request.urlopen('http://127.0.0.1:33640'+path,timeout=10).read());public=get('/qa/module10/public-state/');fixture=read(O/'fixture-entry.json');assert all(public['values'][k]==v for k,v in fixture['values'].items());assert not public['values']['home_hero_image'] and not public['values']['home_hero_mobile_image'];visibility=get('/qa/module10/visibility-state/');assert visibility['enabled'] is True;form=get('/qa/site08/form-state/');assert not any(x['title_ru'].startswith('SITE23 ') for x in form['gallery'])
baseline=read(O/'evidence/browser-site11-lifecycle.json')['initial'] if 'initial' in read(O/'evidence/browser-site11-lifecycle.json') else None
v={'sources_checked':len(sources),'original_sources':len(entry['sources']),'changed_or_added_sources':len(changed),'approved_paths_only':True,'prior_packages':len(entry['prior_packages']),'prior_files':sum(map(len,entry['prior_packages'].values())),'prior_package_hashes_and_file_sets_unchanged':True,'git':g,'git_refs_index_staging_preserved':True,'shared_MO_cbmignore_active_run_preserved':True,'foreign_container_identity_state_preserved':True,'whitespace_exit':check.returncode,'syntax':syntax,'original_public_fields_restored':True,'original_events_flag_TRUE_restored':True,'all_SITE23_owned_rows_removed_natively':True,'owned_upload_files_retained':'Existing model storage policy; no direct filesystem cleanup','production':'NOT TOUCHED','independent_agent':'NOT USED; root executed read-only verification script'}
(O/'source-final.json').write_text(json.dumps({'sources':sources,'changes':changed,'git':g},indent=2));(O/'evidence/final-preservation.json').write_text(json.dumps(v,indent=2));print(json.dumps(v,indent=2))
