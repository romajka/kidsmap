import json
import subprocess
from pathlib import Path

qa=Path(__file__).resolve().parent
(qa/'png').mkdir(exist_ok=True)
template=(qa/'browser-cell.js').read_text(encoding='utf-8')
rows=[]
for lang in ('ru','az','en'):
    for width in (360,390,768,1024,1280,1440):
        cell=len(rows)
        script=template.replace('__CELL__',str(cell)).replace('__LANG__',lang).replace('__WIDTH__',str(width))
        args=['npx','--yes','--package','node@24','--package','@playwright/cli','playwright-cli','-s=m09pc-r1','run-code',script]
        result=subprocess.run(args,cwd=qa.parents[1],text=True,capture_output=True)
        (qa/f'cell-{lang}-{width}.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
        with (qa/'browser-commands.jsonl').open('a') as output:
            output.write(json.dumps({'command':f'playwright-cli run-code cell={cell} lang={lang} width={width}','exit':result.returncode})+'\n')
        if '### Result\n' not in result.stdout:
            print(result.stdout+result.stderr,flush=True)
            raise SystemExit(1)
        data=result.stdout.split('### Result\n',1)[1]
        row,_=json.JSONDecoder().raw_decode(data)
        rows.append(row)
        (qa/'matrix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'cell':cell,'lang':lang,'width':width,'checks':row['checks'],'pageerrors':len(row['pageerrors'])}),flush=True)
print('Completed 18 fresh native conflict cells',flush=True)
