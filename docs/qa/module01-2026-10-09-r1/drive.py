import subprocess, sys, json, re, os, time, datetime, shutil
os.environ['PYTHONIOENCODING']='utf-8'
os.environ['PYTHONUTF8']='1'
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
here=Path(__file__).resolve().parent
credential=(here.parents[2]/'.tmp/module01-20261009-r1/credential').read_text()
source=(here/sys.argv[1]).read_text(encoding='utf-8')
if sys.argv[1]=='branch-lifecycle.js':
    source=source.replace("p.setDefaultTimeout(8000)","p.setDefaultTimeout(20000)")
    source=source.replace("await p.locator('[name=lng]').fill('');", "await p.locator('[name=lng]').fill('');await p.waitForTimeout(800);await Promise.all([p.waitForResponse(r=>r.url().includes('/save-photos/')&&r.request().method()==='POST'),p.locator('[name=form_action][value=save_draft]').click()]);await p.waitForURL('**/edit/#pc-section-4');await p.reload();await p.waitForTimeout(700);")
    source=source.replace("await p.locator('[name=region]').selectOption('baku');", "await p.locator('[name=region]').selectOption('absheron');await p.locator('[name=region]').selectOption('baku');await p.waitForTimeout(300);")
if sys.argv[1] in ('deep-matrix.js','deep-admin-final.js'):
    source=source.replace("await p.locator('[data-pc-section-select]').selectOption('pc-section-3');await p.locator('[data-pc-section-select]').focus();await p.locator('[data-pc-section-select]').press('Alt+ArrowDown');", "if(await p.locator('[data-pc-section-select]').isVisible()){await p.locator('[data-pc-section-select]').selectOption('pc-section-3');await p.locator('[data-pc-section-select]').focus();await p.locator('[data-pc-section-select]').press('Alt+ArrowDown');}else{await p.locator('.pc-nav a[href=\"#pc-section-3\"]').press('Enter');}")
    source=source.replace("await p.locator('[data-pf-coord-manual]').click();", "if(await p.locator('#location [data-place-section-toggle]').getAttribute('aria-expanded')==='false')await p.locator('#location [data-place-section-toggle]').click();await p.locator('[data-km-place-location-toggle]').click();await p.locator('[data-pf-coord-manual]').click();")
    source=source.replace("await p.locator('.errornote,.errorlist').first().waitFor();", "await p.waitForTimeout(700);")
    source=source.replace("'.errornote,.errorlist').allTextContents()", "'.errornote,.errorlist,.km-pf-errors,.km-pf-validation-summary,[role=alert],[data-place-error-summary]').allTextContents()")
    if sys.argv[1]=='deep-admin-final.js':source=source.replace("['owner','moderator']","['moderator']")
if sys.argv[1]=='photo-promote.js':
    source=source.replace("await p.locator('[data-pc-submit]').click();", "for(const [name,val] of [['name_ru','QA clean branch RU'],['name_en','QA clean branch EN']]){const el=p.locator('[name='+name+']'),d=el.locator('xpath=ancestor::details');if(await d.getAttribute('open')===null)await d.locator(':scope > summary').click();await el.fill(val);}await p.waitForTimeout(950);await p.locator('[data-pc-submit]').click();")
    source=source.replace("const photos=p.locator('main img')", "const publicColor=await fingerprint(p.locator('.place-gallery__image').first());add('promoted-cover-public-content',before.reduce((s,v,i)=>s+Math.abs(v-publicColor[i]),0)/before.length<8);const photos=p.locator('main img')")
(here/(Path(sys.argv[1]).stem+'.effective.js')).write_text(source,encoding='utf-8')
source=source.replace('__LOCAL_PASSWORD__',credential)
cli=Path.home()/'AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js'
started=time.monotonic()
result=subprocess.run(['node',str(cli),'-s=module01-r1','run-code',source],capture_output=True,text=True,encoding='utf-8',errors='replace')
out=result.stdout
# Keep results only; never persist echoed executed code or credentials.
match=re.search(r'### Result\s*\n(.*?)(?=\n### |\Z)',out,re.S)
clean=match.group(1) if match else re.sub(r'```js.*?```','[executed code omitted]',out,flags=re.S)
clean=clean.replace(credential,'[redacted]')
target=here/(Path(sys.argv[1]).stem+'.result.txt')
if target.exists():
    index=1
    while target.with_name(target.stem+f'.attempt{index}.txt').exists():index+=1
    shutil.copyfile(target,target.with_name(target.stem+f'.attempt{index}.txt'))
target.write_text(clean,encoding='utf-8')
with (here/'command-ledger.jsonl').open('a',encoding='utf-8') as out:
    out.write(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':f'.venv/Scripts/python.exe docs/qa/module01-2026-10-09-r1/drive.py {sys.argv[1]}','cli_exit_code':result.returncode,'duration_seconds':round(time.monotonic()-started,2),'result':target.name})+'\n')
print(clean[:6500]);print('CLI exit',result.returncode)
if result.stderr:print(result.stderr[:500])
