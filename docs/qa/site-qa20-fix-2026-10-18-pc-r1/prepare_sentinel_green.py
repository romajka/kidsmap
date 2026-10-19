import json
from pathlib import Path
O=Path(__file__).resolve().parent;s=(O/'browser-sentinels-red.js').read_text();baseline=json.loads((O/'evidence/browser-sentinels-red.json').read_text())
s=s.replace("phase='red',previous=null","phase='green',previous="+json.dumps(baseline))
s=s.replace("if(previous){const old=", "checks.no_hub_CSS=await p.evaluate(()=>![...document.styleSheets].some(s=>s.href?.includes('kidsmap_site_settings.css')));\nif(previous){const old=")
(O/'browser-sentinels-green.js').write_text(s)
print('Fresh own Place/Event baseline embedded for exact applied-source geometry comparison.')
