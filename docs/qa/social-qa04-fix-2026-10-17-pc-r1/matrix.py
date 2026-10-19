import json
import subprocess
from pathlib import Path

QA=Path(__file__).resolve().parent
states=['empty','unread','read','invitation','revoked','expired']
langs={'ru':('/ru','Служебные уведомления'),'az':('','Xidməti bildirişlər'),'en':('/en','Service notifications')}
rows=[]
(QA/'png').mkdir(exist_ok=True)
for state in states:
    for lang,(prefix,heading) in langs.items():
        for width in [360,390,768,1024,1280,1440]:
            item={'state':state,'lang':lang,'width':width,'url':prefix+'/account/notifications/','heading':heading}
            code=(QA/'matrix-cell.js').read_text(encoding='utf-8').replace('__ITEM__',json.dumps(item,ensure_ascii=False))
            (QA/'cell.js').write_text(code,encoding='utf-8')
            run=subprocess.run(['python3',str(QA/'browser_driver.py'),'cell.js'],capture_output=True,text=True,encoding='utf-8')
            raw=run.stdout+run.stderr
            if run.returncode or '### Result\n' not in raw:
                (QA/'matrix-error.txt').write_text(raw,encoding='utf-8')
                raise SystemExit('QA CLI failure at '+str(item))
            row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0])
            rows.append(row)
            (QA/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            assert all(row['controls'].values()), {k:v for k,v in row['controls'].items() if not v}
            assert all(row['style_checks'].values()), {k:v for k,v in row['style_checks'].items() if not v}
            print(state,lang,width,'controls',len(row['controls']),'styleFAIL',sum(v is False for v in row['style_checks'].values()),flush=True)
print(json.dumps({'cases':len(rows),'control_pass':sum(sum(r['controls'].values()) for r in rows),
    'style_pass':sum(sum(r['style_checks'].values()) for r in rows),
    'style_fail':sum(sum(not v for v in r['style_checks'].values()) for r in rows)}))
