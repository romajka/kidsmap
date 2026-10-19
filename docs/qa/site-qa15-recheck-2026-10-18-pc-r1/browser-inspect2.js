async original=>{
let output=[];
for(const c of original.context().browser().contexts())for(const p of c.pages())if(p.url().includes('sitefootersettings')) {
 output.push(await p.locator('button,a[role=button],input[type=submit]').evaluateAll(es=>es.filter(e=>e.getClientRects().length).map(e=>({tag:e.tagName,name:e.name,id:e.id,class:e.className,text:e.textContent?.trim().slice(0,90),data:{...e.dataset}}))));
 await p.screenshot({path:'/mnt/c/kidsmap/docs/qa/site-qa15-recheck-2026-10-18-pc-r1/png/harness-mobile-controls.png',animations:'disabled'});
 break;
}
return{output};
}
