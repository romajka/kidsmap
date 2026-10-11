"""Correct own QA Select2 interaction; no application/assertion change."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'site-finish.js').read_text(encoding='utf-8')
s=s.replace("m.on('dialog',d=>d.accept());",'').replace('try{let s=await state(m)',"m.on('dialog',d=>d.accept());try{let s=await state(m)")
s=s.replace("await m.locator('#id_status').selectOption(status);",'''const label=await m.locator('#id_status option[value="'+status+'"]').innerText();await m.locator('#select2-id_status-container').click();await m.getByRole('option',{name:label,exact:true}).click();''')
s=s.replace("const label=await m.locator", "await m.locator('a.nav-link').filter({hasText:'Модерация'}).click();const label=await m.locator") if "a.nav-link" not in s else s
(P/'site-finish.js').write_text(s,encoding='utf-8')
