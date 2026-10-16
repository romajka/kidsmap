async original=>{
 const B='http://127.0.0.1:34133',F=(await(await original.request.get(B+'/qa/fixtures/')).json()),rows=[],diag=[];
 const PASSWORD=(await(await original.request.get(B+'/qa/fixtures/')).json()).password;
 for(const lang of ['ru'])for(const role of ['anonymous','author','person','owner','network','employee','outsider','moderator','reviewer','staff']){
  const prefix=lang==='az'?'/':'/'+lang+'/',c=await original.context().browser().newContext(),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(9000);
  const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width:'N/A HTTP',...x});
  try{
   await p.goto(B+prefix+'auth/login/');if(role!=='anonymous'){await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill(PASSWORD);await Promise.all([p.waitForURL(u=>u.pathname.includes('/account/')),p.locator('.auth-form button[type=submit]:visible').click()]);}
   const before=await (await p.request.get(B+'/qa/state/')).json();
   for(const [key,d] of Object.entries(F.documents)){
    const url=prefix+'specialists/documents/'+d.id+'/download/',r=await p.request.get(B+url),allowed=key==='public_certificate'||role==='reviewer'||role==='admin'||(role==='person'&&key!=='other_identity')||(role==='outsider'&&key==='other_identity');
    add('document-'+key,r.status()===(allowed?200:404),{url,http:r.status(),expected:allowed?200:404,headers:allowed?{cache:r.headers()['cache-control'],disposition:r.headers()['content-disposition'],nosniff:r.headers()['x-content-type-options']}:undefined});
    if(allowed)add('document-private-response-headers',r.headers()['cache-control']==='private, no-store'&&r.headers()['x-content-type-options']==='nosniff'&&r.headers()['content-disposition']?.includes('attachment'),{entity:key,url});
    const media=await p.request.get(B+'/media/'+d.path);add('direct-private-media-denied',media.status()===404,{entity:key,http:media.status(),url:'/media/'+d.path});
   }
   const legacy=await p.request.get(B+'/media/protected_docs/specialists/qa07-legacy.txt');add('legacy-media-denied',legacy.status()===404,{http:legacy.status()});
   for(const label of ['owner','other','author','volunteer','volunteer_b','branch']){
    const pid=F.places[label],url=prefix+'account/places/'+pid+'/edit/',r=await p.request.get(B+url,{maxRedirects:0}),allowed=role==='admin'||(label==='owner'&&['owner','employee'].includes(role))||(label==='other'&&role==='outsider')||(label==='author'&&role==='author')||(label==='branch'&&['network','employee'].includes(role));
    const denied=[302,403,404].includes(r.status());add('place-edit-ACL',allowed?r.status()===200:denied,{entity:label,url,http:r.status(),expected:allowed?'200':'denied'});
   }
   for(const label of ['owner','other']){
    if(role==='admin'||(label==='owner'&&role==='owner')||(label==='other'&&role==='outsider'))continue;
    const url=prefix+'account/business/team/place/'+F.places[label]+'/invite/',csrf=(await c.cookies()).find(x=>x.name==='module07fullr1_csrf')?.value;
    const r=await p.request.post(B+url,{headers:{'X-CSRFToken':csrf||'','Content-Type':'application/json'},data:{email:'ungranted07@example.invalid',role:'EDITOR',actions:['place.view','place.edit']}});add('foreign-place-team-mutation-denied',r.status()===403,{url,http:r.status()});
   }
   if(!['admin','network'].includes(role)){
    const url=prefix+'account/business/team/organization/'+F.organization+'/invite/',csrf=(await c.cookies()).find(x=>x.name==='module07fullr1_csrf')?.value,r=await p.request.post(B+url,{headers:{'X-CSRFToken':csrf||'','Content-Type':'application/json'},data:{email:'ungrantedorg07@example.invalid',role:'EDITOR',scope:'all_network',place_ids:[]}});add('foreign-organization-team-denied',r.status()===403,{url,http:r.status()});
   }
   const after=await (await p.request.get(B+'/qa/state/')).json();add('denials-no-domain-side-effects',JSON.stringify(before)===JSON.stringify(after),{tracked:['users','verified','members','invitations','org_grants','org_invitations','places','documents','deletions']});
  }catch(e){rows.push({id:'acl-harness-error',status:'NOT RUN',role,lang,width:'N/A HTTP',error:String(e)});}
  await c.close();
 }
 return{rows,diagnostics:diag};
}
