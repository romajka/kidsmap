import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent;cases=[c for c in json.loads((Q/'cases.json').read_text()) if not c['key'].startswith('guard-')];rows=json.loads((Q/'matrix.json').read_text()) if (Q/'matrix.json').exists() else []
for item in cases:
 if any(r['item']['key']==item['key'] for r in rows):continue
 (Q/'cell.js').write_text((Q/'cell-body.js').read_text(encoding='utf-8-sig').replace('__ITEM__',json.dumps(item)))
 r=subprocess.run(['python3',str(Q/'browser_driver.py'),'cell.js'],capture_output=True,text=True)
 raw=r.stdout+r.stderr
 if r.returncode or '### Result\n' not in raw:
  (Q/('failure-'+item['key']+'.txt')).write_text(raw);raise SystemExit('Native harness failed '+item['key'])
 row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);rows.append(row)
 (Q/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 assert all(row['controls'].values()) and all(row['source'].values()),(row['controls'],row['source'])
 assert not row['pageerrors'],row
 assert not row['request_failed'],row['request_failed']
 assert all(c['url'].endswith('/accept/') and '403' in c['text'] for c in row['consoleErrors']),row['consoleErrors']
 assert all(r['status']==403 and r['url'].endswith('/accept/') for r in row['http_failures']),row['http_failures']
 print(item['key'],'controlPASS',len(row['controls']),'sourceFAIL',sum(not v for v in row['source'].values()),flush=True)
print('cells',len(rows),'controlPASS',sum(sum(r['controls'].values()) for r in rows),'sourceFAIL',sum(sum(not v for v in r['source'].values()) for r in rows))


