async page=>{
const O='/mnt/c/kidsmap/docs/qa/social-qa11-recheck-2026-10-18-pc-r1';
const rows=[],errors=[],network=[],blocked=[],pages=[page,await page.context().newPage()];
await page.context().route('**/*',r=>{let u=new URL(r.request().url());if(u.hostname==='127.0.0.1')return r.continue();blocked.push(u.hostname);return r.abort();});
for(let i=0;i<2;i++){pages[i].on('pageerror',e=>errors.push({side:i,error:String(e)}));pages[i].on('response',r=>{if(r.status()>=400)network.push({side:i,path:new URL(r.url()).pathname,status:r.status()});});await pages[i].goto('http://127.0.0.1:'+(33410+i)+'/qa/social11-login/');}
const cases=[...['place','activity','specialist','event'].map(kind=>({name:kind,path:'/reviews/'+kind+'/target/1/',selector:'.typed-reviews'})),{name:'inbox',path:'/account/notifications/?tab=all',selector:'#main-content'}];
for(const lang of ['az','ru','en'])for(const width of [360,390,768,1024,1280,1440])for(const c of cases){
 const pair=[];
 for(let i=0;i<2;i++){
  const p=pages[i];await p.setViewportSize({width,height:950});const response=await p.goto('http://127.0.0.1:'+(33410+i)+(lang==='az'?'':'/'+lang)+c.path);await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(70);
  const state=await p.locator(c.selector).evaluate(root=>{
   const props=['display','marginTop','flex','position','zIndex','width','paddingTop','paddingBottom','gap'];const style=getComputedStyle(root);const rect=e=>{let r=e.getBoundingClientRect();return [r.x,r.y,r.width,r.height];};
   return {tag:root.tagName,mainCount:document.querySelectorAll('main').length,nested:document.querySelectorAll('main main').length,mainRoles:document.querySelectorAll('main,[role=main]').length,style:Object.fromEntries(props.map(k=>[k,style[k]])),boxes:[root,...root.querySelectorAll('h1,h2,section,article,form,input,textarea,select,button')].slice(0,100).map(rect),controls:[...root.querySelectorAll('a,button,input,textarea,select')].map(e=>[e.tagName,e.getAttribute('name'),e.getAttribute('type'),e.getAttribute('href')]),h1:root.querySelector('h1')?.textContent.trim(),livingMapScript:[...document.scripts].some(e=>e.src.includes('living_map_background')),horizontalOverflow:document.documentElement.scrollWidth>innerWidth+1};
  });
  const first=p.locator(c.selector).locator('a[href],button:not([disabled]),input:not([type=hidden]):not([disabled]),textarea,select').first();let keyboard=null;
  if(await first.count()){await first.focus();let focused=await first.evaluate(e=>document.activeElement===e);await p.keyboard.press('Tab');await p.keyboard.press('Shift+Tab');keyboard={focused,returned:await first.evaluate(e=>document.activeElement===e)};}
  state.keyboard=keyboard;state.status=response.status();pair.push(state);
  if(width===390)await p.screenshot({path:O+'/png/'+lang+'-'+c.name+'-'+(i?'candidate':'baseline')+'.png',fullPage:true,animations:'disabled'});
 }
 const [a,b]=pair;const geometry=a.boxes.length===b.boxes.length&&a.boxes.every((r,j)=>r.every((v,k)=>Math.abs(v-b.boxes[j][k])<=1));
 const checks={http200:a.status===200&&b.status===200,baseline_nested:a.mainCount===2&&a.nested===1,candidate_single_main:b.mainCount===1&&b.nested===0&&b.mainRoles===1,styles_preserved:JSON.stringify(a.style)===JSON.stringify(b.style),geometry_preserved:geometry,controls_preserved:JSON.stringify(a.controls)===JSON.stringify(b.controls),heading_preserved:a.h1===b.h1,keyboard_preserved:JSON.stringify(a.keyboard)===JSON.stringify(b.keyboard)&&(!b.keyboard||b.keyboard.focused&&b.keyboard.returned),no_horizontal_overflow:!a.horizontalOverflow&&!b.horizontalOverflow,no_living_map_script:!a.livingMapScript&&!b.livingMapScript};
 rows.push({lang,width,case:c.name,checks,baseline:a,candidate:b});
}
return {rows,errors,network,blocked};
}
