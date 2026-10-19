import json
from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module10-sequential-2026-10-18-pc-r1');read=lambda p:json.loads(p.read_text());n=read(O/'evidence/browser-final-public.json');r=read(O/'evidence/browser-final-retired-r2.json');assert not n['errors'] and not n['pageerrors'] and not r['errors'] and not r['pageerrors'];assert all(v for row in r['rows'] for v in row['checks'].values())
replacements={row['id']:row for row in r['rows'] if '-events-' in row['id']};assert len(replacements)==18;rows=[]
for row in n['rows']:
 if row['id'] in replacements:
  assert {k for k,v in row['checks'].items() if not v}=={'correct_status','noindex','recovery_links'};rows.append(replacements[row['id']])
 else:assert all(row['checks'].values());rows.append(row)
assert len(rows)==181 and all(v for row in rows for v in row['checks'].values());d={'rows':rows,'errors':[],'pageerrors':[],'scope':'Composed final current-source acceptance:162passing ON-fixture public route cells plus18fresh OFF-precondition410cells and original read-only control. First raw matrix retained54observer precondition failures:events ON200 was correct. Native setup/restore checks retained separately, original eventflagTRUE restored with exactly2synthetic logs; no public GET mutations.','raw_sources':['browser-final-public.json','browser-final-retired-r2.json']};(O/'evidence/final-browser-acceptance.json').write_text(json.dumps(d,indent=2));print({'rows':181,'checks':sum(len(row['checks']) for row in rows),'all_PASS':True})
