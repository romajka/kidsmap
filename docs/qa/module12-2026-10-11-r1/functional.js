async original=>{
__QA12_COMMON__
const actions=[];async function state(c){return (await c.request.get(B+'/qa/state/')).json();}
function count(s,id=1,type='place_view'){return s.events.filter(x=>x.subject_id===id&&x.event_type===type).reduce((a,x)=>a+x.total,0);}
async function act(c,p,name,action,expect={},role='guest'){
 const before=await state(c),result=await action(),after=await state(c);
 const delta={raw:count(after)-count(before),views:after.metrics['1'].views-before.metrics['1'].views,unique:after.metrics['1'].unique_visitors-before.metrics['1'].unique_visitors,contacts:after.metrics['1'].contact_actions-before.metrics['1'].contact_actions};
 actions.push({name,role,before,after,delta,result});const ok=Object.entries(expect).every(([k,v])=>delta[k]===v);
 add(name,ok,{delta,expected:expect,result},role,'ru',1440,p.url());return{before,after,delta,result};
}
const contexts={};for(const role of ['guest','outsider','owner','staff']){const q=await context(role);contexts[role]=q;await act(q.c,q.p,'card-first-'+role,()=>visit(q.p,F.urls.ru.place),{raw:1,views:role==='staff'?0:1},role);}
const{c,p}=contexts.guest;
await act(c,p,'reload',async()=>{const r=await p.reload();return r.status();},{raw:1,views:1,unique:0});
await act(c,p,'back',async()=>{await p.goto(B+'/ru/about/');const r=await p.goBack();return r?.status()??null;},{raw:1,views:1,unique:0});
await act(c,p,'forward',async()=>{await p.goForward();const r=await p.goBack();return r?.status()??null;},{raw:1,views:1,unique:0});
await act(c,p,'two-tabs',async()=>{const tab=await c.newPage();const s=await visit(tab,F.urls.ru.place);await tab.close();return s;},{raw:1,views:1,unique:0});
for(const lang of ['az','en','ru'])await act(c,p,'language-'+lang,()=>visit(p,F.urls[lang].place),{raw:1,views:1,unique:0});
await act(c,p,'query-redirect',()=>visit(p,F.urls.ru.place+'?unwanted=fictional'),{raw:1,views:1,unique:0});
const endpoint='/ru/events/track/';async function event(payload,headers={}){return p.evaluate(async({endpoint,payload,headers})=>{const r=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:typeof payload==='string'?payload:JSON.stringify(payload)});return{status:r.status,body:r.status===500?'server-error':await r.text()};},{endpoint,payload,headers});}
for(const type of ['phone_click','whatsapp_click','website_click','social_click','directions_click']){
 const before=await state(c),result=await event({event_type:type,place_id:1,path:F.urls.ru.place,source:'place-detail'}),after=await state(c);actions.push({name:'endpoint-'+type,before,after,result});add('endpoint-'+type,result.status===200&&count(after,1,type)-count(before,1,type)===1,{result,delta:count(after,1,type)-count(before,1,type)});
}
const repeated=await act(c,p,'repeat-click-request',()=>event({event_type:'phone_click',place_id:1,source:'phone-reveal'}),{contacts:1});
const cases=[['invalid-json','{',400],['array',[],400],['unsupported',{event_type:'unknown',place_id:1},400],['missing-id',{event_type:'phone_click'},400],['inactive-id',{event_type:'phone_click',place_id:F.places.inactive},400],['deleted-id',{event_type:'phone_click',place_id:F.places.deleted},400],['unknown-id',{event_type:'phone_click',place_id:999999},400],['private-draft-id',{event_type:'phone_click',place_id:F.places.draft},400],['private-archived-id',{event_type:'phone_click',place_id:F.places.archived},400]];
for(const[name,payload,status]of cases){const before=await state(c),result=await event(payload),after=await state(c);actions.push({name,before,after,result});add(name,result.status===status&&after.event_count===before.event_count,{result,expectedStatus:status,eventDelta:after.event_count-before.event_count});}
const beforeFailure=await state(c),failure=await event({event_type:'phone_click',place_id:1},{'X-QA-Failure':'event-store'}),afterFailure=await state(c);actions.push({name:'backend-failure',before:beforeFailure,after:afterFailure,result:failure});add('backend-failure',failure.status===500&&beforeFailure.event_count===afterFailure.event_count,{result:failure,SIMULATED:true});
const networkBefore=await state(c);await p.route('**/events/track/',r=>r.abort('failed'));const network=await event({event_type:'phone_click',place_id:1}).catch(e=>String(e).split('\n')[0]);await p.unroute('**/events/track/');const networkAfter=await state(c);actions.push({name:'network-failure',before:networkBefore,after:networkAfter,result:network});add('network-failure',networkAfter.event_count===networkBefore.event_count,{SIMULATED:true,eventDelta:networkAfter.event_count-networkBefore.event_count});
await shot(p,'public-ru-1440-functional');
for(const role of ['outsider','owner','staff']){const q=contexts[role];const st=await visit(q.p,'/ru/account/places/1/analytics/');add('owner-analytics-acl-'+role,st===(role==='owner'?200:404),{http:st,body:(await q.p.locator('body').innerText()).slice(-300)},role);await shot(q.p,'analytics-acl-'+role+'-1440');}
const admin=await context('admin');for(const role of ['staff','admin']){const q=role==='staff'?contexts.staff:admin;const st=await visit(q.p,'/admin/catalog/siteanalytics/?period=90');add('admin-analytics-acl-'+role,st===(role==='admin'?200:403),{http:st,kpi:await q.p.locator('[data-kpi-value]').allTextContents()},role);await shot(q.p,'admin-analytics-'+role+'-1440');}
const disabled=await context('guest');await disabled.p.goto('http://localhost:8830'+F.urls.ru.place);const db=await state(disabled.c);const disabledResult=await disabled.p.evaluate(async()=>{const r=await fetch('/ru/events/track/',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({event_type:'phone_click',place_id:1})});return r.status;});const da=await state(disabled.c);actions.push({name:'disabled',before:db,after:da,result:disabledResult});add('disabled-collection',disabledResult===200&&db.event_count===da.event_count,{status:disabledResult,eventDelta:da.event_count-db.event_count});
const version=await(await c.request.get(B+'/qa/version/')).json();for(const q of [...Object.values(contexts),admin,disabled])await q.c.close();return{rows,actions,version};
}
