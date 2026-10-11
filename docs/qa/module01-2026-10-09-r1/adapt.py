"""Adapt historical navigation, never historical results, to a fresh isolated stand."""
from pathlib import Path
import re
here=Path(__file__).resolve().parent
old=here.parent/'place-acceptance-2026-10-09-8792/scripts'
login="""const login=async role=>{await c.clearCookies(); if(role==='guest')return; await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(role+'@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();};"""
s=(old/'lifecycle.js').read_text(encoding='utf-8')
start=s.index('const login=');end=s.index(';\ntry{',start)+1
s=s[:start]+login+s[end:]
s=s.replace('8792','8811').replace('/home/ramin/kidsmap/docs/qa/place-acceptance-2026-10-09-8811/screenshots/','C:/kidsmap/docs/qa/module01-2026-10-09-r1/screenshots/').replace('/home/ramin/kidsmap/.tmp/content-entry-final-20261007/assets/cover.png','C:/kidsmap/.tmp/module01-20261009-r1/assets/cover.png')
(here/'lifecycle.js').write_text(s,encoding='utf-8')
(here/'screenshots').mkdir(exist_ok=True)
for filename in ('branch-create.js','branch-fill.js','coordinates.js','media-map.js','admin-create.js','branch-final.js'):
    s=(old/filename).read_text(encoding='utf-8')
    for role in ('owner','moderator'):
        pattern=r"await p\.goto\(base\+'/qa/'\);await p\.getByRole\('button',\{name:'Войти: demo_"+role+r"',exact:true\}\)\.click\(\);"
        replacement="await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill('"+role+"@example.invalid');await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.getByRole('button',{name:'Войти',exact:true}).click();"
        s=re.sub(pattern,lambda m:replacement,s)
    s=s.replace('8792','8811').replace('/home/ramin/kidsmap/docs/qa/place-acceptance-2026-10-09-8811/screenshots/','C:/kidsmap/docs/qa/module01-2026-10-09-r1/screenshots/')
    s=s.replace('/home/ramin/kidsmap/.tmp/content-entry-final-20261007/assets/','C:/kidsmap/.tmp/module01-20261009-r1/assets/').replace('/home/ramin/kidsmap/.tmp/content-entry-final-20261007/synthetic-photo.png','C:/kidsmap/.tmp/module01-20261009-r1/assets/cover.png')
    s=s.replace('/home/ramin/kidsmap/.tmp/content-completion-20261009/','C:/kidsmap/.tmp/module01-20261009-r1/assets/')
    s=s.replace('gallery-one.png','gallery.png').replace('gallery-two.png','gallery-two.png').replace('/159/','/2/').replace('id:159','id:2').replace('/organizations/71/','/organizations/1/')
    s=s.replace("await choose('#id_subcategory','edu-quality-tests');","await choose('#id_subcategory','learning');")
    (here/filename).write_text(s,encoding='utf-8')
