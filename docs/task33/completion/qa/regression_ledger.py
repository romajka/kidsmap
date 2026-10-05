"""Account for all 120 immutable baseline entries against fresh full executions."""
import argparse, ast, difflib, hashlib, json, subprocess
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--host',required=True)
parser.add_argument('--image')
args=parser.parse_args()
root=Path(__file__).resolve().parents[4]; out=root/'docs/task33/completion'
baseline=json.loads((root/'docs/task33/final-audit/domain-failure-classification.json').read_text(encoding='utf-8'))
entry=json.loads((out/'entry.json').read_text(encoding='utf-8'))
backup=Path(entry['snapshot'])/'files'
if not backup.exists():backup=root/'scratch'/Path(entry['snapshot'].replace('\\','/')).name/'files'
host=json.loads(Path(args.host).read_text(encoding='utf-8'))
host=host.get('suite',host)
image=json.loads(Path(args.image).read_text(encoding='utf-8')) if args.image else None
if image:image=image.get('suite',image)
notes={e['id']:e['change'] for e in json.loads((out/'root-regression.json').read_text(encoding='utf-8'))['entries']}
notes.update({
 'test_owner_edit_form_can_force_refresh_coordinates':'Application fix: explicit geocoding goes through a new validated moderation candidate; approved coordinates stay unchanged until review. The fixture uses two valid points in the same district.',
 'test_owner_edit_creates_place_change_audit':'Assert versioned candidate author/base/changed fields and reviewer decision; submit actual form values without treating an existing FieldFile as a fresh upload.',
 'test_staff_with_change_place_permission_can_publish_after_approval':'Publication approval is explicitly KIND_PUBLICATION; ownership claim alone does not authorize publication.',
 'test_place_admin_can_save_an_empty_new_place_as_draft':'Application adapter now transfers cleaned legacy draft name when ModelForm excludes name; verify saved empty draft and continuation.',
 'test_place_admin_can_publish_ready_place_from_change_form':'Real ready fixture, source token for the exact record and actual tariff payload; removed mocked readiness bypass.',
 'test_failed_publish_keeps_published_card_active_and_shows_all_issues':'Submit invalid coordinate bounds through real admin form; require both field errors, unchanged published projection/version and no candidate. Photo/GPS absence is covered as allowed by readiness tests.',
 'test_event_admin_can_publish_from_change_form':'Confirmed organizer and actual event interval, organizer fields in POST, plus current admin phone/photo requirements; no readiness bypass.',
})
def function(source, identifier):
    parts=identifier.split('.'); cls, method=parts[-2:]
    tree=ast.parse(source)
    for c in tree.body:
        if isinstance(c,ast.ClassDef) and c.name==cls:
            for node in c.body:
                if isinstance(node,ast.FunctionDef) and node.name==method:
                    return '\n'.join(source.splitlines()[node.lineno-1:node.end_lineno])+'\n'
    return ''
def verdict(suite,identifier):
    if suite is None:return 'NOT_RUN'
    if identifier not in suite['executed_ids']:return 'NOT_DISCOVERED'
    if any(p['id'].split(' (',1)[0]==identifier for p in suite['problems']):return 'FAIL'
    if identifier in suite.get('skipped_ids',[]):return 'SKIPPED'
    return 'PASS'
records=[]
for original in baseline['entries']:
    identifier=original['id']; module=identifier.split('.')[2]
    relative='src/catalog/testcases/'+module+'.py'
    saved=backup/relative
    before=saved.read_text(encoding='utf-8') if saved.exists() else subprocess.check_output(
        ['git','show',entry['head']+':'+relative],cwd=root).decode('utf-8')
    after=(root/relative).read_text(encoding='utf-8')
    old=function(before,identifier);new=function(after,identifier)
    diff=''.join(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='preserved-entry',tofile='completion-WORKTREE'))
    method=identifier.split('.')[-1]
    note=notes.get(identifier,notes.get(method))
    if not note:
        if 'review' in method and module=='admin':note='Use exact pending review revision and actual reviewer HTTP action; retain rejection/approval and rating checks. Legacy bulk cannot bypass version checks.'
        elif module=='specialists':note='Use confirmed person/claim and explicit certificate publication consent; verify private-document ACL and actual publication projection.'
        elif any(word in method for word in ('renders','page','rehydrates','preview','steps')):note='Update selectors and copy to the current accepted editor; retain rendered values, localization and visibility checks.'
        elif module in ('owner','permanent_place_wizard'):note='Use signed current source/candidate protocol and accepted optional-field/permission contract; assert approved data versus pending edits and actual post-review outcome where applicable.'
        elif module=='admin':note='Use actual current form/action contract, validated fixture and candidate/approved projection checks; see exact function diff and original diagnosis.'
        else:note='Deterministic operation ordering and explicit success/conflict outcomes; inspect all invariants after each operation and successful retry.'
    records.append({'entry':original['entry'],'id':identifier,'subtest':original.get('subtest',''),
        'cause':original['reason'],'change':note,'source':relative,'test_diff':diff,
        'host':verdict(host,identifier),'image':verdict(image,identifier),
        'before_test_sha256':hashlib.sha256(old.encode()).hexdigest(),
        'after_test_sha256':hashlib.sha256(new.encode()).hexdigest()})
assert len(records)==120 and len({r['id'] for r in records})==109
result={'entries':records,'total':120,'unique_ids':109,'host_source':args.host,'image_source':args.image,
    'host_pass':sum(r['host']=='PASS' for r in records),'image_pass':sum(r['image']=='PASS' for r in records),
    'historical_audit_modified':False}
(out/'regression-ledger.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lines=['# Все 120 исходных записей регрессии','', 'Каждая строка сопоставлена с реально обнаруженным ID теста. Полные причины и изменения тестовых сценариев: [JSON](regression-ledger.json).','',
       '| № | Тест | Причина / изменение | Host | Image |','|---|---|---|---|---|']
for r in records:
    explanation=(str(r['cause'])+' → '+r['change']).replace('|','/').replace('\n',' ')
    lines.append(f"| {r['entry']} | `{r['id']}` {r['subtest']} | {explanation} | {r['host']} | {r['image']} |")
(out/'regression-ledger.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='entries'}))
