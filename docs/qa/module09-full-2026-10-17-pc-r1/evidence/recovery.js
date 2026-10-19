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
},base='http://127.0.0.1:33380',dir='/mnt/c/kidsmap/.tmp/module09-full-pc-r1/png/',rows=[],contexts=[],browser=original.context().browser();
const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(7000);if(role!=='guest'){await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('<fictional-local-password>');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));}return p;}
async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}
const state=async p=>(await p.request.get(base+'/qa/state/')).json();

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
