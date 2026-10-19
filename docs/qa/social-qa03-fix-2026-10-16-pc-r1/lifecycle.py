import json
import subprocess
import time
from pathlib import Path

qa=Path(__file__).resolve().parent
items=[item for item in json.loads((qa/'cases.json').read_text()) if item['width'] in (390,1440)]
template=(qa/'lifecycle.js').read_text(encoding='utf-8')
for phase in ('raceprep','race','guards','retry'):
    path=qa/(phase+'.json')
    rows=json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    completed={row['item']['cell'] for row in rows if row.get('checks') and all(row['checks'].values())}
    for item in items:
        if item['cell'] in completed:continue
        while True:
            memo=next((row for row in json.loads((qa/'raceprep.json').read_text(encoding='utf-8')) if row['item']['cell']==item['cell']),{}) if phase=='race' else {}
            script=template.replace('__CASE__',json.dumps(item)).replace('__PHASE__',phase).replace('__MEMO__',json.dumps(memo))
            args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=social03-pc-fix-r1','run-code',script]
            result=subprocess.run(args,cwd=qa.parents[1],text=True,capture_output=True)
            (qa/f'{phase}-{item["cell"]}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
            with (qa/'browser-commands.jsonl').open('a') as file:file.write(json.dumps({'command':f'{phase} {item["cell"]}','exit':result.returncode})+'\n')
            if '### Result\n' not in result.stdout:
                print(result.stdout+result.stderr,flush=True);raise SystemExit(1)
            row,_=json.JSONDecoder().raw_decode(result.stdout.split('### Result\n',1)[1])
            if row.get('stage')=='WAIT_REAL_COOLDOWN':
                print(json.dumps({'phase':phase,'cell':item['cell'],'wait_real_seconds':row['retry_after']}),flush=True)
                time.sleep(min(20,max(1,row['retry_after'])));continue
            rows.append(row)
            path.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            if not all(row['checks'].values()):
                print(json.dumps(row,ensure_ascii=False),flush=True);raise SystemExit(1)
            print(json.dumps({'phase':phase,'cell':item['cell'],'kind':item['kind'],'lang':item['lang'],'width':item['width'],'checks':len(row['checks']),'pageerrors':len(row['pageerrors'])}),flush=True)
            break
print('Completed24 race,24 privacy/CSRF,24 retry/approval native cases',flush=True)
