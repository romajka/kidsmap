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
  }
},base='http://localhost:8822',browser=original.context().browser(),c=await browser.newContext({viewport:{width:1440,height:950}}),rows=[];await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors.author.email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));let s=await(await p.request.get(base+'/qa/state/')).json();rows.push({id:'employee-report-final-persisted',status:s.typed.place.responses.some(x=>x.actor_id===F.actors.employee.id&&x.kind==='report'&&x.text==='QA09 PRIVATE REPORT place')?'PASS':'FAIL',role:'employee',lang:'ru',width:1440,note:'Readback after asynchronous native Enter submit; supplement early state read was premature.'});
await p.goto(base+'/ru/reviews/place/target/'+E.place+'/');rows.push({id:'employee-report-still-private',status:!(await p.locator('.typed-reviews').innerText()).includes('QA09 PRIVATE REPORT')?'PASS':'FAIL',role:'author',lang:'ru',width:1440});
await p.goto(base+'/ru/reviews/specialist/target/'+F.specialist+'/');const h=s.typed.specialist.heads.find(x=>x.specialist_id===F.specialist&&x.user_id===F.actors.author.id),token=await p.locator('[name=csrfmiddlewaretoken]').first().getAttribute('value');const r=await p.request.post(base+'/ru/reviews/specialist/'+h.id+'/react/',{form:{csrfmiddlewaretoken:token,revision_id:String(h.current_revision_id),value:'8'},maxRedirects:0});rows.push({id:'self-reaction-denied-before-invalid-value',status:r.status()===403?'PASS':'FAIL',role:'author',lang:'ru',width:1440,http:r.status(),note:'Self-reaction forbidden before value validation; old expected400 was incorrect.'});
await p.goto(base+'/ru/reviews/');const sf=p.locator('form[action$="/review/"]');await sf.locator('[name=text]').fill('QA09 REQUIRED RATING RETAINED');const before=s.site.length;await sf.locator('button[type=submit]').click();await p.waitForTimeout(400);s=await(await p.request.get(base+'/qa/state/')).json();const feedback=await p.locator('[data-review-live]').innerText();rows.push({id:'site-required-rating-error-retains-input',status:s.site.length===before&&await sf.locator('[name=text]').inputValue()==='QA09 REQUIRED RATING RETAINED'&&feedback.length>0?'PASS':'FAIL',role:'author',lang:'ru',width:1440,feedback,screenshot:'screenshots/site-required-rating-error.png'});await sf.scrollIntoViewIfNeeded();await p.screenshot({path:'C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/site-required-rating-error.png'});
await c.close();return{rows,utc:new Date().toISOString()};
}
