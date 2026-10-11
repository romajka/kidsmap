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
},base='http://localhost:8822',dir='C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/',rows=[],contexts=[],browser=original.context().browser();const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6000);await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));return p;}async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}const state=async p=>(await p.request.get(base+'/qa/state/')).json();const a=await page('author'),o=await page('owner'),i=await page('empty'),m=await page('moderator');
try{await a.goto(base+'/ru/place-reviews/');const first=await a.locator('.place-review-card,.review-item').allTextContents();await a.locator('.pagination a[href*="page=2"]').first().click();await a.waitForURL(u=>u.searchParams.get('page')==='2',{waitUntil:'domcontentloaded'});const next=await a.locator('.place-review-card,.review-item').allTextContents();add('place-index-pagination-retry',first.length>0&&next.length>0&&first.every(x=>!next.includes(x)),{firstCount:first.length,secondCount:next.length,url:a.url(),screenshot:await shot(a,'place-pagination2-fresh')});}catch(err){rows.push({id:'pagination-retry-harness',status:'NOT RUN',role:'author',lang:'ru',width:1440,error:String(err).slice(0,350)});}
for(const c of contexts)await c.close();return{rows,utc:new Date().toISOString()};
}