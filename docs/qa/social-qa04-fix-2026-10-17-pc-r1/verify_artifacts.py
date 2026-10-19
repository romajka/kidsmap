"""Verify approved SOCIAL04 source and recorded local evidence, without tests.

Only this package's manifest/verification metadata are written. Original
pre-patch reports, assertions, application files and Git state are read-only.
"""
import ast
import hashlib
import json
import re
import struct
import subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
QA=ROOT/'.tmp/social04-pc-fix-r1'
PLAN=ROOT/'docs/qa/social-qa04-recheck-2026-10-16-pc-r1'
GUIDE=ROOT/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
TEMPLATE='src/catalog/templates/pages/account_notifications.html'
CSS='static/css/pages/account_notifications.css'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))
def git(*args):
    r=subprocess.run(['git','-c','core.quotepath=false',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert r.returncode==0,(args,r.stderr)
    return r.stdout.rstrip('\r\n')
entry,green=read('source-entry.json'),read('green-source.json')
assert len(entry['sources'])==1020 and len(green['sources'])==1021
assert set(green['sources'])==set(entry['sources'])|{CSS}
assert all(sha(ROOT/p)==h for p,h in green['sources'].items())
assert all(sha(ROOT/p)==h for p,h in entry['sources'].items() if p!=TEMPLATE)
assert all(sha(ROOT/p)==h for p,h in entry['shared_mo'].items())
assert sha(ROOT/'.cbmignore')==entry['cbmignore_sha256']
assert git('rev-parse','HEAD')==entry['head']
assert git('branch','--show-current')==entry['branch']
assert git('rev-parse','task33-progress')==entry['task33_ref']
assert git('rev-parse','HEAD^{tree}')==entry['index_tree']
git('diff','--cached','--exit-code')
git('diff','--check')
assert all(line==line.rstrip() for line in (ROOT/CSS).read_text().splitlines())
allowed={line[3:] for line in entry['status'].splitlines()}|{TEMPLATE,CSS}
for line in git('status','--porcelain=v1','-uall').splitlines():
    assert line[3:] in allowed or line[3:].startswith('docs/qa/social-qa04-fix-2026-10-17-pc-r1/'),line
active=[s for s in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if s.startswith('active_run:')]
assert active==entry['active_run']==['active_run: NONE']
note=(OUT/'status-note.md').read_bytes().rstrip(b'\r\n')+b'\n\n'
assert GUIDE.read_bytes().count(note)==1
assert hashlib.sha256(GUIDE.read_bytes().replace(note,b'',1)).hexdigest()==entry['guide_sha256']
prior={}
for name in ['module09-pc-resume-2026-10-16-r1','social-qa03-fix-2026-10-16-pc-r1','social-qa04-recheck-2026-10-16-pc-r1']:
    folder=ROOT/'docs/qa'/name
    manifest=json.loads((folder/'artifact-manifest.json').read_text(encoding='utf-8'))
    assert all(sha(folder/p)==h for p,h in manifest.items())
    prior[name]=len(manifest)
approval=read('approval.json')
assert approval['message']=='одобряю' and set(approval['scope'])=={TEMPLATE,CSS}
assert approval['plan_sha256']==sha(PLAN/'IMPLEMENTATION_PLAN.md')
for p in [TEMPLATE,CSS]:
    assert (ROOT/p).read_text(encoding='utf-8')==(PLAN/'candidate'/Path(p).name).read_text(encoding='utf-8')
    assert sha(ROOT/p)==read('patch-scope.json')[p]['sha256']
original=git('show','HEAD:'+TEMPLATE)
current=(ROOT/TEMPLATE).read_text(encoding='utf-8')
assert re.findall(r'<form[^>]*>',original)==re.findall(r'<form[^>]*>',current)
assert original.count('{% csrf_token %}')==current.count('{% csrf_token %}')==4
assert re.findall(r'{% url [^%]+%}',original)==re.findall(r'{% url [^%]+%}',current)

matrix=read('matrix.json')
expected={(s,l,w) for s in ['empty','unread','read','invitation','revoked','expired']
          for l in ['ru','az','en'] for w in [360,390,768,1024,1280,1440]}
assert len(matrix)==108 and {(r['item']['state'],r['item']['lang'],r['item']['width']) for r in matrix}==expected
assert all(all(v is True for v in r['controls'].values()) and all(v is True for v in r['style_checks'].values()) for r in matrix)
assert sum(len(r['controls']) for r in matrix)==1188 and sum(len(r['style_checks']) for r in matrix)==1368
assert all(r['before']==r['after'] and not r['facts']['overflow'] and not r['http_failures'] for r in matrix)
assert all('actions_min44' not in r['style_checks'] for r in matrix if not r['facts']['buttons'])
flows,guards,smoke,focus=map(read,['flows.json','guards.json','smoke.json','focus.json'])
for rows,count,observations in [(flows,30,279),(guards,3,24),(smoke,30,144),(focus,6,18)]:
    assert len(rows)==count and sum(len(r['checks']) for r in rows)==observations
    assert all(all(v is True for v in r['checks'].values()) for r in rows)
assert len({r['item']['key'] for r in flows})==30
assert sum(r['status']==400 for r in flows)==3 and sum(r['status']==409 for r in flows)==3
assert sum(r['status'] is None for r in flows)==3
assert sum(bool(r['loading']) for r in flows)==3 and sum(bool(r['fixtureEvent']) for r in flows)==3
assert {r['lang'] for r in guards}=={'ru','az','en'}
assert {(r['lang'],r['width']) for r in focus}=={(l,w) for l in ['ru','az','en'] for w in [390,1440]}
assert all(r['facts']['ratio']>=3 for r in focus)
assert all(c['ratio']>=4.5 for r in matrix for c in r['contrast'])
assert sum(len(r.get('pageerrors',[])) for rows in [matrix,flows,smoke] for r in rows)==0
assert sum('key' in r for r in smoke)==12 and sum('surface' in r for r in smoke)==18
assert not any(r['facts']['overflow'] for r in smoke)
baseline=(OUT/'green.log').read_text(encoding='utf-8')
assert int((OUT/'green.exit').read_text())==0 and '\nOK\n' in baseline and 'Ran 4 tests in 1.400s' in baseline
assert len(set(re.findall(r'^(test_\w+) \(',baseline,re.M)))==4
runtime=read('runtime-info.json')['info']
assert read('live-final.json')==runtime and runtime['testing'] and runtime['source_files']==1021
assert all(runtime['hashes'][p]==green['sources'][p] for p in [TEMPLATE,CSS])
locales=read('locale-manifest.json')
assert set(locales['locales'])=={'ru','az','en'} and len(locales['entries'])==3
assert runtime['sole_locales']==[locales['locale_root']]
for p in locales['entries']:
    assert sha(ROOT/'locale'/p['source'])==p['po_sha256']
    assert sha(QA/'locales'/p['snapshot'])==p['po_sha256']
    assert sha(QA/'locales'/p['mo'])==p['mo_sha256']
pngs=read('png-manifest.json')
assert len(pngs)==174 and len({p['path'] for p in pngs})==174
assert {p['path'] for p in pngs}=={p.relative_to(OUT).as_posix() for p in (OUT/'screenshots').glob('*.png')}
for p in pngs:
    raw=(OUT/p['path']).read_bytes()
    assert sha(OUT/p['path'])==p['sha256'] and raw[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',raw[16:24])==(p['width'],p['height']) and p['native']
for r in matrix+flows+smoke:
    assert (OUT/r['png']).exists()
    if r.get('errorPng'):assert (OUT/r['errorPng']).exists()
byname=lambda s:{l.split()[1]:l.split()[:3] for l in s.splitlines() if l.strip()}
before=byname((OUT/'containers-entry.txt').read_text())
after=byname((OUT/'containers-final.txt').read_text())
assert len(before)==30 and all(after.get(k)==v for k,v in before.items())
links=0
for p in OUT.glob('*.md'):
    text=p.read_text(encoding='utf-8')
    assert not re.search(r'[ \t]+$',text,re.M),p
    base=GUIDE.parent if p.name=='status-note.md' else p.parent
    for link in re.findall(r'\[[^]\n]+\]\(([^)\n]+)\)',text):
        if link.startswith(('http://','https://','#')):continue
        assert (base/link.split('#',1)[0]).exists(),(p,link)
        links+=1
for p in OUT.glob('*.py'):
    ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
assert not any((OUT/p).exists() for p in ['qa_settings.py','runtime.py','storage-state.json','.env'])
manifest={p.relative_to(OUT).as_posix():sha(p) for p in sorted(OUT.rglob('*'))
          if p.is_file() and p.name not in ['artifact-manifest.json','verification.json']}
(OUT/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
data=read('verification.json')
data['metadata_gate']='VERIFIED approved source/evidence integrity; SOCIAL04 scoped LOCAL closure, module09 OPEN'
data['final_verified_at']=datetime.now(timezone(timedelta(hours=4))).isoformat(timespec='seconds')
data['metadata_integrity']={'source1021_match_green':True,'outside_approved_source_match_entry':True,
    'approved_candidate_matches':2,'original_forms_csrf_urls_retained':True,'existing_assertions_changed':False,
    'head_branch_task33_index_active_run_shared_mo_cbmignore_match':True,'guide_original_bytes_preserved':True,
    'prior_manifests':prior,'entry30container_ids_states_match':True,'png_sha_dimensions_verified':174,
    'document_links_verified':links,'python_helpers_ast_verified':True,'git_diff_check_exit':0,
    'artifact_manifest_files':len(manifest)}
(OUT/'verification.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(data['metadata_integrity']))
