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
},base='http://localhost:8822',dir='C:/kidsmap/docs/qa/module09-2026-10-10-r1/screenshots/',rows=[],browser=original.context().browser(),contexts=[];
const add=(id,ok,data={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'author',lang:'ru',width:1440,...data});
async function page(role){const c=await browser.newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(6000);await p.goto(base+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForURL(u=>!u.pathname.includes('/auth/login/'));return p;}
async function shot(p,name){await p.screenshot({path:dir+name+'.png'});return'screenshots/'+name+'.png';}const state=async p=>(await p.request.get(base+'/qa/state/')).json();const a=await page('author'),m=await page('moderator');
try{
await a.goto(base+'/ru/reviews/specialist/target/'+E.specialist+'/');await a.locator('#review-rating').selectOption('1');await a.locator('#review-text').fill('QA09 NEW REJECTED CANDIDATE');await a.locator('[data-review-edit] button').click();await a.waitForLoadState('domcontentloaded');await m.goto(a.url());const s=await state(a),h=s.typed.specialist.heads.find(x=>x.specialist_id===E.specialist&&x.user_id===F.actors.author.id);const cand=m.locator('[data-candidate-id="'+h.candidate_revision_id+'"]');await cand.locator('[name=reason]').fill('QA09 SAVED REJECTION REASON');await cand.locator('form[action$="/reject/"] button').click();await m.waitForLoadState('domcontentloaded');
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){await a.setViewportSize({width,height:950});const prefix=base+(lang==='az'?'/':'/'+lang+'/');try{
await a.goto(prefix+'reviews/specialist/target/'+E.specialist+'/');await a.locator('[data-review-edit]').scrollIntoViewIfNeeded();let screenshot=await shot(a,'proof-feedback-'+lang+'-'+width);const rating=await a.locator('#review-rating').inputValue();add('saved-rating-restored',rating==='5',{lang,width,rating,savedRating:5,screenshot});add('rejection-reason-visible',(await a.locator('.typed-reviews').innerText()).includes('QA09 SAVED REJECTION REASON'),{lang,width,savedReason:'QA09 SAVED REJECTION REASON',screenshot});
await a.goto(prefix+'reviews/activity/target/'+F.activity+'/');const title=await a.locator('.typed-reviews h1').innerText();add('activity-human-title',!title.includes('Activity object'),{lang,width,title,expectedName:'Uydurma QA09 fəaliyyət',screenshot:await shot(a,'proof-activity-title-'+lang+'-'+width)});
await a.goto(prefix+'account/notifications/');const css=await a.locator('.account-main-layout').evaluate(e=>({display:getComputedStyle(e).display,navDisplay:getComputedStyle(e.querySelector('.account-nav-item')).display,styles:Array.from(document.querySelectorAll('link[rel=stylesheet]')).map(x=>new URL(x.href).pathname)}));add('notification-account-styles',css.display==='flex'||css.display==='grid',{lang,width,...css,screenshot:await shot(a,'proof-notification-'+lang+'-'+width)});
await a.goto(prefix+'reviews/specialist/target/'+F.specialist+'/');const tab=await a.context().newPage();await tab.setViewportSize({width,height:950});await tab.goto(a.url());await a.locator('#review-rating').selectOption('3');await a.locator('#review-text').fill('QA09 MATRIX A '+lang+' '+width);await a.locator('[data-review-edit] button').click();await a.waitForLoadState('domcontentloaded');await tab.locator('#review-rating').selectOption('1');await tab.locator('#review-text').fill('QA09 UNSAVED MATRIX B '+lang+' '+width);const wait=tab.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/target/'));await tab.locator('[data-review-edit] button').click();const response=await wait;await tab.waitForLoadState('domcontentloaded');screenshot=await shot(tab,'proof-conflict-'+lang+'-'+width);add('matrix-two-tabs-409',response.status()===409,{lang,width,http:response.status(),screenshot});add('matrix-conflict-recovery',await tab.locator('#review-text').count()===1,{lang,width,http:response.status(),editorCount:await tab.locator('#review-text').count(),visible:await tab.locator('body').innerText(),screenshot});await tab.close();
await a.goto(prefix+'reviews/?page=3');const text=await a.locator('body').innerText();add('long-html-escaped',text.includes('window.QA09_XSS=1')&&await a.evaluate(()=>!window.QA09_XSS)&&await a.locator('.site-reviews-list script,.site-reviews-list img[src=x]').count()===0,{lang,width,screenshot:await shot(a,'proof-long-review-'+lang+'-'+width)});
}catch(err){rows.push({id:'proof-cell-harness',status:'NOT RUN',role:'author',lang,width,error:String(err).slice(0,400)});}}
}catch(err){rows.push({id:'proof-setup-harness',status:'NOT RUN',role:'moderator',lang:'ru',width:1440,error:String(err).slice(0,400)});}
try{await a.setViewportSize({width:768,height:950});await a.goto(base+'/ru/reviews/');const details=await a.locator('.review-form-grid').evaluate(e=>{let r=e.getBoundingClientRect();return{grid:getComputedStyle(e).gridTemplateColumns,width:r.width,right:r.right,children:Array.from(e.children).map(x=>({width:x.getBoundingClientRect().width,right:x.getBoundingClientRect().right,minWidth:getComputedStyle(x).minWidth})),document:document.documentElement.scrollWidth};});add('site768-form-fits',details.right<=768,{width:768,details,screenshot:await shot(a,'proof-site768-editor')});
const p1=await a.locator('.site-reviews-list .review-item').allTextContents();await a.locator('.pagination a[href*="page=2"]').first().click();await a.waitForLoadState('domcontentloaded');const p2=await a.locator('.site-reviews-list .review-item').allTextContents();add('site-native-pagination',p1.length===12&&p2.length===12&&p1.every(x=>!p2.includes(x)),{firstCount:p1.length,secondCount:p2.length,url:a.url(),screenshot:await shot(a,'site-pagination2')});
await a.goto(base+'/ru/place-reviews/');const count=await a.locator('.place-review-card,.review-item').count();const next=a.locator('.pagination a[href*="page=2"]').first();if(await next.count()){await next.click();await a.waitForLoadState('domcontentloaded');add('place-index-pagination',a.url().includes('page=2'),{firstCount:count,url:a.url(),screenshot:await shot(a,'place-review-pagination2')});}
}catch(err){rows.push({id:'pagination-harness',status:'NOT RUN',role:'author',lang:'ru',width:768,error:String(err).slice(0,400)});}
const s=await state(a);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}
