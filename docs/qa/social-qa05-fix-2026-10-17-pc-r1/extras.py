import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent
rows=[]
cases=[]
for lang,prefix,heading in [('ru','/ru','Общие отзывы о сайте'),('az','','Sayt haqqında ümumi rəylər'),('en','/en','General site reviews')]:
    for width in [760,761]:
        cases.append({'role':'author','lang':lang,'width':width,'url':prefix+'/reviews/','heading':heading})
for item in cases:
    (Q/'cell.js').write_text((Q/'matrix-cell.js').read_text().replace('__ITEM__',json.dumps(item,ensure_ascii=False)),encoding='utf-8')
    result=subprocess.run(['python3',str(Q/'browser_driver.py'),'cell.js'],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode==0,result.stdout+result.stderr
    row=json.loads(result.stdout.split('### Result\n',1)[1].split('\n###',1)[0])
    row['layout']['responsive_track_count']=len(row['facts']['gridTracks'].split())==(1 if item['width']==760 else 2)
    rows.append(row)
    (Q/'boundary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert all(row['controls'].values()) and all(row['layout'].values()),row
    print(item['lang'],item['width'],'PASS',flush=True)
