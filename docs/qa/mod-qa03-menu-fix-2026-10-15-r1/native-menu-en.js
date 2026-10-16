async original=>{
const B='http://127.0.0.1:57187',H='/home/ramin/kidsmap/docs/qa/mod-qa03-menu-fix-2026-10-15-r1',LANG='en';
const c=await original.context().browser().newContext(),p=await c.newPage(),rows=[],diagnostics=[],boundary=[];let model='place',width=1024,sidebar='expanded',index=0,kind='base';
await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
p.on('pageerror',e=>diagnostics.push({kind:'pageerror',lang:LANG,model,width,sidebar,text:String(e).split('\n')[0]}));p.on('requestfailed',r=>diagnostics.push({kind:'requestfailed',lang:LANG,model,width,sidebar,local:r.url().startsWith(B+'/'),host:new URL(r.url()).host,error:r.failure()?.errorText}));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)diagnostics.push({kind:'http',local:true,status:r.status(),model,width,sidebar});});p.on('console',m=>{if(m.type()==='error')diagnostics.push({kind:'console',local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]'),model,width,sidebar});});
const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',lang:LANG,model,width,sidebar,index,kind,detail});
const wait=async()=>{await p.waitForLoadState('networkidle');};const tick=async()=>await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
const source=await(await p.request.get(B+'/qa/source/')).json(),before=await(await p.request.get(B+'/qa/state/')).json();
const checkpoint=async complete=>{await p.request.post(B+'/qa/checkpoint/'+LANG+'/',{data:{rows,diagnostics,boundary,source:{pid:source.pid,startup_matches_disk:source.startup_matches_disk},mode:'actual approved source JS; no injected response/styles',before,complete}});};
const F=await(await p.request.get(B+'/qa/fixtures/')).json();await p.setViewportSize({width,height:950});
await p.goto(B+'/ru/admin/login/?next=/ru/admin/catalog/place/');await p.locator('[name=username]').fill(F.actors.admin);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/catalog/place/')),p.locator('form button[type=submit]').click()]);await wait();
await p.locator('.km-admin-lang-btn').click();const languageForm=p.locator('form.km-admin-lang-switch-form').filter({has:p.locator('input[name=language][value='+LANG+']')});await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),languageForm.locator('button[type=submit]').click()]);await wait();add('native language menu actual locale',await p.locator('html').getAttribute('lang')===LANG);
const sidebarState=async()=>await p.locator('.main-sidebar').evaluate(e=>{const r=e.getBoundingClientRect();return r.width>150&&r.right>150&&r.left>=-1;});
const setSidebar=async want=>{if(await sidebarState()!==want){if(width<768&&!want&&await p.locator('#sidebar-overlay').isVisible())await p.locator('#sidebar-overlay').click({position:{x:width-20,y:100}});else await p.locator('.km-admin-header__toggle').click();}await p.waitForFunction(({want,width})=>{const r=document.querySelector('.main-sidebar').getBoundingClientRect();return width>=768?Math.abs(r.width-(want?300:72))<1:(want?r.left>=-1:r.right<=1);},{want,width});};
const measure=async loc=>await loc.evaluate(e=>{const r=e.getBoundingClientRect(),points=[[r.x+r.width/2,r.y+r.height/2],[r.x+5,r.y+5],[r.right-5,r.bottom-5]];return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,viewport:innerWidth,root:document.documentElement.scrollWidth,hit:points.every(([x,y])=>e.contains(document.elementFromPoint(x,y))),tableAncestor:!!e.closest('.card-body.table-responsive')};});
for(model of ['place','event'])for(width of [360,390,768,1024,1280,1440]){
 await p.setViewportSize({width,height:950});await p.goto(B+(LANG==='az'?'/':'/'+LANG+'/')+'admin/catalog/'+model+'/');await wait();
 for(sidebar of ['expanded','collapsed']){
 try{
 await setSidebar(sidebar==='expanded');add('native sidebar stable and locale retained',await sidebarState()===(sidebar==='expanded')&&await p.locator('html').getAttribute('lang')===LANG);
 if(width<768&&sidebar==='expanded'){add('native mobile overlay visible',await p.locator('#sidebar-overlay').isVisible());boundary.push({lang:LANG,model,width,sidebar,status:'NOT RUN',reason:'native overlay blocks background menus; all row interactions performed after native close in collapsed state'});await p.screenshot({path:H+'/screenshots/menu-overlay-'+LANG+'-'+model+'-'+width+'.png',fullPage:false,animations:'disabled'});continue;}
 const surface=p.locator('.card-body.table-responsive');await surface.scrollIntoViewIfNeeded();let box=await surface.boundingBox();await p.mouse.move(box.x+box.width/2,box.y+Math.min(80,box.height/2));await p.mouse.wheel(10000,0);await p.waitForTimeout(120);const scroll=await surface.evaluate(e=>({left:e.scrollLeft,max:e.scrollWidth-e.clientWidth,page:document.documentElement.scrollLeft}));add('native local wheel reaches actions without page overflow',Math.abs(scroll.left-scroll.max)<2&&scroll.page===0,scroll);
 for(index of [0,2]){
 const row=p.locator('#result_list tbody tr').nth(index);
 for(const spec of model==='place'?[['[data-readiness-trigger]','#km-readiness-popover','readiness'],['[data-more-actions-btn]','#km-row-actions-dropdown','actions']]:[['summary.km-admin-action-menu__toggle','.km-admin-action-menu__panel','actions']]){
 const [selector,panelSelector,name]=spec;kind=name;
 try{
 const trigger=row.locator(selector),nativeDetails=model==='event'?row.locator('details.km-admin-action-menu'):null;
 let originalPanel=null,originalStyle=null,originalLinks=null;
 if(model==='event'){originalPanel=await row.locator(panelSelector).elementHandle();originalStyle=await originalPanel.getAttribute('style');originalLinks=await originalPanel.evaluate(e=>[...e.querySelectorAll('a')].map(x=>({href:x.getAttribute('href'),text:x.textContent})));}
 const panel=()=>model==='event'?p.locator('body > '+panelSelector):p.locator(panelSelector);
 const open=async keyboard=>{if(keyboard)await trigger.press('Enter');else await trigger.click();await panel().waitFor({state:'visible'});await tick();};
 const closed=async()=>model==='event'?!await nativeDetails.evaluate(e=>e.open)&&await p.locator('body > '+panelSelector).count()===0:!await p.locator(panelSelector).isVisible();
 await open(index===2);const g=await measure(panel());add('row panel within viewport and hit-test reachable',g.left>=0&&g.right<=width+1&&g.top>=0&&g.bottom<=951&&g.hit,g);add('row panel escapes table clipping and root fits',!g.tableAncestor&&g.root<=width+1,g);
 if(model==='event'){const same=await originalPanel.evaluate(e=>e.parentElement===document.body);const links=await panel().evaluate(e=>[...e.querySelectorAll('a')].map(x=>({href:x.getAttribute('href'),text:x.textContent})));add('Event portal preserves same node and original href labels',same&&JSON.stringify(links)===JSON.stringify(originalLinks));add('Event first menu option receives focus',await panel().evaluate(e=>e.contains(document.activeElement)));}
 if(index===2&&kind==='actions'){const focus=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e);return{tag:e.tagName,cls:e.className,visible:e.matches(':focus-visible'),outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow};});add('keyboard open keeps visible focus',focus.visible&&((focus.outline!=='none'&&focus.width!=='0px')||focus.shadow!=='none'),focus);}
 await p.screenshot({path:H+'/screenshots/menu-'+LANG+'-'+model+'-'+width+'-'+sidebar+'-'+index+'-'+kind+'.png',fullPage:false,animations:'disabled'});
 if(kind==='readiness'){await trigger.click();add('readiness closes and reopens without mutation',!await p.locator(panelSelector).isVisible());continue;}
 await p.keyboard.press('Escape');add('Escape closes and restores exact trigger focus',await closed()&&await trigger.evaluate(e=>e===document.activeElement));
 if(model==='event')add('Event close restores original node parent and style',await originalPanel.evaluate((e,style)=>!!e.closest('details.km-admin-action-menu')&&e.getAttribute('style')===style,originalStyle));
 if(index===0){
 await open(true);await p.locator('h1').click();add('outside click closes row menu',await closed());
 await open(true);await p.setViewportSize({width:width+1,height:950});await tick();add('native resize closes row menu',await closed());await p.setViewportSize({width,height:950});await tick();
 await open(true);box=await surface.boundingBox();await p.mouse.move(box.x+box.width/2,Math.min(900,box.y+Math.min(70,box.height/2)));const old=await surface.evaluate(e=>e.scrollLeft);await p.mouse.wheel(old>0?-120:120,0);await p.waitForTimeout(160);const moved=await surface.evaluate(e=>e.scrollLeft);if(Math.abs(moved-old)>0.5)add('native horizontal scroll closes row menu',await closed(),{old,moved});else{boundary.push({lang:LANG,model,width,sidebar,index,kind,status:'NOT RUN',reason:'no actual horizontal movement at this fitting table size; dismissal tested on movable sizes'});await p.keyboard.press('Escape');}
 if(model==='event'){await open(true);await p.keyboard.press('Shift+Tab');await tick();add('native keyboard focus leaving Event menu closes it',await closed());}
 add('repeated lifecycle leaves no body portal',await p.locator('body > .km-admin-action-menu__panel').count()===0);
 }
 }catch(e){rows.push({id:'row menu interaction completion',status:'NOT RUN',lang:LANG,model,width,sidebar,index,kind,error:String(e).split('\n')[0]});try{await p.keyboard.press('Escape');await p.locator('h1').click();}catch{}}
 }
 }
 await checkpoint(false);
 }catch(e){rows.push({id:'matrix cell completion',status:'NOT RUN',lang:LANG,model,width,sidebar,error:String(e).split('\n')[0]});await checkpoint(false);}
 }
}
const after=await(await p.request.get(B+'/qa/state/')).json();add('own synthetic domain data unchanged',JSON.stringify(before)===JSON.stringify(after),{before,after});const result={rows,diagnostics,boundary,before,after,source:{pid:source.pid,startup_matches_disk:source.startup_matches_disk},complete:true,mode:'actual approved JS from own runtime; native pointer/keyboard/scroll/resize, no CSS/JS injection or domain action selected'};await p.request.post(B+'/qa/checkpoint/'+LANG+'/',{data:result});await c.close();return result;
}
