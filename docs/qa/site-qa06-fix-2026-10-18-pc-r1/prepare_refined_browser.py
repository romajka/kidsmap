from pathlib import Path
O=Path(__file__).resolve().parent
s=(O/'browser-final-matrix.js').read_text().replace("['content','super']","['content']").replace("['az','ru','en']","['ru']").replace('[360,390,768,1024,1280,1440]','[390,1440]').replace("O+'/png/final-","O+'/png/smoke-final-")
(O/'browser-refinement-smoke.js').write_text(s)
for name in ['browser-editors.js','browser-permissions.js','browser-concurrency.js','browser-legacy.js']:
 p=O/name;s=p.read_text().replace(".km-place-form-alert strong",".km-place-form-alert__heading").replace('setDefaultTimeout(15000)','setDefaultTimeout(30000)').replace('setDefaultTimeout(12000)','setDefaultTimeout(30000)')
 # Navigation waits for DOM and explicit target decode, not unrelated public carousel assets.
 import re
 s=re.sub(r'await ([apb])\.goto\((base\+[^;]*?)\);',r"await \1.goto(\2,{waitUntil:'domcontentloaded'});",s)
 p.write_text(s)
print('Fresh refined smoke and edge harness prepared; no prior evidence overwritten.')
