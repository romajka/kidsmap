async original=>{
const output=[];
for(const c of original.context().browser().contexts())for(const p of c.pages()){
 const url=p.url();let forms=[];
 if(url.includes('sitefootersettings'))forms=await p.locator('form').evaluateAll(fs=>fs.map(f=>({id:f.id,action:f.action,buttons:[...f.querySelectorAll('button[type=submit],input[type=submit]')].map(b=>({tag:b.tagName,name:b.name,visible:!!b.getClientRects().length,text:b.textContent}))})));
 output.push({url,forms});
}
return{output};
}
