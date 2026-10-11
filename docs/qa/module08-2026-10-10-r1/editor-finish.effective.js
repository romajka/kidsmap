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
},rows=[],c=await original.context().browser().newContext({viewport:{width:1440,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.setDefaultTimeout(9000);await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors.admin.username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);const state=async()=>(await p.request.get(B+'/qa/state/')).json();const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'admin',lang:'ru',width:1440,...x});
 for(const [kind,id] of [['event',2],['specialist',1]])try{
  await p.goto(B+'/ru/admin/catalog/'+kind+'/'+id+'/change/');if(kind==='event')await p.locator('[data-km-admin-step-link][href="#media"]').click();else await p.locator('.km-specialist-nav a').last().click();await p.locator('[name=status]').selectOption('rejected');await p.locator('[name=rejection_reason]').fill('SYNTHETIC QA08 valid refusal');
  const controls=await p.locator('[name=_save],[name=_continue]').evaluateAll(es=>es.map(e=>({tag:e.tagName,type:e.type,name:e.name,visible:!!e.getClientRects().length,form:e.form?.id,formAction:e.form?.getAttribute('action')})));await p.locator('[name=_save],[name=_continue]').filter({visible:true}).first().click();await p.waitForTimeout(500);const modal=p.locator('.km-modal[role=alertdialog],.km-modal[role=dialog]');if(await modal.count()){const text=await modal.innerText();rows.push({id:kind+'-native-save-confirmation',status:'PASS',role:'admin',lang:'ru',width:1440,text});await modal.locator('.km-btn-modal--primary,.km-btn-modal--warning,.km-btn-modal--danger').click();await p.waitForTimeout(500);}await p.waitForLoadState('domcontentloaded');
  const s=await state(),table=kind==='event'?'events':'specialists',item=s[table].find(x=>x.id===id),errors=await p.locator('.errorlist').allTextContents();const file=kind+'-valid-native-rejection.png';await p.screenshot({path:D+file,fullPage:false,animations:'disabled'});add(kind+'-valid-native-reject-reason',item.status==='rejected'&&item.rejection_reason==='SYNTHETIC QA08 valid refusal',{url:p.url(),item,errors,controls,screenshot:file,ui:(await p.locator('body').innerText()).slice(0,1200)});
  if(item.status!=='rejected'){rows.push({id:kind+'-following-reject-resubmit-approve',status:'NOT RUN',reason:'Reject did not persist; fixture/form cause must be reviewed; not inferred as app defect.'});continue;}
  await p.goto(B+'/ru/admin/catalog/'+kind+'/');const checkbox=p.locator('[name=_selected_action][value="'+id+'"]');await checkbox.check();await p.locator('[data-bulk-submit=mark_pending]').click();await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(150);let t=(await state())[table].find(x=>x.id===id);add(kind+'-valid-native-resubmit',t.status==='pending'&&t.rejection_reason==='');await p.locator('[name=_selected_action][value="'+id+'"]').check();await p.locator('[data-bulk-submit=mark_published]').click();await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(150);t=(await state())[table].find(x=>x.id===id);const shot=kind+'-valid-native-approved.png';await p.screenshot({path:D+shot,fullPage:false,animations:'disabled'});add(kind+'-valid-native-approve',t.status==='published',{item:t,screenshot:shot,notice:await p.locator('.messagelist').allTextContents()});
 }catch(e){rows.push({id:kind+'-editor-finish-harness',status:'NOT RUN',error:String(e),url:p.url()});}
 const s=await state();await c.close();return{rows,final_state:s};
}
