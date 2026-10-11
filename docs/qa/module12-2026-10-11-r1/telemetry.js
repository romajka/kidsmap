async original=>{
__QA12_COMMON__
const telemetry=[],actions=[];
for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440])for(const role of ['guest','owner','admin']){
 const{c,p}=await context(role,lang,width),errors=[],responses=[],external=[];
 p.on('pageerror',e=>errors.push(String(e)));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('response',r=>{if(new URL(r.url()).hostname==='localhost'&&r.status()>=400)responses.push({status:r.status(),url:r.url()});});p.on('requestfailed',r=>{if(new URL(r.url()).hostname!=='localhost')external.push(new URL(r.url()).hostname);});
 const before=await(await c.request.get(B+'/qa/state/')).json(),url=role==='guest'?F.urls[lang].place:role==='owner'?prefix(lang)+'/account/places/1/analytics/':'/admin/catalog/siteanalytics/?qa_ga=filled';const st=await visit(p,url);await p.waitForTimeout(150);const after=await(await c.request.get(B+'/qa/state/')).json();actions.push({name:'telemetry-'+role+'-'+lang+'-'+width,before,after});const localErrors=errors.filter(x=>!x.includes('ERR_FAILED')&&!x.includes('net::ERR_ABORTED'));add('console-network',st===200&&responses.length===0&&localErrors.length===0,{http:st,localErrors,localErrorResponses:responses,blockedExternal:[...new Set(external)],external:'SIMULATED blocked transport',viewDelta:after.metrics['1'].views-before.metrics['1'].views},role,lang,width,p.url());
 if(role==='guest'&&(width===390||width===1440)){const reveal=p.locator('[data-phone-reveal="1"]').first();if(await reveal.count()){await reveal.click();await p.waitForTimeout(250);const g=await geometry(p),s=await shot(p,'phone-dialog-'+lang+'-'+width);add('phone-dialog-geometry',g.document<=width+1,{geometry:g},role,lang,width,p.url(),s);await p.keyboard.press('Escape');}}
 telemetry.push({role,lang,width,errors,responses,blockedExternal:[...new Set(external)]});await c.close();
}
return{rows,telemetry,actions};
}
