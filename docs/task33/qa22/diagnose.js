async(page)=>{
const origin='http://127.0.0.1:8782';
await page.context().unroute('**/*');
await page.context().route('**/*',async route=>{
 const url=new URL(route.request().url());
 if(url.origin===origin)return route.continue();
 if(url.hostname==='kidsmap.az')return route.fulfill({response:await route.fetch({url:origin+url.pathname+url.search})});
 if(url.hostname==='fonts.googleapis.com')return route.fulfill({response:await route.fetch({url:origin+'/qa-font.css'})});
 return route.fulfill({status:200,contentType:'application/javascript',body:''});
});
const fixtures=await(await page.request.get(origin+'/qa22/fixtures')).json();
await page.request.get(origin+'/qa22/session/staff?lang=ru');
await page.setViewportSize({width:390,height:900});
const response=await page.goto(origin+fixtures.paths.ru.admin.place,{waitUntil:'networkidle'});
const facts=await page.evaluate(()=>({url:location.pathname,lang:document.documentElement.lang,viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('body *')].filter(node=>{const r=node.getBoundingClientRect();return r.right>innerWidth+1&&r.width>0}).map(node=>{const r=node.getBoundingClientRect(),s=getComputedStyle(node);return{tag:node.tagName,id:node.id,classes:node.className,width:r.width,left:r.left,right:r.right,minWidth:s.minWidth,display:s.display,columns:s.gridTemplateColumns,whiteSpace:s.whiteSpace,overflowX:s.overflowX}}).slice(0,60)}));
await page.screenshot({path:'__QA22_EVIDENCE__/admin-place-ru-390-diagnose.png',fullPage:true});
return{status:response.status(),...facts};
}
