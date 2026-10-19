import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent;expected=json.loads((Q/'fixtures.json').read_text())['expected'];rows=json.loads((Q/'matrix.json').read_text()) if (Q/'matrix.json').exists() else []
for role in ['guest','author']:
 for lang in ['ru','az','en']:
  for width in [360,390,768,1024,1280,1440]:
   item=dict(role=role,lang=lang,width=width,id=f'{role}-{lang}-{width}')
   if any(r['item']['id']==item['id'] for r in rows):continue
   (Q/'cell.js').write_text((Q/'cell-body.js').read_text(encoding='utf-8-sig').replace('__ITEM__',json.dumps(item)).replace('__EXPECTED__',json.dumps(expected)))
   r=subprocess.run(['python3',str(Q/'browser_driver.py'),'cell.js'],capture_output=True,text=True);raw=r.stdout+r.stderr
   if r.returncode or '### Result\n' not in raw:
    (Q/('failure-'+item['id']+'.txt')).write_text(raw);raise SystemExit('Native failed '+item['id'])
   row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);rows.append(row);(Q/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
   assert all(row['controls'].values()) and all(row['source'].values()),(row['controls'],row['source'])
   assert not row['pageerrors'] and not row['requestfailed'] and not row['http_failures'] and not row['consoleErrors'],row
   print(item['id'],'controlPASS',len(row['controls']),'sourceFAIL',sum(not v for v in row['source'].values()),flush=True)
print('cells',len(rows),'controlPASS',sum(sum(r['controls'].values()) for r in rows),'sourceFAIL',sum(sum(not v for v in r['source'].values()) for r in rows))
