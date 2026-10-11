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
},base='http://localhost:8822',browser=original.context().browser(),c=await browser.newContext({viewport:{width:1440,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors.author.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));await p.goto(base+'/ru/place-reviews/');const links=await p.locator('.pagination a').evaluateAll(es=>es.map(e=>({href:e.getAttribute('href'),absolute:e.href,text:e.textContent.trim()})));const requests=[];p.on('request',r=>{if(r.isNavigationRequest())requests.push({method:r.method(),url:r.url()});});const before=p.url();await p.locator('.pagination a[href*="page=2"]').first().click();await p.waitForTimeout(700);const after=p.url(),text=(await p.locator('body').innerText()).slice(0,300),active=await p.locator('.pagination .active').allTextContents();await p.screenshot({path:'C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/pagination-diagnostic.png'});await c.close();return{before,after,links,requests,text,active};
}
