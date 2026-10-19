async original=>{
const F=__FIXTURES_JSON__,base='http://127.0.0.1:33380',dir='/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/',rows=[],contexts=[],browser=original.context().browser();
const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(7000);if(role!=='guest'){await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('<fictional-local-password>');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));}return p;}
async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}
const state=async p=>(await p.request.get(base+'/qa/state/')).json();
const a=await page('author'),m=await page('moderator'),g=await page('guest');
const kinds={place:F.places.empty,specialist:F.specialist,activity:F.activity,event:F.event};
for(const [kind,pk]of Object.entries(kinds)){const url=base+'/ru/reviews/'+kind+'/target/'+pk+'/';try{
let s=await state(a),h=s.typed[kind].heads.find(x=>x.user_id===F.actors.author.id);await g.goto(url);add('pending-private-'+kind,(await g.locator('.typed-reviews').innerText()).includes('QA09 FIRST')===false);
await m.goto(url);const candidate=m.locator('[data-candidate-id="'+h.candidate_revision_id+'"]');
if(kind==='event'){await candidate.locator('[name=reason]').fill('QA09 REJECT: clarify fictional event facts');await candidate.locator('form[action$="/reject/"] button').click();}
else await candidate.locator('form[action$="/approve/"] button').click();await m.waitForLoadState('domcontentloaded');
s=await state(m);h=s.typed[kind].heads.find(x=>x.user_id===F.actors.author.id);add('moderation-'+kind,kind==='event'?h.status==='rejected':h.is_approved,{head:h,role:'moderator',screenshot:await shot(m,'flow-'+kind+'-decision')});
await a.goto(url);add('author-rejection-reason-'+kind,kind!=='event'||(await a.locator('.typed-reviews').innerText()).includes('QA09 REJECT'),{role:'author',savedReason:h.rejection_reason,visible:(await a.locator('.typed-reviews').innerText()).slice(-900),screenshot:await shot(a,'flow-'+kind+'-author-decision')});
await g.goto(url);add('public-projection-'+kind,kind==='event'?await g.locator('article[data-review-id]').count()===0:(await g.locator('article[data-review-id]').innerText()).includes('QA09 FIRST'),{role:'guest',summary:s.summaries[kind][String(pk)],screenshot:await shot(g,'flow-'+kind+'-public')});
add('escaped-html-'+kind,await g.evaluate(()=>!window.QA09_XSS)&&await g.locator('main script,main img[src=x]').count()===0,{role:'guest'});
}catch(e){rows.push({id:'harness-'+kind,status:'NOT RUN',role:'author',lang:'ru',width:1440,error:String(e).slice(0,500),screenshot:await shot(a,'flow-'+kind+'-harness').catch(()=>null)});}}
const s=await state(a);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}
