import hashlib,json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1'
stage=json.loads((Q/'stage.json').read_text());stage['test_db']='test_m10s15_fix_r1_preview';(Q/'stage.json').write_text(json.dumps(stage))
if (Q/'green-server.log').exists():(Q/'green-before-preview-server.log').write_bytes((Q/'green-server.log').read_bytes())
s=(O/'browser-final-matrix.js').read_text().replace("'/png/final-'","'/png/preview-final-'");(O/'browser-preview-final-matrix.js').write_text(s)
s=(O/'browser-file-media.js').read_text().replace("'/png/file-conflict-'","'/png/preview-file-conflict-'")
s=s.replace("fileInputEmpty:await", "currentPreviewStored:await b.locator('.km-place-form-page img[src^=\"/media/\"]').evaluateAll(imgs=>imgs.every(img=>img.complete&&img.naturalWidth>0)),fileInputEmpty:await")
(O/'browser-preview-file-media.js').write_text(s)
s=(O/'browser-editors.js').read_text().replace("'/png/final-checkbox", "'/png/preview-checkbox")
start=s.index(" const cr=await a.goto(base+'/admin/catalog/catalogcontentsettings/1/change/');")
end=s.index('\n await c.close();',start)
s=s[:start]+" // CatalogContentSettings direct UI is NOT RUN beyond existing __str__ TypeError500; baseline proof and first failed observation retained separately.\n"+s[end:]
(O/'browser-preview-editors.js').write_text(s)
print('New fresh testDB selected; current-source final scripts use distinct evidence/PNG names. Catalog direct UI remains explicit NOT RUN after baseline500; not converted to PASS.')
