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
},base='http://localhost:8822',browser=original.context().browser();const c=await browser.newContext({viewport:{width:1440,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors.moderator.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));const s=await(await p.request.get(base+'/qa/state/')).json(),h=s.site.find(x=>x.user_id===F.actors.author.id);await p.goto(base+'/ru/admin/catalog/sitereview/'+h.id+'/change/');const controls=await p.locator('button,a,[role=tab],summary').evaluateAll(es=>es.filter(e=>e.getBoundingClientRect().width).map(e=>({tag:e.tagName,id:e.id,cls:e.className,text:e.textContent.trim().slice(0,65),href:e.getAttribute('href')})));const parents=await p.locator('#id_status').evaluate(e=>{const r=[];while(e&&r.length<7){r.push({tag:e.tagName,id:e.id,cls:e.className,hidden:e.hidden,display:getComputedStyle(e).display});e=e.parentElement;}return r;});await p.screenshot({path:'C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/site-admin-probe.png'});await c.close();return{controls,parents};
}
