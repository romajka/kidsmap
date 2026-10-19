import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;Q=O.parents[2]/'.tmp/site06-pc-fix-r1';ledger=[]
def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True);ledger.append({'command':cmd,'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr});(O/'evidence/after-matrix-commands.json').write_text(json.dumps(ledger,indent=2));print(r.stdout,flush=True);assert r.returncode==0,cmd
run(['python3',str(O/'prepare_color_final.py')])
run(['python3',str(O/'use_owned_ram_media.py')])
(O/'start_color_browser.py').write_text((O/'start_browser.py').read_text().replace('range(40)','range(120)'))
run(['python3',str(O/'start_color_browser.py'),'green'])
jobs=[]
for name in ['run_final_green.py','run_final_static.py']:
 log=(Q/(name+'.log')).open('w');jobs.append((name,subprocess.Popen(['python3',str(O/name)],stdout=log,stderr=subprocess.STDOUT),log))
run(['python3',str(O/'browser_driver.py'),'browser-color-forms.js'])
d=json.loads((O/'evidence/browser-color-forms.json').read_text());assert not d.get('error') and len(d['rows'])==36 and all(all(x['checks'].values()) for x in d['rows'])
for name,p,log in jobs:
 code=p.wait();log.close();ledger.append({'command':['python3',str(O/name)],'exit':code});(O/'evidence/after-matrix-commands.json').write_text(json.dumps(ledger,indent=2));assert code==0,name
 print(json.dumps({'script':name,'exit':code}),flush=True)
run(['python3',str(O/'run_browser_edges.py')])
run(['docker','exec','m10s06-fix-r1-app','python',str(O/'export_owned_media.py')])
(O/'evidence/media-final-manifest.json').write_bytes((Q/'media-final-manifest.json').read_bytes())
print(json.dumps({'post_matrix_all_pass':True}),flush=True)
