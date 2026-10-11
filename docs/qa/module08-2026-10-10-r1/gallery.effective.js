async original=>{
 const B='http://localhost:8821',D='C:/kidsmap/docs/qa/module08-2026-10-10-r1/screenshots/',F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa08_owner",
      "email": "owner08@example.invalid"
    },
    "outsider": {
      "id": 2,
      "username": "qa08_outsider",
      "email": "outsider08@example.invalid"
    },
    "volunteer": {
      "id": 3,
      "username": "qa08_volunteer",
      "email": "volunteer08@example.invalid"
    },
    "volunteer_b": {
      "id": 4,
      "username": "qa08_volunteer_b",
      "email": "volunteer_b08@example.invalid"
    },
    "moderator": {
      "id": 5,
      "username": "qa08_moderator",
      "email": "moderator08@example.invalid"
    },
    "reviewer": {
      "id": 6,
      "username": "qa08_reviewer",
      "email": "reviewer08@example.invalid"
    },
    "reviewer_b": {
      "id": 7,
      "username": "qa08_reviewer_b",
      "email": "reviewer_b08@example.invalid"
    },
    "staff": {
      "id": 8,
      "username": "qa08_staff",
      "email": "staff08@example.invalid"
    },
    "admin": {
      "id": 9,
      "username": "qa08_admin",
      "email": "admin08@example.invalid"
    }
  },
  "places": {
    "live": 1,
    "batch_ready": 2,
    "volunteer": 3,
    "foreign": 4,
    "revoke": 5,
    "delete": 6,
    "batch_bad": 7
  },
  "organizations": {
    "flow": 1,
    "reject": 2,
    "conflict": 3,
    "filler3": 4,
    "filler4": 5,
    "filler5": 6,
    "filler6": 7,
    "filler7": 8,
    "filler8": 9,
    "filler9": 10,
    "filler10": 11,
    "filler11": 12,
    "filler12": 13,
    "filler13": 14,
    "filler14": 15,
    "filler15": 16,
    "filler16": 17,
    "filler17": 18,
    "filler18": 19,
    "filler19": 20,
    "filler20": 21,
    "filler21": 22,
    "filler22": 23,
    "filler23": 24,
    "filler24": 25,
    "filler25": 26,
    "filler26": 27,
    "filler27": 28,
    "filler28": 29,
    "filler29": 30,
    "filler30": 31,
    "filler31": 32
  },
  "revisions": {
    "live": 1,
    "revoke": 2,
    "flow": 3,
    "reject": 4,
    "conflict": 5,
    "filler3": 6,
    "filler4": 7,
    "filler5": 8,
    "filler6": 9,
    "filler7": 10,
    "filler8": 11,
    "filler9": 12,
    "filler10": 13,
    "filler11": 14,
    "filler12": 15,
    "filler13": 16,
    "filler14": 17,
    "filler15": 18,
    "filler16": 19,
    "filler17": 20,
    "filler18": 21,
    "filler19": 22,
    "filler20": 23,
    "filler21": 24,
    "filler22": 25,
    "filler23": 26,
    "filler24": 27,
    "filler25": 28,
    "filler26": 29,
    "filler27": 30,
    "filler28": 31,
    "filler29": 32,
    "filler30": 33,
    "filler31": 34
  },
  "event": 1,
  "specialist": 1,
  "private_document": 1,
  "synthetic_only": true
},rows=[],contexts=[];
 const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang:'ru',width:1440,...x});
 const setup=async role=>{const c=await original.context().browser().newContext({viewport:{width:1440,height:950}});contexts.push(c);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(12000);await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('.auth-form button[type=submit]:visible').click()]);return p;};
 const shot=async(p,name)=>{await p.screenshot({path:D+name+'.png',fullPage:true,animations:'disabled'});return name+'.png';};
 const state=async p=>(await p.request.get(B+'/qa/state/')).json();
 const a=await setup('admin'),o=await setup('owner');
 try{
  const pid=F.places.batch_ready,url=B+'/ru/account/places/'+pid+'/edit/';await o.goto(url);const before=await state(a);await o.locator('[name=name_az]').fill('Uydurma QA08 gallery moderated');await o.locator('[name=photo]').setInputFiles('C:/kidsmap/.tmp/module08-20261010-r1/assets/gallery.png');await o.locator('[name=gallery_images]').setInputFiles(['C:/kidsmap/.tmp/module08-20261010-r1/assets/candidate.png','C:/kidsmap/.tmp/module08-20261010-r1/assets/live.png']);await o.locator('[name=form_action][value=save_draft]').click();await o.waitForTimeout(700);let s=await state(a),rev=s.revisions.find(r=>r.place_id===pid);add('owner-gallery-draft-candidate',rev?.status==='draft'&&rev.payload.gallery?.length===2&&s.photos.filter(p=>p.place_id===pid).length===0&&s.places.find(p=>p.id===pid).photo===before.places.find(p=>p.id===pid).photo,{role:'owner',state:rev,screenshot:await shot(o,'gallery-draft-candidate')});
  await o.reload();add('owner-gallery-reload',(await o.locator('[name=name_az]').inputValue())==='Uydurma QA08 gallery moderated',{role:'owner',screenshot:await shot(o,'gallery-owner-reload')});await o.locator('[name=form_action][value=save_and_publish]').click();await o.waitForTimeout(700);s=await state(a);rev=s.revisions.find(r=>r.place_id===pid);add('owner-gallery-submit-pending',rev.status==='pending',{role:'owner',screenshot:await shot(o,'gallery-owner-pending')});
  const review=B+'/ru/admin/volunteer/moderation/content/'+rev.id+'/';await a.goto(review);add('hub-gallery-photo-preview',await a.locator('.km-volunteer img').count()>0,{role:'admin',screenshot:await shot(a,'gallery-hub-paths-only')});const compare=await a.locator('.km-volunteer-comparison').innerText();add('hub-gallery-saved-paths-visible',compare.includes('gallery')||compare.includes('галере')||compare.includes('image'),{role:'admin',text:compare.slice(0,1500)});await a.locator('[name=reason]').fill('SYNTHETIC QA08 photos and gallery verified');await a.locator('[name=action][value=approve]').click();await a.waitForLoadState('domcontentloaded');await a.waitForTimeout(200);s=await state(a);rev=s.revisions.find(r=>r.id===rev.id);add('gallery-approved-atomic-live',rev.status==='approved'&&s.photos.filter(p=>p.place_id===pid).length===2&&s.places.find(p=>p.id===pid).photo!==before.places.find(p=>p.id===pid).photo,{role:'admin',state:rev});
  const c=await original.context().browser().newContext();contexts.push(c);const p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const r=await p.goto(B+'/place/'+pid+'/');await p.reload();const imgs=await p.locator('img').evaluateAll(es=>es.map(e=>({src:e.getAttribute('src'),loaded:e.naturalWidth>0})));add('gallery-public-reload',r.status()===200&&imgs.filter(i=>i.loaded&&i.src?.includes('gallery/')).length>=2,{role:'anonymous',url:p.url(),images:imgs,screenshot:await shot(p,'gallery-public-approved')});
 }catch(e){rows.push({id:'gallery-harness',status:'NOT RUN',error:String(e),url:o.url()});await shot(o,'gallery-harness-error');}
 // Discard own malformed initial setup candidates through the actual reviewer UI.
 for(const id of [F.revisions.live,F.revisions.revoke]){
  await a.goto(B+'/ru/admin/volunteer/moderation/content/'+id+'/');if(await a.locator('[name=reason]').count()){await a.locator('[name=reason]').fill('SYNTHETIC QA08 initial fixture gallery was malformed; exclude setup attempt');await a.locator('[name=action][value=reject]').click();await a.waitForLoadState('domcontentloaded');await a.waitForTimeout(100);}
 }
 for(const c of contexts)await c.close();return{rows};
}
