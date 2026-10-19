import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent;targets=json.loads((Q/'targets.json').read_text());cases=[];rows=[]
for target in targets['activities']+targets['shared']:
    for role in ['guest','author']:
        for lang,prefix,h in [('ru','/ru','Отзывы:'),('az','','Rəylər:'),('en','/en','Reviews:')]:
            widths=[360,390,768,1024,1280,1440] if target.get('variant')=='localized' else [390]
            for width in widths:
                item={**target,'role':role,'lang':lang,'prefix':prefix,'width':width,
                    'headingPrefix':h,'expected':target['names'][lang]}
                item['id']='-'.join([target.get('variant',target['kind']),role,lang,str(width)])
                cases.append(item)
for item in cases:
    (Q/'cell.js').write_text((Q/'cell-body.js').read_text().replace('__ITEM__',json.dumps(item,ensure_ascii=False)),encoding='utf-8')
    r=subprocess.run(['python3',str(Q/'browser_driver.py'),'cell.js'],capture_output=True,text=True,encoding='utf-8')
    raw=r.stdout+r.stderr
    if r.returncode or '### Result\n' not in raw:
        (Q/'matrix-error.txt').write_text(raw,encoding='utf-8');raise SystemExit('Native QA error '+item['id'])
    row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);rows.append(row)
    (Q/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert all(row['controls'].values()),(item['id'],row['controls'])
    print(item['id'],'controlsPASS',len(row['controls']),'sourceFAIL',sum(not v for v in row['source'].values()),flush=True)
print(json.dumps({'cells':len(rows),'controlsPASS':sum(sum(r['controls'].values()) for r in rows),
    'sourceFAIL':sum(sum(not v for v in r['source'].values()) for r in rows)}))
