import json
import subprocess
from pathlib import Path

QA=Path(__file__).resolve().parent
cases=json.loads((QA/'cases.json').read_text())
rows=json.loads((QA/'flows.json').read_text(encoding='utf-8')) if (QA/'flows.json').exists() else []
done={r['item']['key'] for r in rows if all(r['checks'].values())}
for item in cases:
    if 'action' not in item or item['key'] in done:continue
    item.update(prefix={'ru':'/ru','az':'','en':'/en'}[item['lang']],width=1440 if item['lang']=='en' else 390)
    code=(QA/'flows.js').read_text(encoding='utf-8').replace('__ITEM__',json.dumps(item))
    (QA/'flow-cell.js').write_text(code,encoding='utf-8')
    result=subprocess.run(['python3',str(QA/'browser_driver.py'),'flow-cell.js'],capture_output=True,text=True,encoding='utf-8')
    raw=result.stdout+result.stderr
    if result.returncode or '### Result\n' not in raw:
        (QA/('flow-error-'+item['key']+'.txt')).write_text(raw,encoding='utf-8')
        raise SystemExit('QA flow failure '+item['key'])
    row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0])
    rows.append(row);(QA/'flows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(item['key'],row['status'],{k:v for k,v in row['checks'].items() if not v},flush=True)
    assert all(row['checks'].values()),item['key']
print('Native30flows completed')
