from pathlib import Path
Q=Path(__file__).resolve().parent
base=(Q/'flows-template.js').read_text();header=base[:base.index("const a=await page('author')")]
body=r'''
const a=await page('author'),m=await page('moderator');
const url=base+'/ru/reviews/specialist/target/'+F.specialist+'/';
try{
 await a.goto(url);const b=await a.context().newPage();await b.goto(url);
 await a.locator('#review-rating').selectOption('3');await a.locator('#review-text').fill('ACCEPT09 candidate A');await a.locator('[data-review-edit] button').click();await a.waitForLoadState('domcontentloaded');
 const before=(await state(a)).typed.specialist;
 await b.locator('#review-rating').selectOption('1');await b.locator('#review-text').fill('ACCEPT09 unsaved B');const wait=b.waitForResponse(r=>r.request().method()==='POST');await b.locator('[data-review-edit] button').click();const response=await wait;await b.waitForLoadState('domcontentloaded');
 add('conflict-409-keeps-B',response.status()===409&&await b.locator('#review-text').inputValue()==='ACCEPT09 unsaved B'&&await b.locator('#review-rating').inputValue()==='1',{screenshot:await shot(b,'accept-conflict-409')});
 add('conflict-no-server-overwrite',JSON.stringify(before)===JSON.stringify((await state(a)).typed.specialist));
 const h=before.heads.find(h=>h.user_id===F.actors.author.id);await m.goto(url);const cand=m.locator('[data-candidate-id="'+h.candidate_revision_id+'"]');await cand.locator('[name=reason]').fill('ACCEPT09 clarify details');await cand.locator('form[action$="/reject/"] button').click();await m.waitForLoadState('domcontentloaded');
 await a.goto(url);add('rejected-edit-author-feedback',(await a.locator('.typed-reviews').innerText()).includes('ACCEPT09 clarify details'),{screenshot:await shot(a,'accept-rejected-edit')});
 await a.locator('#review-rating').selectOption('5');await a.locator('#review-text').fill('ACCEPT09 corrected resubmission');await a.locator('[data-review-edit] button').click();await a.waitForLoadState('domcontentloaded');
 add('new-pending-removes-old-rejection',!(await a.locator('.typed-reviews').innerText()).includes('ACCEPT09 clarify details'));
 const h2=(await state(a)).typed.specialist.heads.find(x=>x.id===h.id);await m.goto(url);await m.locator('[data-candidate-id="'+h2.candidate_revision_id+'"] form[action$="/approve/"] button').click();await m.waitForLoadState('domcontentloaded');
 add('resubmission-approved',(await state(m)).typed.specialist.heads.find(x=>x.id===h.id).text==='ACCEPT09 corrected resubmission');
}catch(err){rows.push({id:'recovery-harness',status:'NOT RUN',error:String(err).slice(0,450)});}
for(const c of contexts)await c.close();return{rows,utc:new Date().toISOString()};}
'''
(Q/'recovery-template.js').write_text(header+body)
