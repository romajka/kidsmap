from pathlib import Path
p=Path(__file__).with_name('admin-flow.js')
s=p.read_text(encoding='utf-8')
s=s.replace("let phase='login';", "const fill=async(name,value)=>{const el=p.locator('[name='+name+']');if(!await el.isVisible()){const id=await el.locator('xpath=ancestor::div[contains(@class,\"tab-pane\")]').getAttribute('id');await p.locator('a[role=tab]').filter({hasText:name.startsWith('description')?'Описание':'Названия'}).click();}await el.fill(value);};let phase='login';")
import re
s=re.sub(r"await p.locator\('\[name=(name_az|name_ru|name_en|description_az)\]'\).fill\(('.*?')\)",lambda m: "await fill('"+m[1]+"',"+m[2]+")",s)
p.write_text(s,encoding='utf-8')
