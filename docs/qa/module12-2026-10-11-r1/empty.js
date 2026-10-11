async original=>{
__QA12_COMMON__
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){const{c,p}=await context('owner',lang,width);const before=await(await c.request.get(B+'/qa/state/')).json();const st=await visit(p,prefix(lang)+'/account/places/6/analytics/'),vals=(await p.locator('.owner-analytics__grid article strong').allTextContents()).map(x=>x.trim()),after=await(await c.request.get(B+'/qa/state/')).json(),s=await shot(p,'owner-zero-'+lang+'-'+width);add('owner-zero-data',st===200&&vals.length===5&&vals.every(x=>x==='0')&&before.event_count===after.event_count,{http:st,values:vals,db:after.metrics['6']},'owner',lang,width,p.url(),s);await c.close();}return{rows};
}
