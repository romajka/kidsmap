import json
import subprocess
import time
from pathlib import Path

qa=Path(__file__).resolve().parent
(qa/'png').mkdir(exist_ok=True)
items=json.loads((qa/'cases.json').read_text())
template=(qa/'browser-cell.js').read_text(encoding='utf-8')
rows=[]
prep=json.loads((qa/'native-prep.json').read_text())
def call(item,mode):
    script=template.replace('__CASE__',json.dumps(item)).replace('__MODE__',mode)
    args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=social03-pc-fix-r1','run-code',script]
    result=subprocess.run(args,cwd=qa.parents[1],text=True,capture_output=True)
    (qa/f'cell-{item["cell"]}-{mode}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    with (qa/'browser-commands.jsonl').open('a') as file:file.write(json.dumps({'command':f'cell {item["cell"]} {mode}','exit':result.returncode})+'\n')
    if '### Result\n' not in result.stdout:
        print(result.stdout+result.stderr,flush=True)
        raise SystemExit(1)
    row,_=json.JSONDecoder().raw_decode(result.stdout.split('### Result\n',1)[1])
    if row.get('stage')=='WAIT_REAL_COOLDOWN':
        print(json.dumps({'cell':item['cell'],'real_cooldown_wait_seconds':row['retry_after']}),flush=True)
        time.sleep(min(20,max(1,row['retry_after'])))
        return call(item,mode)
    if mode=='prep':
        prep.append(row)
        (qa/'native-prep.json').write_text(json.dumps(prep,indent=2)+'\n')
    else:
        rows.append(row)
        (qa/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if row.get('stage')!='conflict' or not all(row['checks'].values()):
            print(json.dumps(row,ensure_ascii=False),flush=True)
            raise SystemExit(1)
    print(json.dumps({'cell':item['cell'],'kind':item['kind'],'lang':item['lang'],'width':item['width'],'stage':row['stage'],'checks':len(row.get('checks',{})),'pageerrors':len(row.get('pageerrors',[]))}),flush=True)
for item in items[18:20]:call(item,'recheck')
for item in items[20:]:call(item,'full')
for item in items[:18]:call(item,'finish')
print('Completed72 real conflict cells',flush=True)
