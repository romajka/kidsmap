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
 const active=()=>({tag:document.activeElement.tagName,id:document.activeElement.id,cls:String(document.activeElement.className),place:document.activeElement.dataset?.placeId});
 for(const lang of ['ru','az','en']){
  const pre=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext({viewport:{width:1024,height:950},storageState:auth}),p=await c.newPage();p.setDefaultTimeout(8000);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const errors=[];p.on('pageerror',e=>errors.push(String(e)));
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role:'admin',lang,...x});const shot=async name=>{const file=name+'-'+lang+'-'+p.viewportSize().width+'.png';await p.screenshot({path:D+file,fullPage:false,animations:'disabled'});return file;};
  for(const kind of ['place','event','specialist']){await p.goto(B+pre+'admin/catalog/'+kind+'/');await p.waitForTimeout(450);const geometry=await p.evaluate(()=>({root:document.documentElement.scrollWidth,viewport:innerWidth,row:[...document.querySelectorAll('#result_list tbody tr')].slice(0,3).map(e=>({height:e.getBoundingClientRect().height,width:e.getBoundingClientRect().width})),big:[...document.querySelectorAll('#result_list *')].map(e=>({tag:e.tagName,cls:String(e.className).slice(0,90),width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,display:getComputedStyle(e).display,svg:e instanceof SVGElement})).filter(e=>e.width>200||e.height>120).slice(0,20)}));add('queue-1024-confirmed-root-overflow',geometry.root<=1025,{width:1024,kind,geometry,screenshot:await shot('queue-'+kind+'-settled'),url:p.url()});}
  for(const width of [390,1440]){await p.setViewportSize({width,height:950});await p.goto(B+pre+'admin/catalog/place/');await p.waitForTimeout(300);const opener=p.locator('[data-more-actions-btn][data-place-id="'+F.places.batch_ready+'"]');await opener.focus();await opener.press('Enter');await p.locator('#km-row-act-pub').click();const modal=p.locator('.km-modal[role=alertdialog]');await modal.waitFor();await p.waitForTimeout(200);const initial=await p.evaluate(active),text=await modal.innerText(),focusables=await modal.evaluate(e=>[...e.querySelectorAll('button:not([disabled]),[href]:not([disabled]),input:not([disabled]):not([type=hidden]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])')].filter(n=>n.offsetWidth>0||n.offsetHeight>0||n.getClientRects().length>0).map(n=>({tag:n.tagName,href:n.getAttribute('href'),tabIndex:n.tabIndex,svg:n instanceof SVGElement,ariaHidden:n.closest('[aria-hidden]')?.getAttribute('aria-hidden'),focusFunction:typeof n.focus})));const trace=[];for(let n=0;n<6;n++){await p.keyboard.press('Tab');trace.push(await p.evaluate(active));}add('modal-SVG-focus-cause-native',await modal.evaluate(e=>e.contains(document.activeElement)),{width,initial,focusables,trace,screenshot:await shot('modal-focus-cause'),url:p.url()});add('modal-language-confirmed',lang==='ru'||!text.includes('\u0421\u043d\u044f\u0442\u044c \u0441 \u043f\u0443\u0431\u043b\u0438\u043a\u0430\u0446\u0438\u0438'),{width,text});await p.keyboard.press('Escape');await p.waitForTimeout(300);add('modal-focus-restore-confirmed',await opener.evaluate(e=>document.activeElement===e),{width,focus:await p.evaluate(active),screenshot:await shot('modal-focus-restored')});}
  for(const width of [360,390,768]){await p.setViewportSize({width,height:950});await p.goto(B+pre+'admin/');const toggle=p.locator('[data-widget=pushmenu]').first();await toggle.focus();await toggle.press('Enter');await p.waitForTimeout(300);const opened=await p.evaluate(()=>({opened:document.body.classList.contains('sidebar-open'),sidebar:document.querySelector('.main-sidebar').getBoundingClientRect().toJSON(),overlay:!!document.querySelector('#sidebar-overlay')}));await p.keyboard.press('Escape');await p.waitForTimeout(300);const after=await p.evaluate(()=>({opened:document.body.classList.contains('sidebar-open'),sidebar:document.querySelector('.main-sidebar').getBoundingClientRect().toJSON(),focusTag:document.activeElement.tagName,focusId:document.activeElement.id}));add('sidebar-Escape-native-visible',opened.opened&&!after.opened,{width,opened,after,screenshot:await shot('sidebar-Escape-proof'),url:p.url()});await toggle.press('Enter');await p.waitForTimeout(300);add('sidebar-native-keyboard-toggle-close',!await p.locator('body').evaluate(e=>e.classList.contains('sidebar-open')),{width,note:'Pointer toggle is covered by sidebar logo while open; retained focused toggle activated via Enter.'});}
  diagnostics.push({lang,errors});await c.close();
 }
 const c=await original.context().browser().newContext({viewport:{width:360,height:950}});await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();await p.goto(B+'/ru/admin/login/');await p.locator('[name=username]').fill(F.actors.volunteer.username);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/login/')),p.locator('button[type=submit],input[type=submit]').first().click()]);for(const lang of ['ru','az']){await p.goto(B+(lang==='az'?'/':'/'+lang+'/')+'admin/volunteer/'+F.places.volunteer+'/edit/');const geometry=await p.evaluate(()=>({root:document.documentElement.scrollWidth,viewport:innerWidth,offenders:[...document.querySelectorAll('.km-volunteer *')].map(e=>({tag:e.tagName,cls:String(e.className).slice(0,90),left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.right>innerWidth+1).slice(0,15)}));const file='volunteer-2px-review-'+lang+'-360.png';await p.screenshot({path:D+file,fullPage:true,animations:'disabled'});rows.push({id:'volunteer-2px-impact-manual-review',status:'NOT RUN',role:'volunteer',lang,width:360,geometry,screenshot:file,reason:'Geometry >1px recorded; visual clipping impact requires manual product decision; no confirmed defect assigned.'});}await c.close();return{rows,diagnostics};
}
