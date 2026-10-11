"""Create this run's QA harness from reviewed QA-only examples; never edit application files."""
from pathlib import Path
import json, subprocess, hashlib, secrets
P=Path(__file__).resolve().parent; R=P.parents[2]
S=R/'.tmp/module01-recheck-20261011-r1'; S.mkdir(parents=True,exist_ok=False)
(P/'screenshots').mkdir()
(S/'credential').write_text(secrets.token_urlsafe(32))
paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=R).decode().split('\0')
foreign={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in sorted(set(paths)) if p and not p.startswith(P.relative_to(R).as_posix()+'/') and (R/p).is_file()}
(P/'foreign-entry.json').write_text(json.dumps(foreign,indent=2))
donor=R/'docs/qa/module13-2026-10-11-r1'
for name in ['run.py','qa_settings.py','drive.py','common.js','seed.py','qa_urls.py','place-flow.js']:
 t=(donor/name).read_text(encoding='utf-8')
 t=t.replace('module13-2026-10-11-r1','module01-recheck-2026-10-11-r1').replace('module13-20261011-r1','module01-recheck-20261011-r1').replace('module13-r1','place-recheck-r1').replace('module13_r1','place_recheck_r1').replace('module13','place_recheck').replace('QA13','QA01R').replace('qa13','qa01r').replace('8831','8841').replace('55444','55446').replace("+'13@example.invalid'","+'01r@example.invalid'").replace("role+'13@example.invalid'","role+'01r@example.invalid'")
 if name=='run.py':
  t=t.replace('import django\ndjango.setup()',"import importlib.util\nspec=importlib.util.spec_from_file_location('isolated_locales',ROOT/'scripts/build_isolated_locales.py')\nbuilder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)\nmanifest=builder.verify(STATE/'locales/manifest.json',ROOT/'locale')\nassert manifest['locales']==['ru','az','en']\nimport django\ndjango.setup()")
 if name=='qa_settings.py':t+="\nimport json\nLOCALE_PATHS=(json.loads((QA_ROOT/'locales/manifest.json').read_text())['locale_root'],)\n"
 if name=='seed.py':
  t=t.replace("(HERE/'fixtures.json').write_text", "from catalog.testcases.utils import ensure_quality_subcategory\ncat=Category.objects.create(code='QA01R_LONG',name='QA01R '+'Long fictional category '*18,name_ru='QA01R '+'Длинная вымышленная категория '*18,name_az='QA01R '+'Uzun uydurma kateqoriya '*18,name_en='QA01R '+'Long fictional category '*18)\nsub=ensure_quality_subcategory(cat)\n(HERE/'taxonomy.json').write_text(json.dumps({'category':cat.code,'subcategory':sub.pk}))\n(HERE/'fixtures.json').write_text")
 if name=='common.js':
  t=t.replace("const p=await c.newPage();p.setDefaultTimeout", "const p=await c.newPage();p.on('pageerror',e=>consoleErrors.push({role,lang,width,error:String(e)}));p.on('response',r=>{if(r.status()>=400)networkErrors.push({role,lang,width,url:r.url().split('?')[0],status:r.status()});});p.setDefaultTimeout")
  t=t.replace('rows=[];','rows=[],consoleErrors=[],networkErrors=[];')
 (P/name).write_text(t,encoding='utf-8')
cfg=json.loads((R/'.tmp/module13-20261011-r1/playwright.json').read_text());cfg['outputDir']=str(S/'playwright')
(S/'playwright.json').write_text(json.dumps(cfg))
print('Own harness initialized; foreign files hashed:',len(foreign))
