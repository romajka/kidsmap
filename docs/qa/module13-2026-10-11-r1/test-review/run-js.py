"""Existing JS scripts only; separate counts for Node tests and bare assertion scripts."""
import json, os, re, subprocess, time
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[3]
S=ROOT/'.tmp/module13-20261011-r1/test-review'
S.mkdir(parents=True,exist_ok=True)
(S/'jsdom.cjs').write_text("module.exports = require('C:/kidsmap/.tmp/phone-dom/node_modules/jsdom');\n")
env=os.environ.copy()
for key in list(env):
    if key.startswith(('DJANGO_','DATABASE_','LEGACY_','REDIS_','GOOGLE_','EMAIL_','INDEXNOW_','TASK33_','ANALYTICS_','LOCAL_ANALYTICS_','OWNER_ANALYTICS_')):
        env.pop(key)
env['NODE_PATH']=str(ROOT/'.tmp/phone-dom/node_modules')
env['KIDSMAP_JSDOM']=str(S/'jsdom.cjs')
node='C:/Program Files/nodejs/node.exe'
paths=sorted((ROOT/'scripts').glob('test*.cjs'))+sorted((ROOT/'scripts/tests').glob('*.test.cjs'))+sorted((ROOT/'static/js/tests').glob('*.js'))
browser=[];unit=[]
for f in paths:
    if 'chromium' in f.read_text(encoding='utf-8') and ('chromium.launch' in f.read_text(encoding='utf-8')):
        browser.append(f)
    else:
        unit.append(f)
results=[]
for f in unit:
    command=[node,'--test',str(f)]
    started=time.monotonic()
    try:
        run=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        output=run.stdout+run.stderr
        log=P/('js-'+f.stem+'.log');log.write_text(output,encoding='utf-8')
        counts={key:int(value) for key,value in re.findall(r'^.*? (tests|suites|pass|fail|cancelled|skipped|todo) (\d+)$',output,re.M)}
        # Node wraps bare assertion scripts as one file test, not individual assertions.
        bare="require('node:test')" not in f.read_text(encoding='utf-8') and 'require("node:test")' not in f.read_text(encoding='utf-8')
        row={'file':f.relative_to(ROOT).as_posix(),'command':command,'exit_code':run.returncode,'status':'PASS' if run.returncode==0 else 'FAIL','duration_seconds':round(time.monotonic()-started,3),'node_counts':counts,'bare_assertion_script':bare,'log':log.name,'assertion_count':'NOT ENUMERATED' if bare else 'Node test count'}
    except subprocess.TimeoutExpired:
        row={'file':f.relative_to(ROOT).as_posix(),'command':command,'exit_code':None,'status':'ENVIRONMENT_FAILURE','reason':'Own 120s timeout','duration_seconds':round(time.monotonic()-started,3)}
    results.append(row)
    (P/'js-results.json').write_text(json.dumps({'results':results,'browser_scripts':[{'file':f.relative_to(ROOT).as_posix(),'status':'NOT RUN','reason':'Requires dedicated browser fixtures and configured synthetic accounts; root rendered acceptance is a separate check'} for f in browser],'dependencies':{'NODE_PATH':env['NODE_PATH'],'KIDSMAP_JSDOM':env['KIDSMAP_JSDOM'],'existing_jsdom':'read only; no install or foreign file changes'}},indent=2),encoding='utf-8')
    print(f.name,row['status'],row.get('node_counts'),flush=True)
print('SCRIPTS',len(results),'PASS',sum(x['status']=='PASS' for x in results),'FAIL',sum(x['status']=='FAIL' for x in results),'BROWSER NOT RUN',len(browser),flush=True)
