from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'matrix-template.js';t=p.read_text();t=t.replace("let errors=[],bad=[],blocked=0;","let errors=[],bad=[],blocked=0,consoleErrors=[];")
t=t.replace("p.on('pageerror'","p.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text().slice(0,220));});p.on('pageerror'")
t=t.replace('errors=[];bad=[];blocked=0;try{','errors=[];bad=[];blocked=0;consoleErrors=[];try{')
t=t.replace('errors,externalBlocked:blocked','errors,consoleErrors,externalBlocked:blocked')
# record the actual accessible landmark structure separately from screenshots
needle="rows.push({id:scene+'-render'"
t=t.replace(needle,"rows.push({id:scene+'-single-main-landmark',status:await p.locator('main').count()===1?'PASS':'FAIL',role,lang,width,url,mainCount:await p.locator('main').count()});\n"+needle)
p.write_text(t)
# all eight role batches serial to avoid session interference
(Q/'matrix.sh').write_text('''#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
for role in guest author owner employee moderator staff admin empty; do
 python3 "$qa/run_browser.py" matrix "$role"
done
''')
