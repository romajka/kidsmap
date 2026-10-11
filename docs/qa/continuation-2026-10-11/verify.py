"""Validate documentation coverage/links and preservation; never runs KidsMap."""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GUIDE = ROOT / 'docs/qa/continuation-and-repair-prompts-2026-10-11.md'
checks = []

def check(name, passed, **details):
    checks.append({'check':name,'status':'PASS' if passed else 'FAIL',**details})

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def git(*args):
    return subprocess.check_output(['git', *args],cwd=ROOT).decode('utf-8').strip()

s = GUIDE.read_text(encoding='utf-8')
index = load(HERE/'repair-index.json')
inputs = load(HERE/'transfer-inputs.json')
ledger = load(ROOT/'docs/qa/module13-2026-10-11-r1/reconciliation/historical-findings.json')
groups = index['groups']
expected = {f['id'] for f in ledger['findings'] if not f['id'].startswith('PLACE-QA-')}
expected.update(['CROSS-QA-01','CROSS-QA-02'])
ids = [key for group in groups for key in group['ids']]
keys = [group['key'] for group in groups]
check('remaining historical queue has 76 IDs exactly once', len(ids)==len(set(ids))==76 and set(ids)==expected,
      count=len(ids),missing=sorted(expected-set(ids)),unexpected=sorted(set(ids)-expected))
check('73 repair groups and unique PLAN headings',len(groups)==len(set(keys))==73 and
      set(re.findall(r'^#### PLAN ([\w-]+) ·',s,re.M))==set(keys),count=len(groups))
check('closed PLACE IDs and CROSS alias excluded from open queue',
      not any(key.startswith('PLACE-QA-') or key=='CROSS-QA-03' for key in ids))
actual_groups = {g['key']:g['ids'] for g in groups if len(g['ids'])>1}
check('shared root causes grouped as documented', actual_groups=={
 'NETWORK-GRANT-UI':['ORG-QA-02','ACCESS-QA-03'],
 'COMPILED-LOCALE-FRESHNESS':['EVENT-QA-01','PUBLIC-QA-03','SITE-QA-07']})
check('13 ACCEPT headings',re.findall(r'^### ACCEPT-(\d\d)\.',s,re.M)==[f'{n:02d}' for n in range(1,14)])
fences = re.findall(r'^```([^\n]*)$',s,re.M)
blocks = re.findall(r'^```text\n(.*?)\n```$',s,re.M|re.S)
check('88 complete copyable blocks and balanced fences',len(blocks)==88 and fences==['text','']*88,
      block_count=len(blocks),fence_count=len(fences))
plan_blocks = [b for b in blocks if b.startswith('KidsMap: PLAN ')]
check('every PLAN has plan-only gate, preservation and isolation',len(plan_blocks)==73 and all(all(term in b for term in [
 'ЭТАП ЭТОГО ПРОМПТА: только свежий recheck и конкретный план','dirty WORKTREE/active_run',
 'DJANGO_TESTING=1','LOCALE_PATHS','одобрение конкретного scope','не сохраняй credentials'])
 for b in plan_blocks))
accept_blocks = [b for b in blocks if b.startswith('KidsMap: ACCEPT-')]
check('every ACCEPT explicitly AUDIT ONLY and uses fresh runtime/locales',len(accept_blocks)==13 and all(
 all(term in b for term in ['Режим строго AUDIT ONLY','DJANGO_TESTING=1','LOCALE_PATHS',
 'Без commit/push/deploy/production','NOT RUN']) for b in accept_blocks))

source = (ROOT/'docs/qa/module-acceptance-prompts.md').read_text(encoding='utf-8-sig')
heads = list(re.finditer(r'^## (\d\d)\. ([^\n]+)',source,re.M))
missing_audit_specs = []
for i,m in enumerate(heads):
    part=source[m.end():heads[i+1].start() if i+1<len(heads) else len(source)]
    original = re.findall(r'```text\s*\n(.*?)\n```',part,re.S)[0]
    adapted = original.replace('На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout.',
                               'На этом ПК сначала определи фактический путь checkout.')
    if adapted not in accept_blocks[i]: missing_audit_specs.append(m[1])
check('all 13 complete canonical module specifications retained',not missing_audit_specs,missing=missing_audit_specs)

outside = re.sub(r'^```text\n.*?\n```$', '', s, flags=re.M|re.S)
anchors = re.findall(r'<a id="([^"]+)"',outside)
links = re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',outside)
bad_links=[]
for target in links:
    if target.startswith('#'):
        if target[1:] not in anchors: bad_links.append(target)
    elif not (GUIDE.parent/target).is_file(): bad_links.append(target)
check('local Markdown links and anchors resolve',not bad_links,links=len(links),bad_links=bad_links)
check('HTML anchors unique',len(anchors)==len(set(anchors)),count=len(anchors))
table = re.search(r'^\| Модуль \|.*?(?=\n\n)',s,re.M|re.S)
table_lines = table.group().splitlines() if table else []
check('module table renders as 13 contiguous rows',len(table_lines)==15 and all(x.startswith('|') for x in table_lines),lines=len(table_lines))
missing_inputs=[p for p in inputs['required_entry_inputs'] if not (ROOT/p).is_file()]
check('required transfer inputs exist',not missing_inputs,count=len(inputs['required_entry_inputs']),missing=missing_inputs)

app_preservation = 'NOT RUN; initial local snapshot is not transferred by Git'
baseline_path = ROOT/'.tmp/continuation-docs-20261011/preservation-before.json'
if baseline_path.is_file():
    baseline=load(baseline_path)
    changed=[p for p,h in baseline['app_hashes'].items() if not (ROOT/p).is_file() or hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
    check('pre-existing source/scripts/locale/agent/CI files preserved',not changed,
          files=len(baseline['app_hashes']),changed=changed)
    check('HEAD and branch preserved',git('rev-parse','HEAD')==baseline['head'] and git('branch','--show-current')==baseline['branch'])
    current=set(git('status','--porcelain=v1','-uall').splitlines())
    before=set(baseline['status'].splitlines())
    delta=sorted(current-before)
    missing=sorted(before-current)
    allowed=lambda row: row.startswith('?? docs/qa/continuation-2026-10-11/') or row=='?? docs/qa/continuation-and-repair-prompts-2026-10-11.md'
    check('only new continuation documents added to Git inventory',not missing and all(allowed(row) for row in delta),new_paths=delta,missing_prior_entries=missing)
    app_preservation = 'Verified against initial ignored local snapshot; no application tests executed'
else:
    checks.append({'check':'initial local preservation snapshot','status':'NOT RUN','reason':'Not portable; fresh checkout needs own snapshot'})
active=(ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8-sig')
check('active_run remains NONE at preparation',bool(re.search(r'^active_run:\s*NONE\s*$',active,re.M)))
check('no replacement characters/NUL/secret value markers', '\ufffd' not in s and '\x00' not in s and
      not re.search(r'(?i)(?:password|secret_key|access_token|api_key)\s*[:=]\s*[\x22\x27][^\x22\x27\s]{8,}',s))

result={'scope':'DOCUMENTATION VERIFICATION ONLY; historical application results are not new tests',
 'command': '.venv/Scripts/python.exe docs/qa/continuation-2026-10-11/verify.py',
 'guide_sha256':hashlib.sha256(GUIDE.read_bytes()).hexdigest(),
 'guide_bytes':GUIDE.stat().st_size,'remaining_ids':len(ids),'repair_groups':len(groups),
 'accept_prompts':len(accept_blocks),'copyable_blocks':len(blocks),
 'checks':checks,'application_preservation':app_preservation,
 'application_tests_run':False,'browser_tests_run':False,'commit_push_deploy_run':False,
 'status':'FAIL' if any(c['status']=='FAIL' for c in checks) else 'PASS'}
(HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[c for c in checks if c['status']=='FAIL'],
                  'repair_groups':len(groups),'remaining_ids':len(ids),'copyable_blocks':len(blocks)},ensure_ascii=False))
sys.exit(0 if result['status']=='PASS' else 1)
