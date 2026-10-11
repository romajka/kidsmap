async (page) => {
 const B='http://localhost:8817';const c=await page.context().browser().newContext({viewport:{width:390,height:950}});
 await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 const p=await c.newPage();let out=[];
 for(const path of ['/ru/','/ru/catalog/?q=Aurora','/ru/organizations/','/ru/specialists/','/ru/events/']){
  const res=await p.goto(B+path);await p.waitForTimeout(450);
  out.push({path,status:res.status(),title:await p.title(),text:(await p.locator('main').first().innerText()).slice(0,2000),buttons:await p.locator('main button').evaluateAll(x=>x.filter(e=>e.getBoundingClientRect().height).map(e=>({text:e.innerText,attrs:[...e.attributes].filter(a=>a.name.startsWith('data-')).map(a=>[a.name,a.value])})).slice(0,25)),fields:await p.locator('main input,main select').evaluateAll(x=>x.map(e=>({tag:e.tagName,type:e.type,name:e.name,id:e.id}))) });
 }
 await p.goto(B+'/ru/catalog/?q=Aurora');out.push({map:JSON.parse(await p.locator('#catalog-map-data').textContent()),links:await p.locator('main a').evaluateAll(x=>x.map(e=>({text:e.innerText.slice(0,60),href:e.getAttribute('href')})).filter(x=>x.href?.includes('place/')||x.href?.includes('page=')))});
 await p.screenshot({path:'C:/kidsmap/docs/qa/module06-2026-10-10-r1/screenshots/discover-catalog-ru-390.png',fullPage:true});await c.close();return out;
}
