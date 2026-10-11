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
},E={
  "place": 8,
  "specialist": 2,
  "reviews": {
    "place": 29,
    "specialist": 2
  },
  "event": 2
},base='http://localhost:8822',browser=original.context().browser(),c=await browser.newContext({viewport:{width:390,height:950}}),rows=[];await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors.owner.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));await p.goto(base+'/ru/reviews/event/target/'+E.event+'/');const form=p.locator('form[action$="/reply/"]');await form.locator('[name=text]').fill('QA09 VERIFIED ORGANIZER REPLY');const wait=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/reply/'));await form.locator('button').click();await wait;await p.waitForLoadState('domcontentloaded');const s=await(await p.request.get(base+'/qa/state/')).json();rows.push({id:'event-verified-organizer-native-reply',status:s.typed.event.responses.some(x=>x.text==='QA09 VERIFIED ORGANIZER REPLY'&&x.actor_id===F.actors.owner.id)?'PASS':'FAIL',role:'owner',lang:'ru',width:390,screenshot:'screenshots/event-verified-organizer-reply.png'});await p.screenshot({path:'C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/event-verified-organizer-reply.png'});await c.close();return{rows,utc:new Date().toISOString()};
}
