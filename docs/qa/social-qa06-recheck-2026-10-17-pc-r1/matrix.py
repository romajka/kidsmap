import gettext,json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent
rows=[]
for lang,prefix in [('ru','/ru'),('az',''),('en','/en')]:
    with (Q/'locales/locale'/lang/'LC_MESSAGES/django.mo').open('rb') as f:groupName=gettext.GNUTranslations(f).gettext('Ваша оценка')
    for width in [360,390,768,1024,1280,1440]:
        item={'lang':lang,'width':width,'url':prefix+'/reviews/','groupName':groupName}
        (Q/'cell.js').write_text((Q/'rating-cell.js').read_text().replace('__ITEM__',json.dumps(item,ensure_ascii=False)),encoding='utf-8')
        r=subprocess.run(['python3',str(Q/'browser_driver.py'),'cell.js'],capture_output=True,text=True,encoding='utf-8')
        raw=r.stdout+r.stderr
        if r.returncode or '### Result\n' not in raw:
            (Q/'matrix-error.txt').write_text(raw,encoding='utf-8');raise SystemExit('Native cell error '+str(item))
        row=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);rows.append(row)
        (Q/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        assert all(row['controls'].values()),row['controls']
        print(lang,width,'controlPASS',len(row['controls']),'sourceFAIL',sum(not v for v in row['source'].values()),flush=True)
print(json.dumps({'cells':len(rows),'control_pass':sum(sum(r['controls'].values()) for r in rows),
 'source_pass':sum(sum(r['source'].values()) for r in rows),'source_fail':sum(sum(not v for v in r['source'].values()) for r in rows)}))
