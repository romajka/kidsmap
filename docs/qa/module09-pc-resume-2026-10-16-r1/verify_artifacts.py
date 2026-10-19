"""Verify bounded PLAN evidence; never runs Django, migrations or production tools."""
import ast
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args):
    result=subprocess.run(['git',*args],cwd=ROOT,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    return result.stdout.rstrip('\r\n')
data=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
entry=json.loads((OUT/'source-entry.json').read_text())
assert git('rev-parse','HEAD')==entry['head']==data['git']['head']
assert git('branch','--show-current')==entry['branch']
assert git('rev-list','--left-right','--count','HEAD...origin/'+entry['branch']).split()==['0','0']
assert git('rev-parse','task33-progress')==entry['initial_task33_ref']
assert git('rev-parse','HEAD^{tree}')==entry['index_tree']
git('diff','--cached','--exit-code')
git('diff','--exit-code','--','src','static','templates','scripts','config','locale')
git('diff','--check')
for line in git('status','--porcelain=v1','-uall').splitlines():
    path=line[3:]
    assert path.startswith('docs/qa/module09-pc-resume-2026-10-16-r1/') or path=='docs/qa/continuation-and-repair-prompts-2026-10-11.md',line
assert len(entry['sources'])==1019
assert all(sha(ROOT/path)==digest for path,digest in entry['sources'].items())
assert all(sha(ROOT/path)==digest for path,digest in entry['shared_mo'].items())
active=[line for line in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:')]
assert active==entry['active_run']==['active_run: NONE']
assert not (ROOT/'src/catalog/testcases/test_social_qa03_conflict_recovery.py').exists()
assert not data['proposal']['applied']
git('apply','--check','--ignore-space-change',str(OUT/'proposed.diff'))
rows=json.loads((OUT/'matrix.json').read_text(encoding='utf-8'))
pngs=json.loads((OUT/'png-manifest.json').read_text())
assert {(row['lang'],row['width']) for row in rows}=={(lang,width) for lang in ('ru','az','en') for width in (360,390,768,1024,1280,1440)}
assert len(rows)==len(pngs)==18
assert all(row['status']==409 and row['before']==row['after'] and row['keyboard_submit'] for row in rows)
assert sum(sum(value is True for value in row['checks'].values()) for row in rows)==72
assert sum(sum(value is False for value in row['checks'].values()) for row in rows)==36
assert sum(len(row['pageerrors']) for row in rows)==18
assert all(all('ViewTransition opt-in disabled' in error['message'] for error in row['pageerrors']) for row in rows)
for item in pngs:
    path=OUT/item['path']
    assert sha(path)==item['sha256']
    assert path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',path.read_bytes()[16:24])==(item['width'],item['height'])
links=0
for path in OUT.glob('*.md'):
    text=path.read_text(encoding='utf-8')
    assert not re.search(r'[ \t]+$',text,re.M),path
    for target in re.findall(r'\[[^]\n]+\]\(([^)\n]+)\)',text):
        if target.startswith(('https://','http://','#')):continue
        assert (path.parent/target.split('#',1)[0]).exists(),(path,target)
        links+=1
for path in OUT.glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
manifest={str(path.relative_to(OUT)).replace('\\','/'):sha(path) for path in sorted(OUT.rglob('*'))
          if path.is_file() and path.name not in {'verification.json','artifact-manifest.json'}}
(OUT/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
data['metadata_integrity']={'decision':'VERIFIED evidence integrity only; SOCIAL03 remains OPEN',
    'source1019_match':True,'shared_mo_match':True,'head_branch_index_active_run_match':True,
    'application_changes':0,'new_application_test_file':False,'origin_divergence':[0,0],
    'png_sha_dimensions_verified':18,'document_links_verified':links,'git_diff_check_exit':0,
    'proposal_check_exit':0,'artifact_manifest_files':len(manifest)}
(OUT/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data['metadata_integrity']))
