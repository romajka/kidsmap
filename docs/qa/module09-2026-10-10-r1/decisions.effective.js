async original=>{
const F={
  "actors": {
    "author": {
      "id": 1,
      "username": "qa09_author",
      "email": "author09@example.invalid"
    },
    "owner": {
      "id": 2,
      "username": "qa09_owner",
      "email": "owner09@example.invalid"
    },
    "employee": {
      "id": 3,
      "username": "qa09_employee",
      "email": "employee09@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa09_outsider",
      "email": "outsider09@example.invalid"
    },
    "moderator": {
      "id": 5,
      "username": "qa09_moderator",
      "email": "moderator09@example.invalid"
    },
    "staff": {
      "id": 6,
      "username": "qa09_staff",
      "email": "staff09@example.invalid"
    },
    "admin": {
      "id": 7,
      "username": "qa09_admin",
      "email": "admin09@example.invalid"
    },
    "empty": {
      "id": 8,
      "username": "qa09_empty",
      "email": "empty09@example.invalid"
    },
    "invitee": {
      "id": 9,
      "username": "qa09_invitee",
      "email": "invitee09@example.invalid"
    }
  },
  "places": {
    "live": 1,
    "empty": 2,
    "hidden": 3,
    "inactive": 4,
    "archived": 5,
    "deleted": 6,
    "foreign": 7
  },
  "activity": 1,
  "specialist": 1,
  "event": 1,
  "synthetic_only": true
},base='http://localhost:8822',dir='C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/',rows=[],contexts=[],browser=original.context().browser();
const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6000);if(role!=='guest'){await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));}return p;}
async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}const state=async p=>(await p.request.get(base+'/qa/state/')).json();
const a=await page('author'),m=await page('moderator'),g=await page('guest'),o=await page('owner'),e=await page('employee');
for(const [kind,pk]of Object.entries({place:F.places.empty,specialist:F.specialist,activity:F.activity,event:F.event})){const url=base+'/ru/reviews/'+kind+'/target/'+pk+'/';try{
let s=await state(m),h=s.typed[kind].heads.find(x=>x.user_id===F.actors.author.id);await m.goto(url);const candidate=m.locator('[data-candidate-id="'+h.candidate_revision_id+'"]');
if(kind==='event'){await candidate.locator('[name=reason]').fill('QA09 REJECT: clarify fictional event facts');await candidate.locator('form[action$="/reject/"] button').click();}else await candidate.locator('form[action$="/approve/"] button').click();
await m.waitForLoadState('domcontentloaded');s=await state(m);h=s.typed[kind].heads.find(x=>x.user_id===F.actors.author.id);add('moderation-'+kind,kind==='event'?h.status==='rejected':h.is_approved,{head:h,role:'moderator',screenshot:await shot(m,'decision-'+kind+'-moderator')});
await a.goto(url);add('rejection-reason-'+kind,kind!=='event'||(await a.locator('.typed-reviews').innerText()).includes('QA09 REJECT'),{savedReason:h.rejection_reason,visible:(await a.locator('.typed-reviews').innerText()).slice(-700),screenshot:await shot(a,'decision-'+kind+'-author')});
await g.goto(url);add('public-'+kind,kind==='event'?await g.locator('article[data-review-id]').count()===0:(await g.locator('article[data-review-id]').innerText()).includes('QA09 FIRST'),{role:'guest',summary:s.summaries[kind][String(pk)],screenshot:await shot(g,'decision-'+kind+'-public')});
add('safe-html-'+kind,await g.evaluate(()=>!window.QA09_XSS)&&await g.locator('.typed-reviews img[src=x],.typed-reviews script').count()===0,{role:'guest'});
if(kind==='event')continue;
await o.goto(url);const reply=o.locator('form[action$="/reply/"]');add('owner-reply-available-'+kind,await reply.count()===1,{role:'owner'});if(await reply.count()){await reply.locator('[name=text]').fill('QA09 OWNER REPLY '+kind+' <b>escaped</b>');await reply.locator('button').click();await o.waitForLoadState('domcontentloaded');s=await state(o);add('owner-reply-saved-'+kind,s.typed[kind].responses.some(x=>x.actor_id===F.actors.owner.id&&x.kind==='reply'),{role:'owner',screenshot:await shot(o,'reply-'+kind)});}
await e.goto(url);add('employee-reply-scope-'+kind,kind!=='activity'||await e.locator('form[action$="/reply/"]').count()===1,{role:'employee',replyCount:await e.locator('form[action$="/reply/"]').count()});
await e.locator('article[data-review-id="'+h.id+'"] button[name=value][value="1"]').click();await e.waitForLoadState('domcontentloaded');s=await state(e);let current=s.typed[kind].heads.find(x=>x.id===h.id);add('helpful-saved-'+kind,current.likes_count===1,{role:'employee',head:current});
await e.locator('article[data-review-id="'+h.id+'"] button[name=value][value="1"]').click();await e.waitForLoadState('domcontentloaded');s=await state(e);current=s.typed[kind].heads.find(x=>x.id===h.id);add('helpful-repeat-toggle-'+kind,current.likes_count===0,{role:'employee',head:current});
await e.locator('article[data-review-id="'+h.id+'"] button[name=value][value="-1"]').click();await e.waitForLoadState('domcontentloaded');await e.reload();s=await state(e);current=s.typed[kind].heads.find(x=>x.id===h.id);add('unhelpful-reload-count-'+kind,current.dislikes_count===1&&await e.locator('article[data-review-id="'+h.id+'"] button[value="-1"]').getAttribute('aria-pressed')==='true',{role:'employee',head:current,screenshot:await shot(e,'reaction-'+kind)});
}catch(err){rows.push({id:'decisions-harness-'+kind,status:'NOT RUN',role:'author',lang:'ru',width:1440,error:String(err).slice(0,500)});}}
try{let s=await state(m),h=s.site.find(x=>x.user_id===F.actors.author.id);for(const action of ['reject','approve','hide','approve']){await m.goto(base+'/ru/admin/catalog/sitereview/'+h.id+'/'+action+'/');await shot(m,'site-'+action+'-confirm');await m.locator('form[method=post] button[type=submit]').filter({visible:true}).last().click();await m.waitForLoadState('domcontentloaded');s=await state(m);h=s.site.find(x=>x.id===h.id);add('site-native-'+action+'-'+rows.length,action==='approve'?h.status==='approved':action==='reject'?h.status==='rejected':!h.is_approved,{role:'moderator',head:h,screenshot:await shot(m,'site-'+action+'-after')});await g.goto(base+'/ru/reviews/');add('site-public-'+action,(await g.locator('body').innerText()).includes('QA09 SITE NATIVE')===(action==='approve'),{role:'guest',screenshot:await shot(g,'site-public-'+action)});}}catch(err){rows.push({id:'site-decision-harness',status:'NOT RUN',role:'moderator',lang:'ru',width:1440,error:String(err).slice(0,450)});}
const s=await state(a);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}
