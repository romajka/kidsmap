from pathlib import Path
O=Path(__file__).resolve().parent
p=O/'browser-final-matrix.js';s=p.read_text();needle="const b=baseline.rows.find(x=>x.role===role&&x.lang===lang&&x.width===width);";assert s.count(needle)==1
s=s.replace(needle,needle+"await a.locator('.km-place-form-error-list a[href=\"#id_logo\"]').press('Enter');const linkedFocus=await input.evaluate(e=>document.activeElement===e);")
s=s.replace("keyboardTabVisible:tab.visible,","keyboardTabVisible:tab.visible,errorLinkFocusesInput:linkedFocus,");p.write_text(s)
s=s.replace("['content','super']","['content']").replace("['az','ru','en']","['ru']").replace('[360,390,768,1024,1280,1440]','[390,1440]').replace("O+'/png/final-","O+'/png/smoke-final-");(O/'browser-refinement-smoke.js').write_text(s)
p=O/'browser-editors.js';s=p.read_text();s=s.replace("fieldError:await p.locator('#id_'+field+'_error').count()>0,", "fieldError:await p.locator('#id_'+field+'_error').count()>0,visibleLinkedError:await p.locator('#id_'+field+'_media_error').isVisible(),fileAriaLink:await p.locator('[name='+field+'][type=file]').getAttribute('aria-describedby')==='id_'+field+'_media_error',");p.write_text(s)
print('Refined native checks strengthened with visible error references and native anchor focus.')
