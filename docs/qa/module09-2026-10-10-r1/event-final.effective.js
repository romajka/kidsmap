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
},base='http://localhost:8822',browser=original.context().browser(),rows=[],contexts=[];const state=async p=>(await p.request.get(base+'/qa/state/')).json();
for(const role of ['owner','employee']){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6000);await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));try{
await p.goto(base+'/ru/reviews/event/target/'+F.event+'/');const s=await state(p),h=s.typed.event.heads.find(x=>x.user_id===F.actors.author.id);if(role==='owner'){const reply=p.locator('form[action$="/reply/"]');if(await reply.count()){await reply.locator('[name=text]').fill('QA09 EVENT OWNER RESPONSE');const wait=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/reply/'));await reply.locator('button').click();await wait;await p.waitForLoadState('domcontentloaded');rows.push({id:'event-owner-reply-saved',status:(await state(p)).typed.event.responses.some(x=>x.actor_id===F.actors.owner.id&&x.kind==='reply')?'PASS':'FAIL',role,lang:'ru',width:1440});}else rows.push({id:'event-owner-reply-unsupported-fixture',status:'NOT RUN',role,lang:'ru',width:1440,note:'Published legacy fixture owner does not satisfy organizer/person management contract; do not infer entitlement.'});}else{
for(const value of ['1','1','-1']){const wait=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/react/'));await p.locator('article[data-review-id="'+h.id+'"] button[value="'+value+'"]').click();await wait;await p.waitForLoadState('domcontentloaded');const current=(await state(p)).typed.event.heads.find(x=>x.id===h.id);rows.push({id:'event-reaction-'+value+'-'+rows.length,status:value==='-1'?current.dislikes_count===1?'PASS':'FAIL':current.likes_count===(rows.filter(x=>x.id.startsWith('event-reaction-1')).length===0?1:0)?'PASS':'FAIL',role,lang:'ru',width:1440,head:current});}
await p.reload();await p.screenshot({path:'C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/event-reaction-final.png'});
}
}catch(err){rows.push({id:'event-final-harness',status:'NOT RUN',role,lang:'ru',width:1440,error:String(err).slice(0,350)});}}
for(const c of contexts)await c.close();return{rows,utc:new Date().toISOString()};
}
