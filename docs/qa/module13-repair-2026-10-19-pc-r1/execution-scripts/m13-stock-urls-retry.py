from pathlib import Path
import json,subprocess,os
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
cfg=json.loads((Q/'stock-url-config.json').read_text());cfg['addPath']='/ru/admin/catalog/place/add/?type=permanent';(Q/'stock-url-config-r2.json').write_text(json.dumps(cfg))
env={**os.environ,'PLAYWRIGHT_MODULE':(Q/'playwright-module.txt').read_text(),'CHROMIUM_EXECUTABLE':'/root/.cache/ms-playwright/chromium-1247/chrome-linux64/chrome','PLACE_URL_BROWSER_ORIGIN':'http://127.0.0.1:33811','PLACE_URL_BROWSER_CONFIG':str(Q/'stock-url-config-r2.json')}
cmd=['npx','--yes','--package','node@24','node',str(Q/'stock-scripts/test_localized_place_urls.cjs')];p=subprocess.run(cmd,cwd=R,env=env,capture_output=True,text=True);raw=p.stdout+p.stderr;(Q/'stock-urls-r2.log').write_text(raw);d={'command':cmd,'exit':p.returncode,'unchanged_assertions':True,'correct_add_choice_type_precondition':True,'success_lines':[l for l in raw.splitlines() if l.startswith('PASS')]};(O/'evidence/stock-urls-r2.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
