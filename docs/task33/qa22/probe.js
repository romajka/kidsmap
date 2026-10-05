async (page)=>{
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
const rows=[];
for(const actor of ['public','author','owner','staff']){
 await page.request.get(origin+'/qa22/session/'+actor);
 for(const lang of ['az','ru','en'])for(const kind of ['place','activity','specialist','event']){
  const response=await page.goto(origin+fixtures.paths[lang][kind],{waitUntil:'networkidle'});
  const facts=await page.evaluate(()=>({edit:!!document.querySelector('[data-review-edit]'),reply:!!document.querySelector('form[action$="/reply/"]'),approve:!!document.querySelector('form[action$="/approve/"]')}));
  const issues=[];
  if(facts.edit!==(actor!=='public'))issues.push('actor edit form mismatch');
  if(facts.reply!==(actor==='owner'))issues.push('actor reply form mismatch');
  if(facts.approve!==(actor==='staff'))issues.push('actor approve form mismatch');
  rows.push({actor,lang,kind,status:response.status(),heading:await page.locator('h1').innerText(),facts,issues});
 }
}
return{rows,total:rows.length};
}
