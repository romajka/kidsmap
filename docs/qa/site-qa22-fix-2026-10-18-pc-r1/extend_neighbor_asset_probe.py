import json
from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/site-qa22-fix-2026-10-18-pc-r1')
s=(O/'browser-sentinels.js').read_text();needle='checks.geometry_identical=JSON.stringify(old)===JSON.stringify(geometry);';assert needle in s;s=s.replace(needle,needle+"checks.no_hub_CSS=await p.evaluate(()=>![...document.styleSheets].some(s=>s.href?.includes('kidsmap_site_settings.css')));")
(O/'browser-sentinels.js').write_text(s);(O/'browser-sentinels-green.js').write_text(s.replace('__PHASE__','green').replace('__SENTINEL_BASELINE__',(O/'evidence/browser-sentinels-red.json').read_text()))
