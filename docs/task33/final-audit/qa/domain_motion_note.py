"""Attribute final browser diagnostic without adding it to main context/check totals."""
import json
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]
motion=json.loads((OUT/'browser-motion-results.json').read_text(encoding='utf-8'))
assert motion['status']=='FAIL' and len(motion['unexpected_page_errors'])==2 and motion['cleanup']=='PASS'
note='Отдельная причинная диагностика browser reviewer: оба нативных Program POST (400 без impact confirmation и 302 с подтверждением) дают InvalidStateError ViewTransition. При 400 candidate не создаётся; при 302 pending сохраняется, approved данные не меняются. Это подтверждает ошибку браузерного перехода при правильном business state. Два diagnostic errors не добавлены к основным 816 contexts/1724 checks. [browser-motion-results.json](browser-motion-results.json).'
helper=OUT/'qa/domain_review_write.py'
text=helper.read_text(encoding='utf-8')
anchor='## 2. Что работает и как части соединены'
assert anchor in text
text=text.replace(anchor,note+'\n\n'+anchor)
helper.write_text(text,encoding='utf-8')
exec(compile(text,str(helper),'exec'))
evidence=json.loads((OUT/'domain-browser-evidence.json').read_text(encoding='utf-8'))
evidence['separate_motion_diagnostic']={'ref':'browser-motion-results.json','executor':'/root/stage26_public','status':'FAIL','page_errors':2,'responses':[r['status'] for r in motion['responses']],'business_state':motion['business_state'],'included_in_main_totals':False,'cleanup':'PASS'}
(OUT/'domain-browser-evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
