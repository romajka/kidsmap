from pathlib import Path
import json,subprocess,os,hashlib,difflib
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';shadow=Q/'stock-scripts';shadow.mkdir(exist_ok=True);(Q/'stock-screenshots').mkdir(exist_ok=True);rows=[]
def session(role):return next(c['value'] for c in json.loads((Q/('stock-'+role+'-state.json')).read_text())['cookies'] if c['name']=='sessionid')
# Only private ignored configs contain fictional session credentials.
(Q/'stock-url-config.json').write_text(json.dumps({'session':session('admin'),'addPath':'/ru/admin/catalog/place/add/','editPath':'/ru/admin/catalog/place/1/change/'}))
cross=json.loads(subprocess.check_output(['curl','-fsS','http://127.0.0.1:33810/qa/m13/cross/'],text=True))
for kind,role in [('stock','excluded'),('cooldown','editor')]:
 (Q/(kind+'-review-config.json')).write_text(json.dumps({'session':session(role),'place':cross['urls']['ru']['place'],'specialist':'/ru/specialists/'}))
for name,profile,config in [('test_localized_place_urls.cjs','stock','stock-url-config.json'),('test_review_submission.cjs','stock','stock-review-config.json'),('test_review_cooldown.cjs','cooldown','cooldown-review-config.json')]:
 source=R/'scripts'/name;before=source.read_text();after=before.replace('/tmp/',str(Q/'stock-screenshots')+'/');target=shadow/name;target.write_text(after)
 # Only literal screenshot destinations changed; assertions remain exact.
 assert after.replace(str(Q/'stock-screenshots')+'/','/tmp/')==before
 env={**os.environ,'PLAYWRIGHT_MODULE':(Q/'playwright-module.txt').read_text(),'CHROMIUM_EXECUTABLE':'/root/.cache/ms-playwright/chromium-1247/chrome-linux64/chrome','PLACE_URL_BROWSER_ORIGIN':'http://127.0.0.1:33811','PLACE_URL_BROWSER_CONFIG':str(Q/config),'REVIEW_BROWSER_ORIGIN':'http://127.0.0.1:'+('33811' if profile=='stock' else '33812'),'REVIEW_BROWSER_CONFIG':str(Q/config)}
 cmd=['npx','--yes','--package','node@24','node',str(target)];p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/(name+'.stock.log')).write_text(raw)
 row={'file':source.relative_to(R).as_posix(),'command':cmd,'exit':p.returncode,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'only_shadow_screenshot_destination_changed':True,'assertions_unchanged':True,'success_lines':[l for l in raw.splitlines() if l.startswith('PASS')],'explicit_simulation':'blocked external transport and script-declared route failures, actual local application POST/GET'};rows.append(row);print(name,p.returncode,flush=True)
(O/'evidence/stock-browser-scripts.json').write_text(json.dumps(rows,indent=2))
