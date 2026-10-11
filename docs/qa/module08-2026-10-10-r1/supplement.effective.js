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
},rows=[],diagnostics=[],auth=await original.context().storageState();
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950},storageState:auth}),p=await c.newPage();p.setDefaultTimeout(8000);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const errors=[],failed=[];p.on('pageerror',e=>errors.push(String(e)));p.on('requestfailed',r=>failed.push({local:r.url().startsWith(B),url:r.url().replace(/\?.*/,''),error:r.failure()?.errorText}));
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang,width,role:'admin',...x});
  const shot=async name=>{const f=name+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+f,fullPage:true,animations:'disabled'});return f};
  try{
   await p.goto(B+pre+'admin/catalog/place/');await p.waitForTimeout(400);const before=await (await p.request.get(B+'/qa/state/')).json();
   if(width===1024){const g=await p.evaluate(()=>({root:document.documentElement.scrollWidth,w:innerWidth,offenders:[...document.querySelectorAll('.content-wrapper *,header *,main *')].map(e=>({tag:e.tagName,cls:String(e.className).slice(0,100),rect:e.getBoundingClientRect(),display:getComputedStyle(e).display,minWidth:getComputedStyle(e).minWidth})).filter(e=>e.display!=='none'&&e.rect.width>0&&(e.rect.right>innerWidth+2||e.rect.left< -2)).slice(0,20)}));add('1024-settled-overflow',g.root<=width+1,{geometry:g,screenshot:await shot('1024-overflow-proof')});}
   const opener=p.locator('[data-more-actions-btn][data-place-id="'+F.places.batch_ready+'"]');await opener.focus();await opener.press('Enter');await p.locator('#km-row-act-pub').click();const modal=p.locator('.km-modal[role=alertdialog]');await modal.waitFor({state:'visible'});await p.waitForTimeout(200);const text=await modal.innerText();add('modal-language',lang==='ru'||!text.includes('РЎРЅСЏС‚СЊ СЃ РїСѓР±Р»РёРєР°С†РёРё'),{text,screenshot:await shot('unpublish-modal')});
   let trapped=true;const trace=[];for(let n=0;n<12;n++){await p.keyboard.press(n<6?'Tab':'Shift+Tab');const f=await modal.evaluate(e=>({inside:e.contains(document.activeElement),tag:document.activeElement.tagName,id:document.activeElement.id,cls:String(document.activeElement.className)}));trace.push(f);trapped=trapped&&f.inside;}add('modal-keyboard-trap',trapped,{trace});await p.keyboard.press('Escape');await p.waitForTimeout(300);add('modal-Escape-close',await p.locator('.km-modal[role=alertdialog]').count()===0);add('modal-visible-focus-return',await opener.evaluate(e=>e===document.activeElement),{focus:await p.evaluate(()=>({tag:document.activeElement.tagName,id:document.activeElement.id,cls:String(document.activeElement.className),place:document.activeElement.dataset.placeId})),screenshot:await shot('modal-closed-focus')});
   // SIMULATED AJAX transport invokes the real loading/error handlers; no server write.
   let release,calls=0;const held=new Promise(r=>release=r);await c.route('**/toggle-publication/',async r=>{calls++;await held;await r.fulfill({status:409,contentType:'application/json',body:JSON.stringify({ok:false,message:'SYNTHETIC QA08 version conflict'})})});
   await opener.click();await p.locator('#km-row-act-pub').click();await p.locator('.km-modal .km-btn-modal--danger,.km-modal .km-btn-modal--primary,.km-modal .km-btn-modal--warning').click();await p.waitForFunction(()=>document.querySelector('[data-more-actions-btn][data-place-id="2"]').disabled);add('quick-action-loading-guard',await opener.isDisabled(),{classification:'SIMULATED delayed AJAX',screenshot:await shot('quick-action-loading')});await p.keyboard.press('Enter');add('quick-action-repeat-single-request',calls===1,{calls,classification:'SIMULATED transport'});release();await p.waitForFunction(()=>!document.querySelector('[data-more-actions-btn][data-place-id="2"]').disabled);await p.waitForTimeout(200);add('quick-action-conflict-visible',(await p.locator('body').innerText()).includes('SYNTHETIC QA08 version conflict'),{classification:'SIMULATED409; actual backend stale checked independently',screenshot:await shot('quick-action-conflict')});
   await c.unroute('**/toggle-publication/');await c.route('**/toggle-publication/',r=>r.abort('failed'));await opener.click();await p.locator('#km-row-act-pub').click();await p.locator('.km-modal .km-btn-modal--danger,.km-modal .km-btn-modal--primary,.km-modal .km-btn-modal--warning').click();await p.waitForFunction(()=>!document.querySelector('[data-more-actions-btn][data-place-id="2"]').disabled);await p.waitForTimeout(200);add('quick-action-network-error-retry-enabled',await opener.isEnabled(),{classification:'SIMULATED aborted AJAX',screenshot:await shot('quick-action-network-error')});add('simulated-transport-content-preserved',JSON.stringify(before)===JSON.stringify(await (await p.request.get(B+'/qa/state/')).json()));
   await p.goto(B+pre+'admin/volunteer/moderation/');await p.waitForTimeout(250);const r=await p.request.get(B+pre+'admin/volunteer/moderation/?page=2');add('pagination-second-page-HTTP',r.status()===200,{http:r.status(),note:'HTTP only; missing UI link remains failure'});
  }catch(e){rows.push({id:'supplement-harness',status:'NOT RUN',lang,width,error:String(e),url:p.url()});await shot('supplement-harness-error');}
  diagnostics.push({lang,width,errors,failed});await c.close();
 }
 return {rows,diagnostics};
}
