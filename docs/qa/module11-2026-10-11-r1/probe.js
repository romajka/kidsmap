async original=>{
 __QA11_COMMON__
 const {c,p}=await context('admin','ru');await visit(p,F.urls.ru.place);const snap=await p.locator('body').ariaSnapshot();const h=await head(p);const ss=await shot(p,'probe-place-ru-1440');
 await visit(p,'/admin/catalog/place/1/change/');const inputs=await p.locator('input,textarea,select,button').evaluateAll(es=>es.filter(e=>e.name&&e.type!=='hidden').map(e=>({name:e.name,type:e.type,value:e.type==='password'?'[omitted]':e.value,visible:!!e.getClientRects().length,text:e.tagName==='BUTTON'?e.textContent.trim():''})));const adminSnap=await p.locator('body').ariaSnapshot();await c.close();return{h,ss,snap:snap.slice(0,15000),adminSnap:adminSnap.slice(0,8000),inputs};
}
