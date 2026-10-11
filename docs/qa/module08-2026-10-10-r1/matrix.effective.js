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
},rows=[],diagnostics=[];
 const auth={};for(const role of ['admin','volunteer','reviewer']){
  const c=await original.context().browser().newContext();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors[role].username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);auth[role]=await c.storageState();await c.close();
 }
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width,height:950},storageState:auth.admin}),p=await c.newPage();p.setDefaultTimeout(9000);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const errors=[],failed=[];p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('requestfailed',r=>failed.push({url:r.url().replace(/\?.*/,''),local:r.url().startsWith(B),error:r.failure()?.errorText}));
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',lang,width,role:'admin',...x});
  const shot=async state=>{const file=state+'-'+lang+'-'+width+'.png';await p.screenshot({path:D+file,fullPage:true,animations:'disabled'});return file};
  const capture=async(state,status)=>{const file=await shot(state),g=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,content:document.querySelector('main,.content-wrapper')?.innerText.slice(0,350),broken:[...document.images].filter(x=>x.getBoundingClientRect().width>0&&x.complete&&!x.naturalWidth&&x.src.startsWith(location.origin)).map(x=>x.getAttribute('src'))}));add(state+'-render',Boolean(g.content),{http:status,url:p.url(),screenshot:file});add(state+'-overflow',g.scroll<=width+1,{geometry:g,screenshot:file});add(state+'-images',g.broken.length===0,{broken:g.broken,screenshot:file});};
  try{
   const states=[['admin-home','admin/'],['place-queue','admin/catalog/place/'],['organization-queue','admin/catalog/organization/'],['event-queue','admin/catalog/event/'],['specialist-queue','admin/catalog/specialist/'],['hub','admin/volunteer/moderation/'],['hub-page2','admin/volunteer/moderation/?page=2'],['hub-empty','admin/volunteer/moderation/?entity=offering_group'],['hub-filter-error','admin/volunteer/moderation/?author=bad'],['hub-conflict','admin/volunteer/moderation/content/'+F.revisions.conflict+'/'],['hub-long-comparison','admin/volunteer/moderation/content/'+F.revisions.filler3+'/'],['legacy-photo-review','admin/volunteer/review/'+F.places.live+'/'],['sla','admin/moderation-sla/']];
   for(const [state,path]of states){const r=await p.goto(B+pre+path);await capture(state,r.status());add(state+'-HTTP',r.status()===(state==='hub-filter-error'?400:200),{http:r.status()});
    if(state==='hub'){
     const tableRows=await p.locator('.km-volunteer-hub-table tbody tr').count(),links=await p.locator('main a[href*="page=2"]').count();add('hub-pagination-navigation',links>0,{tableRows,visibleNextLinks:links,screenshot:'hub-'+lang+'-'+width+'.png'});
     await p.locator('#hub-entity').focus();await p.keyboard.press('Space');await shot('hub-select-open');await p.keyboard.press('Escape');await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');const f=await p.locator('#hub-entity').evaluate(e=>({active:e===document.activeElement,outline:getComputedStyle(e).outlineStyle,shadow:getComputedStyle(e).boxShadow}));add('hub-keyboard-focus',f.active&&(f.outline!=='none'||f.shadow!=='none'),{focus:f});
     await p.locator('#hub-entity').selectOption('organization');await Promise.all([p.waitForLoadState('domcontentloaded'),p.locator('.km-volunteer-hub-filters button').click()]);await p.waitForTimeout(80);add('native-filter-organization',await p.locator('.km-volunteer-hub-table tbody tr td:first-child').evaluateAll(es=>es.every(e=>['Организация','Təşkilat','Organization'].includes(e.textContent.trim()))));await shot('hub-filtered');
    }
    if(state==='hub-filter-error')add('filter-error-focus',(await p.locator('#hub-filter-error').evaluate(e=>e===document.activeElement)),{screenshot:'hub-filter-error-'+lang+'-'+width+'.png'});
    if(state==='hub-conflict')add('conflict-approve-disabled',await p.locator('[value=approve]').isDisabled(),{screenshot:'hub-conflict-'+lang+'-'+width+'.png'});
    if(state==='place-queue'){
     const search=p.locator('#searchbar');if(await search.count()){await search.fill('QA08 incomplete');await search.press('Enter');await p.waitForLoadState('domcontentloaded');await p.waitForTimeout(80);add('native-place-search',await p.locator('[name=_selected_action]').count()===1);await shot('place-search');}
    }
   }
   await p.goto(B+pre+'admin/catalog/place/');const toggle=p.locator('[data-widget=pushmenu]:visible');if(await toggle.count()){await toggle.first().click();await p.waitForTimeout(300);await shot('sidebar-open');await p.keyboard.press('Escape');await p.waitForTimeout(300);add('sidebar-Escape-close',!(await p.locator('body').getAttribute('class')).includes('sidebar-open'),{screenshot:'sidebar-open-'+lang+'-'+width+'.png'});}
  }catch(e){rows.push({id:'matrix-harness',status:'NOT RUN',lang,width,error:String(e),url:p.url()});await shot('matrix-harness-error');}
  diagnostics.push({lang,width,errors,failed});await c.close();
  const vc=await original.context().browser().newContext({viewport:{width,height:950},storageState:auth.volunteer}),vp=await vc.newPage();await vc.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
  for(const [state,path] of [['volunteer-list','admin/volunteer/'],['volunteer-edit','admin/volunteer/'+F.places.volunteer+'/edit/'],['volunteer-proposal','admin/volunteer/proposal/organization/'+F.organizations.reject+'/']]){try{const r=await vp.goto(B+pre+path);const file=state+'-'+lang+'-'+width+'.png';await vp.screenshot({path:D+file,fullPage:true,animations:'disabled'});rows.push({id:state+'-render',status:r.status()===200?'PASS':'FAIL',lang,width,role:'volunteer',http:r.status(),screenshot:file});const g=await vp.evaluate(()=>document.documentElement.scrollWidth);rows.push({id:state+'-overflow',status:g<=width+1?'PASS':'FAIL',lang,width,role:'volunteer',scroll:g,screenshot:file});}catch(e){rows.push({id:state+'-harness',status:'NOT RUN',lang,width,role:'volunteer',error:String(e)})}}
  await vc.close();
 }
 return {rows,diagnostics,browser:original.context().browser().version()};
}
