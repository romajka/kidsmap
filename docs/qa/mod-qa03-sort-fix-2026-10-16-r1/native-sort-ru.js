async original=>{
const B='http://127.0.0.1:45135',H='/home/ramin/kidsmap/docs/qa/mod-qa03-sort-fix-2026-10-16-r1',LANG='ru',F=await(await original.request.get(B+'/qa/fixtures/')).json();
const c=await original.context().browser().newContext(),p=await c.newPage(),rows=[],diagnostics=[],boundary=[];let model='event',width=1024,sidebar='expanded';
await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
p.on('pageerror',e=>diagnostics.push({kind:'pageerror',local:true,model,width,sidebar,text:String(e).split('\n')[0]}));p.on('requestfailed',r=>diagnostics.push({kind:'requestfailed',local:r.url().startsWith(B+'/'),host:new URL(r.url()).host,error:r.failure()?.errorText}));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)diagnostics.push({kind:'http',local:true,status:r.status()});});p.on('console',m=>{if(m.type()==='error')diagnostics.push({kind:'console',local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]')});});
const add=(id,ok,detail={})=>rows.push({id,status:ok?'PASS':'FAIL',lang:LANG,model,width,sidebar,detail});
const wait=async()=>await p.waitForLoadState('networkidle');
const nav=async action=>{await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),action()]);await wait();};
const ids=async()=>await p.locator('#result_list tbody input[name=_selected_action]').evaluateAll(es=>es.map(e=>Number(e.value)));
const expected=(key,page=1)=>{const[field,dir]=key.split('_');return [...F.sorting_records[model]].sort((a,b)=>{let v=field==='name'?(a.name<b.name?-1:a.name>b.name?1:0):a[field]-b[field];v||=a.pk-b.pk;return dir==='desc'?-v:v;}).slice((page-1)*F.page_sizes[model],page*F.page_sizes[model]).map(o=>o.pk);};
const LABELS={"created_desc": "Создано (новые)", "created_asc": "Создано (старые)", "updated_desc": "Обновлено (новые)", "updated_asc": "Обновлено (старые)", "name_asc": "По названию (А → Я)", "name_desc": "По названию (Я → А)"};
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const expanded=async()=>await p.locator('.main-sidebar').evaluate(e=>{const r=e.getBoundingClientRect();return r.width>150&&r.right>150&&r.left>=-1;});
const setSidebar=async want=>{if(await expanded()!==want){if(width<768&&!want&&await p.locator('#sidebar-overlay').isVisible())await p.locator('#sidebar-overlay').click({position:{x:width-20,y:100}});else await p.locator('.km-admin-header__toggle').click();}await p.waitForFunction(({want,width})=>{const r=document.querySelector('.main-sidebar').getBoundingClientRect();return width>=768?Math.abs(r.width-(want?300:72))<1:(want?r.left>=-1:r.right<=1);},{want,width});};
const before=await(await p.request.get(B+'/qa/state/')).json();
await p.goto(B+'/ru/admin/login/?next=/ru/admin/catalog/event/');await p.locator('[name=username]').fill(F.actors.admin);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/catalog/event/')),p.locator('form button[type=submit]').click()]);await wait();
await p.locator('.km-admin-lang-btn').click();const form=p.locator('form.km-admin-lang-switch-form').filter({has:p.locator('input[name=language][value='+LANG+']')});await nav(()=>form.locator('button[type=submit]').click());
for(model of ['event','specialist'])for(width of [360,390,768,1024,1280,1440])for(sidebar of ['expanded','collapsed']){
try{
await p.setViewportSize({width,height:950});const base=B+(LANG==='az'?'/':'/'+LANG+'/')+'admin/catalog/'+model+'/';await p.goto(base+'?status__exact=published');await wait();await setSidebar(sidebar==='expanded');
add('native locale and sidebar',await p.locator('html').getAttribute('lang')===LANG&&await expanded()===(sidebar==='expanded'));
if(width<768&&sidebar==='expanded'){boundary.push({lang:LANG,model,width,sidebar,status:'NOT RUN',reason:'native mobile overlay blocks background; sorting exercised after native close'});await p.screenshot({path:H+'/screenshots/overlay-'+LANG+'-'+model+'-'+width+'.png',fullPage:false});continue;}
await p.locator('#searchbar').fill('SORTQA');await nav(()=>p.locator('#searchbar').press('Enter'));
add('native search retains query',new URL(p.url()).searchParams.get('q')==='SORTQA');
// Separate existing search-form status loss: explicit combined URL is the sort precondition.
await p.goto(base+'?q=SORTQA&status__exact=published');await wait();
for(const key of ['created_desc','created_asc','updated_desc','updated_asc','name_asc','name_desc']){
const summary=p.locator('#km-sort-menu>summary');await summary.focus();await p.keyboard.press('Enter');await p.keyboard.press('Tab');
const focus=await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return{option:e.matches('.km-sort-option'),visible:e.matches(':focus-visible'),outline:s.outlineStyle,width:s.outlineWidth,inViewport:r.left>=-1&&r.right<=innerWidth+1};});
add('keyboard option focus '+key,focus.option&&focus.visible&&focus.outline!=='none'&&focus.width!=='0px'&&focus.inViewport,focus);
const option=p.locator('#km-sort-menu .km-sort-option[href*="sort='+key+'"]');await nav(()=>option.click());
const actual=await ids(),want=expected(key);const active=p.locator('#km-sort-menu .km-sort-option.is-active');
add('real row order and retained search '+key,same(actual,want)&&new URL(p.url()).searchParams.get('q')==='SORTQA'&&new URL(p.url()).searchParams.get('status__exact')==='published'&&!new URL(p.url()).searchParams.has('e'),{actual,expected:want});
const title=await p.locator('.km-btn-sort__current').innerText();add('active option and nonempty current label '+key,await active.count()===1&&(await active.getAttribute('href')).includes('sort='+key)&&title.trim()===LABELS[key],{label:title});
}
await p.screenshot({path:H+'/screenshots/sort-'+LANG+'-'+model+'-'+width+'-'+sidebar+'.png',fullPage:false,animations:'disabled'});
const next=p.locator('a.km-redesign-pagination__btn[href*="p=2"]');await nav(()=>next.click());add('native page two preserves order and controls',same(await ids(),expected('name_desc',2))&&new URL(p.url()).searchParams.get('sort')==='name_desc'&&new URL(p.url()).searchParams.get('q')==='SORTQA'&&new URL(p.url()).searchParams.get('status__exact')==='published');
await p.reload();await wait();add('reload retains second page order',same(await ids(),expected('name_desc',2))&&new URL(p.url()).searchParams.get('p')==='2');
await p.locator('#km-sort-menu>summary').click();await nav(()=>p.locator('#km-sort-menu .km-sort-option[href*="sort=created_asc"]').click());add('new sort resets pagination only',!new URL(p.url()).searchParams.has('p')&&same(await ids(),expected('created_asc'))&&new URL(p.url()).searchParams.get('q')==='SORTQA');
await nav(()=>p.locator('.km-btn-reset').click());add('reset clears search sort filters',!new URL(p.url()).searchParams.has('q')&&!new URL(p.url()).searchParams.has('sort')&&!new URL(p.url()).searchParams.has('status__exact')&&await p.locator('#result_list tbody tr').count()===Math.min(F.queue_totals[model],F.page_sizes[model]));
if(model==='event'&&width===1024){const trigger=p.locator('#result_list tbody tr').first().locator('summary.km-admin-action-menu__toggle');await trigger.click();const menu=p.locator('body > .km-admin-action-menu__panel');add('row menu smoke opens',await menu.isVisible());await p.keyboard.press('Escape');add('row menu Escape returns focus',await trigger.evaluate(e=>document.activeElement===e));}
}catch(e){add('native flow completion',false,{error:String(e).split('\n')[0]});}
await p.request.post(B+'/qa/checkpoint/'+LANG+'/',{data:{rows,diagnostics,boundary,mode:'sort native matrix',complete:false}});
}
const after=await(await p.request.get(B+'/qa/state/')).json();add('synthetic domain unchanged',same(before,after),{before,after});const source=await(await p.request.get(B+'/qa/source/')).json();add('running source matches current files',source.startup_matches_disk&&Object.keys(source.source).length===955);
await c.close();return{rows,diagnostics,boundary,source_pid:source.pid,complete:true,mode:'Actual source; native login/language/search/sort/pagination/reload/reset; no asset substitution'};
}
