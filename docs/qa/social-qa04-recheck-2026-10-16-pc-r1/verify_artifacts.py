"""Verify bounded PLAN04 evidence/source. No Django/tests/production execution.

Writes only this package's artifact manifest and verification metadata.
Run in the original checkout while this recorded WORKTREE remains current.
"""
import ast
import hashlib
import json
import re
import struct
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
QA=ROOT/'.tmp/social04-pc-plan-r1'
GUIDE=ROOT/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))
def git(*args):
    r=subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert r.returncode==0,(args,r.stderr)
    return r.stdout.rstrip('\r\n')

entry=read('source-entry.json')
data=read('verification.json')
assert len(entry['sources'])==1020
assert read('source-final.json')['sources']==entry['sources']
assert all(sha(ROOT/p)==h for p,h in entry['sources'].items())
assert all(sha(ROOT/p)==h for p,h in entry['shared_mo'].items())
assert sha(ROOT/'.cbmignore')==entry['cbmignore_sha256']
assert git('rev-parse','HEAD')==entry['head']
assert git('branch','--show-current')==entry['branch']
assert git('rev-parse','task33-progress')==entry['task33_ref']
assert git('rev-parse','HEAD^{tree}')==entry['index_tree']
git('diff','--cached','--exit-code')
git('diff','--check')
entry_paths={line[3:] for line in entry['status'].splitlines()}
for line in git('status','--porcelain=v1','-uall').splitlines():
    p=line[3:]
    assert p in entry_paths or p.startswith('docs/qa/social-qa04-recheck-2026-10-16-pc-r1/'),line
active=[line for line in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines()
        if line.startswith('active_run:')]
assert active==entry['active_run']==['active_run: NONE']
note=(OUT/'status-note.md').read_bytes().rstrip(b'\r\n')+b'\n\n'
assert GUIDE.read_bytes().count(note)==1
assert hashlib.sha256(GUIDE.read_bytes().replace(note,b'',1)).hexdigest()==entry['guide_sha256']
prior_counts={}
for name in ['module09-pc-resume-2026-10-16-r1','social-qa03-fix-2026-10-16-pc-r1']:
    folder=ROOT/'docs/qa'/name
    m=json.loads((folder/'artifact-manifest.json').read_text(encoding='utf-8'))
    assert all(sha(folder/p)==h for p,h in m.items())
    prior_counts[name]=len(m)
candidate=read('candidate-manifest.json')
assert set(candidate)=={'account_notifications.html','account_notifications.css'}
assert all(sha(OUT/'candidate'/p)==h for p,h in candidate.items())
assert not (ROOT/'static/css/pages/account_notifications.css').exists()
git('apply','--check','--ignore-space-change',str(OUT/'proposed.diff'))
original=(ROOT/'src/catalog/templates/pages/account_notifications.html').read_text(encoding='utf-8')
proposed=(OUT/'candidate/account_notifications.html').read_text(encoding='utf-8')
assert re.findall(r'<form[^>]*>',original)==re.findall(r'<form[^>]*>',proposed)
assert original.count('{% csrf_token %}')==proposed.count('{% csrf_token %}')==4
assert re.findall(r'{% url [^%]+%}',original)==re.findall(r'{% url [^%]+%}',proposed)
head_template=git('show','HEAD:src/catalog/templates/pages/account_notifications.html')
assert original.rstrip('\r\n')==head_template
assert data['application_changes_this_run']==0 and data['proposal']['applied'] is False
assert data['proposal']['candidate_rendered'] is False

rows=read('matrix.json')
expected={(s,l,w) for s in ['empty','unread','read','invitation','revoked','expired']
          for l in ['ru','az','en'] for w in [360,390,768,1024,1280,1440]}
assert len(rows)==108
assert {(r['item']['state'],r['item']['lang'],r['item']['width']) for r in rows}==expected
assert all(r['status']==200 and len(r['controls'])==11 and all(v is True for v in r['controls'].values()) for r in rows)
assert all(r['before']==r['after'] for r in rows)
assert sum(sum(v is False for v in r['style_checks'].values()) for r in rows)==684
raw_true=[(r,k) for r in rows for k,v in r['style_checks'].items() if v is True]
assert len(raw_true)==18 and all(r['item']['state']=='read' and k=='actions_min44' and not r['facts']['buttons']
                              for r,k in raw_true)
assert all(r['style_checks']['account_css_loaded'] is False for r in rows)
assert not any(r['facts']['overflow'] or r['http_failures'] or r['pageerrors'] for r in rows)
neighbors=read('neighbors.json')
assert len(neighbors)==6 and all(all(v is True for v in r['checks'].values()) for r in neighbors)
assert {(r['lang'],r['width']) for r in neighbors}=={(l,w) for l in ['ru','az','en'] for w in [390,1440]}
assert not any(r['pageerrors'] for r in neighbors)
assert sum(len(r['request_failed']) for r in neighbors)==6
assert all('fonts.googleapis.com' in f['url'] and 'BLOCKED_BY_CLIENT' in f['error']
           for r in neighbors for f in r['request_failed'])
baseline=(OUT/'baseline.log').read_text(encoding='utf-8')
assert int((OUT/'baseline.exit').read_text())==0
assert 'Ran 4 tests in 1.502s' in baseline and '\nOK\n' in baseline
assert len(set(re.findall(r'^(test_\w+) \(',baseline,re.M)))==4

pngs=read('png-manifest.json')
assert len(pngs)==114 and len({p['path'] for p in pngs})==114
assert {p['path'] for p in pngs}=={p.relative_to(OUT).as_posix() for p in (OUT/'screenshots').glob('*.png')}
for p in pngs:
    raw=(OUT/p['path']).read_bytes()
    assert sha(OUT/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',raw[16:24])==(p['width'],p['height']) and p['native'] is True
assert all((OUT/r['png']).exists() for r in rows+neighbors)
live=read('live-final.json')
assert live==read('runtime-info.json')['info']
assert live['testing'] and live['source_files']==1020
assert live['template_sha256']==entry['sources']['src/catalog/templates/pages/account_notifications.html']
locale=read('locale-manifest.json')
assert set(locale['locales'])=={'ru','az','en'} and len(locale['entries'])==3
assert live['sole_locales']==[locale['locale_root']]
for p in locale['entries']:
    assert sha(ROOT/'locale'/p['source'])==p['po_sha256']
    assert sha(QA/'locales'/p['snapshot'])==p['po_sha256']
    assert sha(QA/'locales'/p['mo'])==p['mo_sha256']
byname=lambda lines:{s.split()[1]:s.split()[:3] for s in lines if s.strip()}
before=byname((OUT/'containers-entry.txt').read_text().splitlines())
after=byname((OUT/'containers-final.txt').read_text().splitlines())
assert len(before)==28 and all(after.get(k)==v for k,v in before.items())

links=0
for p in OUT.glob('*.md'):
    text=p.read_text(encoding='utf-8')
    assert not re.search(r'[ \t]+$',text,re.M),p
    base=GUIDE.parent if p.name=='status-note.md' else p.parent
    for target in re.findall(r'\[[^]\n]+\]\(([^)\n]+)\)',text):
        if target.startswith(('http://','https://','#')):
            continue
        assert (base/target.split('#',1)[0]).exists(),(p,target)
        links+=1
for p in OUT.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
assert not any((OUT/p).exists() for p in ['qa_settings.py','runtime.py','storage-state.json','.env'])
manifest={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
          if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(OUT/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
data['metadata_gate']='VERIFIED source/evidence integrity only; SOCIAL04 remains OPEN, approval PENDING'
data['final_verified_at']=datetime.now(timezone(timedelta(hours=4))).isoformat(timespec='seconds')
data['metadata_integrity']={'source1020_match':True,'application_changes_this_run':0,
    'head_branch_index_task33_active_run_shared_mo_match':True,'cbmignore_match':True,
    'guide_original_bytes_preserved':True,'prior_artifact_manifests':prior_counts,
    'proposal_apply_check_exit':0,'candidate_forms_urls_csrf_match':True,
    'png_sha_dimensions_verified':114,'links_verified':links,'python_helpers_ast_verified':True,
    'style_failures_preserved':684,'raw_true_na_slots':18,'product_style_pass':0,
    'entry28container_ids_states_match':True,'git_diff_check_exit':0,'artifact_manifest_files':len(manifest)}
(OUT/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data['metadata_integrity']))
