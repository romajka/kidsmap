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
m.on('dialog',d=>d.accept());try{let s=await state(m),h=s.site.find(x=>x.user_id===F.actors.author.id);for(const status of ['rejected','approved','pending','approved']){
await m.goto(base+'/ru/admin/catalog/sitereview/'+h.id+'/change/');await m.locator('a.nav-link').filter({hasText:'Модерация'}).click();const label=await m.locator('#id_status option[value="'+status+'"]').innerText();await m.locator('#select2-id_status-container').click();await m.getByRole('option',{name:label,exact:true}).click();await m.locator('#id_rejection_reason').fill(status==='rejected'?'QA09 SITE REASON':'');await m.locator('input[name=_save],button[name=_save]').filter({visible:true}).first().click();await m.waitForLoadState('domcontentloaded');s=await state(m);h=s.site.find(x=>x.id===h.id);add('site-save-'+status+'-'+rows.length,h.status===status&&h.is_approved===(status==='approved'),{role:'moderator',head:h,screenshot:await shot(m,'site-status-'+status)});await g.goto(base+'/ru/reviews/');add('site-public-'+status,(await g.locator('body').innerText()).includes('QA09 SITE NATIVE')===(status==='approved'),{role:'guest',screenshot:await shot(g,'site-public-status-'+status)});
}}catch(err){rows.push({id:'site-editor-harness',status:'NOT RUN',role:'moderator',lang:'ru',width:1440,error:String(err).slice(0,450)});}
const s=await state(m);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}