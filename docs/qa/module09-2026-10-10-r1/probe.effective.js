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
},base='http://localhost:8822',browser=original.context().browser();
const c=await browser.newContext({viewport:{width:1440,height:950}});await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();
await p.goto(base+'/ru/auth/login/');const fields=await p.locator('input:not([type=hidden])').evaluateAll(es=>es.map(e=>({name:e.name,type:e.type})));
await p.locator('input[name=username]').fill(F.actors.author.email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(250);
const states=await (await p.request.get(base+'/qa/state/')).json();
await p.goto(base+'/ru/reviews/place/target/'+F.places.live+'/');const typed={status:await p.locator('h1').innerText(),forms:await p.locator('main form').evaluateAll(es=>es.map(e=>({action:e.getAttribute('action'),fields:Array.from(e.elements).map(x=>x.name).filter(x=>x!=='csrfmiddlewaretoken')}))),reviews:await p.locator('article[data-review-id]').count()};
await p.goto(base+'/ru/account/favorites/');const favorites={text:(await p.locator('.account-main-content').innerText()).slice(0,2000),links:await p.locator('.account-favs-grid a').evaluateAll(es=>es.map(e=>e.getAttribute('href')))};
await p.goto(base+'/ru/account/notifications/');const notification={text:(await p.locator('#main-content').innerText()).slice(0,1800),css:await p.locator('link[rel=stylesheet]').evaluateAll(es=>es.map(e=>e.href))};
await p.goto(base+'/ru/account/places/'+F.places.live+'/team/');const team={url:p.url(),text:(await p.locator('body').innerText()).slice(0,1800),fields:await p.locator('input:not([type=hidden]),select').evaluateAll(es=>es.map(e=>({name:e.name,id:e.id})))};
await c.close();return{fields,typed,favorites,notification,team,stateCounts:{place:states.typed.place.heads.length,site:states.site.length}};
}
