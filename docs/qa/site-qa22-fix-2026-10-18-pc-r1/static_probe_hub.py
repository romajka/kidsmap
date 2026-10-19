import hashlib,json,subprocess,urllib.request
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'.tmp/site22-pc-fix-r1'
cmd=['python3',str(O/'static_probe.py')];r=subprocess.run(cmd,capture_output=True,text=True);(Q/'static-forms-summary.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr[-500:]
d=json.loads((O/'evidence/static-runtime.json').read_text())
with urllib.request.urlopen('http://127.0.0.1:33610/static/admin/css/pages/kidsmap_site_settings.css',timeout=10) as response:d['hub_CSS_HTTP_status']=response.status;d['hub_CSS_HTTP_sha256']=hashlib.sha256(response.read()).hexdigest()
assert d['hub_CSS_HTTP_sha256']==hashlib.sha256((R/'static/admin/css/pages/kidsmap_site_settings.css').read_bytes()).hexdigest() and d['hub_CSS_HTTP_status']==200
code="import sys;from pathlib import Path;Q=Path('/mnt/c/kidsmap/.tmp/site22-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *;from django.template.loader import get_template;print(get_template('admin/catalog/site_settings_hub.html').origin.name)"
r=subprocess.run(['docker','exec','m10s22-fix-r1-app','python','-c',code],capture_output=True,text=True);assert r.returncode==0,r.stderr[-500:];d['hub_template_origin']=r.stdout.strip();d['hub_template_compiled']=True
(O/'evidence/static-runtime.json').write_text(json.dumps(d,indent=2));print(json.dumps({'sources':d['source_count'],'branches':len(d['branches']),'forms_CSS_HTTP':d['CSS_HTTP_status'],'hub_CSS_HTTP':d['hub_CSS_HTTP_status'],'hub_CSS':d['hub_CSS_HTTP_sha256'],'hub_template_compiled':True}))
