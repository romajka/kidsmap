from pathlib import Path
p=Path(__file__).resolve().parent/'admin-functional.js';s=p.read_text(encoding='utf-8')
s=s.replace("const publish=a.locator('[name=_publish_place]')", "const publish=a.locator('[name=_publish_place]:visible').first()")
s=s.replace("a.locator('button[name=_continue]').click()", "a.locator('button[name=_continue]:visible').first().click()")
s=s.replace("r.status()===404,{http:r.status()}", "[404,410].includes(r.status()),{http:r.status()}")
p.write_text(s,encoding='utf-8');print('Own QA: scoped visible Place submit controls; disabled event section correctly accepts HTTP410 Gone.')
