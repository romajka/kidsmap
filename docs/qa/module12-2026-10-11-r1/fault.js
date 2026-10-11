async original=>{
__QA12_COMMON__
for(const width of [390,1440]){
 const{c,p}=await context('guest','ru',width);await c.setExtraHTTPHeaders({'X-QA-Failure':'event-store'});const before=await(await c.request.get(B+'/qa/state/')).json();const st=await visit(p,F.urls.ru.place),after=await(await c.request.get(B+'/qa/state/')).json();const s=await shot(p,'public-analytics-backend-failure-ru-'+width);add('analytics-fault-public-availability',st===200,{actualStatus:st,expectedStatus:200,eventDelta:after.event_count-before.event_count,before:before.metrics['1'],after:after.metrics['1'],SIMULATED:true},'guest','ru',width,p.url(),s);await c.close();
}
return{rows};
}
