import json
import subprocess
from pathlib import Path

QA=Path(__file__).resolve().parent
rows=[]
(QA/'png').mkdir(exist_ok=True)
for role in ['author','guest']:
    for lang,prefix,heading in [('ru','/ru','Общие отзывы о сайте'),('az','','Sayt haqqında ümumi rəylər'),('en','/en','General site reviews')]:
        for width in [360,390,768,1024,1280,1440]:
            item={'role':role,'lang':lang,'width':width,'url':prefix+'/reviews/','heading':heading}
            (QA/'cell.js').write_text((QA/'matrix-cell.js').read_text(encoding='utf-8').replace('__ITEM__',json.dumps(item,ensure_ascii=False)),encoding='utf-8')
            r=subprocess.run(['python3',str(QA/'browser_driver.py'),'cell.js'],capture_output=True,text=True,encoding='utf-8')
            raw=r.stdout+r.stderr
            if r.returncode or '### Result\n' not in raw:
                (QA/'matrix-error.txt').write_text(raw,encoding='utf-8')
                raise SystemExit('QA matrix error '+str(item))
            row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);rows.append(row)
            (QA/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            assert all(row['controls'].values()),row['controls']
            print(role,lang,width,'document',row['facts']['documentWidth'],'layoutFAIL',sum(not v for v in row['layout'].values()),flush=True)
print(json.dumps({'cells':len(rows),'control_pass':sum(len(r['controls']) for r in rows),
    'layout_pass':sum(sum(r['layout'].values()) for r in rows),'layout_fail':sum(sum(not v for v in r['layout'].values()) for r in rows)}))
