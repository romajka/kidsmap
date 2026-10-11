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
},base='http://localhost:8822',dir='C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/',rows=[],contexts=[],browser=original.context().browser();
const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6000);await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));return p;}
async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}const state=async p=>(await p.request.get(base+'/qa/state/')).json();const a=await page('author'),e=await page('employee');
try{await e.goto(base+'/ru/reviews/place/target/'+E.place+'/');const details=e.locator('details');await details.locator('summary').focus();await e.keyboard.press('Enter');await details.locator('textarea').fill('QA09 PRIVATE REPORT place');await details.locator('button').focus();await e.keyboard.press('Enter');await e.waitForLoadState('domcontentloaded');add('employee-report-keyboard-saved',(await state(e)).typed.place.responses.some(x=>x.actor_id===F.actors.employee.id&&x.kind==='report'&&x.text==='QA09 PRIVATE REPORT place'),{role:'employee',screenshot:await shot(e,'employee-report-enter')});}catch(err){rows.push({id:'report-keyboard-harness',status:'NOT RUN',role:'employee',lang:'ru',width:1440,error:String(err).slice(0,350)});}
try{await a.goto(base+'/ru/catalog/');await a.locator('form[action$="/place/'+F.places.live+'/like/"] button').click();await a.waitForTimeout(300);for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){const prefix=base+(lang==='az'?'/':'/'+lang+'/');await a.setViewportSize({width,height:950});await a.goto(prefix+'account/favorites/');add('filled-favorites-visible',(await a.locator('.account-main-content').innerText()).includes('QA09 live'),{lang,width,screenshot:await shot(a,'filled-favorites-'+lang+'-'+width)});await a.goto(prefix+'account/notifications/');add('stale-invites-no-accept',await a.locator('form[action$="/accept/"]').count()===0,{lang,width,screenshot:await shot(a,'stale-notifications-'+lang+'-'+width)});}
await a.setViewportSize({width:1440,height:950});await a.goto(base+'/ru/account/favorites/');await a.locator('form[action$="/place/'+F.places.live+'/like/"] button').click();await a.waitForTimeout(300);add('final-favorite-remove',!(await state(a)).favorites.some(x=>x.user_id===F.actors.author.id&&x.place_id===F.places.live));
}catch(err){rows.push({id:'filled-favorites-harness',status:'NOT RUN',role:'author',lang:'ru',width:1440,error:String(err).slice(0,350)});}
try{
await e.goto(base+'/ru/reviews/');let s=await state(e),h=s.site.find(x=>x.user_id===F.actors.author.id);let form=e.locator('form[action$="/site-review/'+h.id+'/vote/"]');await form.locator('button[value="1"]').click();await e.waitForTimeout(300);add('site-reaction-saved',(await state(e)).site.find(x=>x.id===h.id).likes_count===1,{role:'employee'});await e.reload();add('site-reaction-reload',await e.locator('form[action$="/site-review/'+h.id+'/vote/"] button[value="1"]').getAttribute('aria-pressed')==='true',{role:'employee'});await e.locator('form[action$="/site-review/'+h.id+'/vote/"] button[value="1"]').click();await e.waitForTimeout(300);add('site-reaction-repeat-toggle',(await state(e)).site.find(x=>x.id===h.id).likes_count===0,{role:'employee',screenshot:await shot(e,'site-reaction')});
await a.goto(base+'/ru/reviews/');s=await state(a);const publicSite=s.site.filter(x=>x.is_approved&&x.status==='approved'),avg=publicSite.reduce((n,x)=>n+x.rating,0)/publicSite.length;const score=await a.locator('.site-reviews-score-main').innerText();add('site-rating-count-projection',score.includes(String(publicSite.length))&&score.includes(avg.toFixed(1).replace('.',',')),{count:publicSite.length,average:avg,rendered:score});
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){const prefix=base+(lang==='az'?'/':'/'+lang+'/');await a.setViewportSize({width,height:950});await a.goto(prefix+'reviews/');const sf=a.locator('form[action$="/review/"]');const value='QA09 RETAINED INPUT '+lang+' '+width;await sf.locator('.review-star[data-value="4"]').click();await sf.locator('[name=text]').fill(value);let disabled=false;
await a.route('**/review/',async r=>{if(r.request().method()==='POST'){await new Promise(resolve=>setTimeout(resolve,600));await r.abort('failed');}else await r.continue();});const count=(await state(a)).site.length;await sf.locator('button[type=submit]').click();await a.waitForTimeout(100);disabled=await sf.locator('button[type=submit]').isDisabled();const screenshot=await shot(a,'loading-site-'+lang+'-'+width);add('site-loading-honest',disabled,{lang,width,classification:'SIMULATED delayed transport then abort',screenshot});await a.waitForTimeout(850);add('site-network-input-retained',await sf.locator('[name=text]').inputValue()===value&&!(await sf.locator('button[type=submit]').isDisabled())&&(await state(a)).site.length===count,{lang,width,classification:'SIMULATED network failure',screenshot:await shot(a,'network-site-'+lang+'-'+width)});await a.unroute('**/review/');
}
}catch(err){rows.push({id:'site-extra-harness',status:'NOT RUN',role:'author',lang:'ru',width:1440,error:String(err).slice(0,400)});}
const s=await state(a);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}
