import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site08-pc-followup-r1'
s=(O/'browser-sentinels.js').read_text().replace('__PHASE__','green').replace('__SENTINEL_BASELINE__',(O/'evidence/browser-sentinels-red.json').read_text());(O/'browser-sentinels-green.js').write_text(s)
for lang in ['az','ru','en']:(O/('browser-saved-message-'+lang+'.js')).write_text((O/'browser-saved-message.js').read_text().replace('__LANG__',lang))
names=['browser-acceptance-green','browser-readonly-green','browser-sentinels-green','browser-json-error-snapshots','browser-file-error-central','browser-permissions','browser-saved-message-az','browser-saved-message-ru','browser-saved-message-en'];commands=[]
for n in names:
 cmd=['python3',str(O/'browser_driver.py'),n+'.js'];r=subprocess.run(cmd,capture_output=True,text=True);(Q/(n+'-summary.log')).write_text(r.stdout+r.stderr);commands.append({'command':cmd,'exit':r.returncode});(O/'evidence/acceptance-commands.json').write_text(json.dumps(commands,indent=2));print(r.stdout,flush=True);assert r.returncode==0,r.stderr[-700:]
 d=json.loads((O/'evidence'/(n+'.json')).read_text());assert not d.get('error'),d.get('error');assert 'rows' in d
print('Native acceptance commands completed; inspect every boolean, network and fixture guard before final decision.',flush=True)
