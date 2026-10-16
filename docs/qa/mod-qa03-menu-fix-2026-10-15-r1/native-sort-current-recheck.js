async original=>{
const B='http://127.0.0.1:57187',H='/home/ramin/kidsmap/docs/qa/mod-qa03-menu-fix-2026-10-15-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json(),c=await original.context().browser().newContext(),p=await c.newPage(),rows=[],observations=[];
await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());await p.setViewportSize({width:1024,height:950});await p.goto(B+'/ru/admin/login/?next=/ru/admin/catalog/place/');await p.locator('[name=username]').fill(F.actors.admin);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>u.pathname.endsWith('/admin/catalog/place/')),p.locator('form button[type=submit]').click()]);
const g=async sel=>await p.locator(sel).evaluate(e=>{const r=e.getBoundingClientRect(),x=Math.max(0,Math.min(innerWidth-1,r.x+r.width/2)),y=Math.max(0,Math.min(innerHeight-1,r.y+r.height/2));return{left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height,viewport:{w:innerWidth,h:innerHeight},hit:e.contains(document.elementFromPoint(x,y)),ancestors:[...function*(x){while(x){yield x;x=x.parentElement;}}(e.parentElement)].slice(0,5).map(x=>({tag:x.tagName,cls:x.className,overflow:getComputedStyle(x).overflow,position:getComputedStyle(x).position}))};});
const before=await(await p.request.get(B+'/qa/state/')).json();
for(const model of ['event','specialist']){
 await p.goto(B+'/ru/admin/catalog/'+model+'/');await p.waitForLoadState('networkidle');
 await p.locator('#searchbar').fill('QA Queue 2');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('#searchbar').press('Enter')]);await p.waitForLoadState('networkidle');
 const matching=await p.locator('#result_list tbody tr').count();
 await p.locator('#km-sort-menu>summary').click();const link=p.locator('#km-sort-menu .km-sort-option').first();const href=await link.getAttribute('href');await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),link.click()]);await p.waitForLoadState('networkidle');
 rows.push({id:'native shared sort preserves valid search',status:new URL(p.url()).searchParams.get('q')==='QA Queue 2'&&await p.locator('#result_list tbody tr').count()===1?'PASS':'FAIL',model,matching_before:matching,sort_href:href,query_after:new URL(p.url()).search});
 await p.screenshot({path:H+'/screenshots/sort-current-recheck-'+model+'.png',fullPage:false,animations:'disabled'});
}
const after=await(await p.request.get(B+'/qa/state/')).json();observations.push({domain_unchanged:JSON.stringify(before)===JSON.stringify(after)});
await original.goto(B+'/ru/admin/login/');await c.close();return{rows,observations,mode:'Fresh actual current source after menu JS fix; existing Event/Specialist sort issue recheck only, no response/style injection or domain writes'};}
