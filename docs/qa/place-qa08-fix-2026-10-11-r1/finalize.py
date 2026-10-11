"""Verify preservation, update only journal row01, then verify again."""
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
STATE=ROOT/'.tmp/place-qa08-fix-20261011-r1'
entry=json.loads((HERE/'entry.json').read_text(encoding='utf-8'))
foreign=json.loads((HERE/'foreign-entry.json').read_text(encoding='utf-8'))
allowed={'locale/ru/LC_MESSAGES/django.po','docs/qa/module-acceptance-prompts.md','src/catalog/testcases/test_place_qa08_district_localization.py'}
changed=[];missing=[]
for path,sha in foreign.items():
    if path in allowed:continue
    full=ROOT/path
    if not full.is_file():missing.append(path)
    elif hashlib.sha256(full.read_bytes()).hexdigest()!=sha:changed.append(path)
before=(STATE/'ru-po-before.bin').read_bytes()
old='#~ msgid "Выберите район"\r\n#~ msgstr "Выберите район"'.encode('utf-8')
new='msgid "Выберите район"\r\nmsgstr "Выберите район"'.encode('utf-8')
po_ok=(ROOT/'locale/ru/LC_MESSAGES/django.po').read_bytes()==before.replace(old,new,1)
shared_ok=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in entry['source_files'].items() if p.endswith('.mo'))
active=next(x.split(':',1)[1].strip() for x in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if x.startswith('active_run:'))
containers=subprocess.check_output(['wsl.exe','--','docker','ps','--format','{{.ID}} {{.Names}} {{.Ports}}'],text=True).splitlines()
listeners=json.loads(subprocess.check_output(['powershell.exe','-NoProfile','-Command',"Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Compress"],text=True))
protected=[x for x in entry['listeners'] if 8800<=x['LocalPort']<=8841 or 55442<=x['LocalPort']<=55446]
def signature(x):return(x['LocalAddress'],x['LocalPort'],x['OwningProcess'])
listener_ok=all(signature(x) in {signature(y) for y in listeners} for x in protected)
with urllib.request.urlopen('http://localhost:8842/qa/version/',timeout=40) as response:version=json.load(response)
snap=json.loads((HERE/'runtime-snapshot.json').read_text(encoding='utf-8'))
source_changed=[p for p,sha in entry['source_files'].items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=sha and p not in allowed]
secret=(STATE/'credential').read_bytes()
leaks=[p.relative_to(ROOT).as_posix() for p in HERE.rglob('*') if p.is_file() and secret in p.read_bytes()]
counts=json.loads((HERE/'counts.json').read_text(encoding='utf-8'))
qa_hashes=json.loads((HERE/'qa-runtime-hashes.json').read_text(encoding='utf-8'))
checks={
 'foreign_files_preserved':not changed and not missing,
 'ru_po_only_exact_two_line_change':po_ok,
 'all_shared_mo_preserved':shared_ok,
 'other_application_source_preserved':not source_changed,
 'head_preserved':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==entry['head'],
 'branch_preserved':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()==entry['branch'],
 'active_run_preserved':active==entry['active_run']=='NONE',
 'foreign_containers_preserved':all(line in containers for line in entry['containers']),
 'foreign_listener_pids_preserved':listener_ok,
 'own_runtime_startup_disk_match':version['snapshot_matches_startup'] and version['startup_matches_disk'] and version['disk_digest']==snap['source_digest'],
 'own_qa_runtime_files_preserved':all(hashlib.sha256((HERE/p).read_bytes()).hexdigest()==sha for p,sha in qa_hashes.items()),
 'credential_absent_from_artifacts':not leaks,
 'scratch_credential_is_ignored':subprocess.run(['git','check-ignore','-q',str(STATE/'credential')],cwd=ROOT).returncode==0,
 'all_scoped_browser_checks_pass':counts['browser']['PASS']==87 and counts['browser']['FAIL']==0,
}
assert all(checks.values()), {'failed':[k for k,v in checks.items() if not v],'foreign_changed':changed,'foreign_missing':missing,'source_changed':source_changed,'leaks':leaks}
journal=ROOT/'docs/qa/module-acceptance-prompts.md'
original=(STATE/'journal-before.bin').read_bytes()
assert journal.read_bytes()==original,'Foreign journal drift; do not overwrite'
old_row=next(line for line in original.splitlines(keepends=True) if line.startswith(b'| 01 |'))
text=old_row.decode('utf-8')
text=text.replace('DONE — FAIL (scoped recheck: PLACE-QA-01–07 PASS; RU district P3 OPEN; full limits NOT RUN)','DONE — scoped PASS (PLACE-QA-01–07 recheck + PLACE-QA-08 repair; full module01 NOT RUN)')
text=text.replace('new localhost:8841 + isolated fresh PO/MO','recheck localhost:8841; repair localhost:8842 + new isolated fresh PO/MO')
text=text.replace('; [история r2]', '; [PLACE-QA-08 repair](place-qa08-fix-2026-10-11-r1/REPORT.md), [repair verification](place-qa08-fix-2026-10-11-r1/verification.json); [история r2]')
text=text.replace('remaining PLACE-QA-08 alias CROSS-QA-03;', 'PLACE-QA-08 alias CROSS-QA-03 closed in fresh isolated repair profile: 6 Django PASS, browser87P/0F, 24 native PNG;')
assert text!=old_row.decode('utf-8') and 'P3 OPEN' not in text
replacement=text.encode('utf-8')
updated=original.replace(old_row,replacement,1)
journal.write_bytes(updated)
checks['journal_only_row01_changed']=journal.read_bytes().replace(replacement,old_row,1)==original
checks['final_runtime_source_still_matches']=version['disk_digest']==snap['source_digest']
verification={'checks':checks,'passed':sum(checks.values()),'total':len(checks),'foreign_file_count':len(foreign),'foreign_changed':changed,'foreign_missing':missing,'other_source_changed':source_changed,'active_run':active,'protected_listeners':protected,'foreign_containers':entry['containers'],'own_runtime':version,'authorized_application_changes':['RU PO entry reactivation','new test_place_qa08_district_localization.py'],'journal_scope':'row01 only','credential_leaks':leaks}
(HERE/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
assert all(checks.values())
print('Final preservation verification:',sum(checks.values()),'/',len(checks),'PASS; journal row01 only')
