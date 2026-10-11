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
},rows=[],c=await original.context().browser().newContext({viewport:{width:1440,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(10000);p.on('dialog',d=>d.accept());await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors.admin.username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);const state=async()=>(await p.request.get(B+'/qa/state/')).json();const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'admin',...x});
 for(const lang of ['ru','az','en'])for(const width of [390,1440])try{
  await p.setViewportSize({width,height:950});await p.goto(B+(lang==='az'?'/':'/'+lang+'/')+'admin/catalog/specialist/1/change/');for(const box of await p.locator('#id_specializations input[type=checkbox]').all())await box.uncheck();if(width===390)await p.locator('#specialist-section-jump').selectOption('km-sec-12');else await p.locator('.km-specialist-nav a').last().click();await p.locator('[name=status]').selectOption('rejected');await p.locator('[name=rejection_reason]').fill('SYNTHETIC QA08 valid refusal');const before=await state(),response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/specialist/1/change/'));await p.locator('[name=_save]').click();await response;await p.waitForLoadState('domcontentloaded');const errors=await p.locator('.errorlist').evaluateAll(es=>es.map(e=>({text:e.innerText,field:e.closest('.km-field')?.querySelector('input,textarea,select')?.name}))),banner=p.locator('[data-specialist-errors]'),links=await banner.locator('li a').allTextContents();await banner.scrollIntoViewIfNeeded();const file='specialist-error-banner-'+lang+'-'+width+'.png';await p.screenshot({path:D+file,fullPage:false,animations:'disabled'});add('specialist-native-validation-preserves-state',JSON.stringify(before)===JSON.stringify(await state()),{lang,width,errors});add('specialist-error-summary-human-message',links.length<10&&links.every(s=>s.length>12),{lang,width,links:links.slice(0,24),linkCount:links.length,errors,screenshot:file,url:p.url()});
 }catch(e){rows.push({id:'specialist-error-banner-harness',status:'NOT RUN',lang,width,error:String(e),url:p.url()});}
 try{
  await p.setViewportSize({width:1440,height:950});await p.goto(B+'/ru/admin/catalog/specialist/1/change/');await p.locator('.km-specialist-nav a').nth(2).click();await p.locator('#id_specializations input[type=checkbox]').first().check();await p.locator('.km-specialist-nav a').last().click();await p.locator('[name=status]').selectOption('rejected');await p.locator('[name=rejection_reason]').fill('SYNTHETIC QA08 valid refusal');const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/specialist/1/change/'));await p.locator('[name=_save]').click();await response;await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(100);let item=(await state()).specialists.find(x=>x.id===1);add('specialist-native-refusal-corrected-form',item.status==='rejected'&&item.rejection_reason==='SYNTHETIC QA08 valid refusal',{lang:'ru',width:1440,item});for(const [action,status] of [['mark_pending','pending'],['mark_published','published']]){await p.goto(B+'/ru/admin/catalog/specialist/');await p.locator('[name=_selected_action][value="1"]').check();await p.locator('[data-bulk-submit='+action+']').click();await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(120);item=(await state()).specialists.find(x=>x.id===1);add('specialist-native-'+action,item.status===status,{lang:'ru',width:1440,item});}await p.reload();add('specialist-native-published-reload',(await state()).specialists[0].status==='published',{lang:'ru',width:1440});
 }catch(e){rows.push({id:'specialist-final-corrected-form-harness',status:'NOT RUN',error:String(e),url:p.url()});}
 const s=await state();await c.close();return{rows,final_state:s};
}
