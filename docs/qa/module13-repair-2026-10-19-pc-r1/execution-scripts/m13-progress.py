from pathlib import Path
import re,json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';s=(Q/'full-r1.log').read_text();ids=re.findall(r'test_\S+ \((catalog\.[^)]+)\)',s);print(json.dumps({'full_methods_observed':len(set(ids)),'latest':ids[-1] if ids else None,'bytes':len(s),'failure_headings':len(re.findall(r'^FAIL:|^ERROR:',s,re.M))}))
paths=list(Path('/root/.npm/_npx').glob('*/node_modules/playwright/package.json'));print(json.dumps({'playwright_module':str(paths[-1].parent) if paths else None}))
if paths:(Q/'playwright-module.txt').write_text(str(paths[-1].parent))
