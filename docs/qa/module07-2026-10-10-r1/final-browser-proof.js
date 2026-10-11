async original=>{
 const B='http://localhost:8820',D='C:/kidsmap/docs/qa/module07-2026-10-10-r1/screenshots/',F=__FIXTURES_JSON__,rows=[];
 for(const lang of ['ru','az','en']){
  const pre=lang==='az'?'/':'/'+lang+'/';
  for(const role of ['anonymous','author','reviewer','admin']){
   const c=await original.context().browser().newContext({viewport:{width:1440,height:950}}),p=await c.newPage();await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());p.setDefaultTimeout(11000);const add=(id,ok,x={})=>rows.push({id,status:ok?'PASS':'FAIL',role,lang,width:'N/A HTTP',...x});
   try{
    if(role!=='anonymous'){await p.goto(B+pre+'auth/login/');await p.locator('[name=username]').fill(F.actors[role].email);await p.locator('[name=password]').fill('__LOCAL_PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/')),p.locator('.auth-form button[type=submit]:visible').click()]);}
    for(const [key,d] of Object.entries(F.documents)){const response=await p.request.get(B+pre+'specialists/documents/'+d.id+'/download/',{maxRedirects:0}),allowed=['reviewer','admin'].includes(role);add('post-deletion-download-'+key,response.status()===(allowed?200:404),{entity:key,http:response.status(),headers:allowed?{cache:response.headers()['cache-control'],nosniff:response.headers()['x-content-type-options']}:undefined});const direct=await p.request.get(B+'/media/'+d.path);add('post-deletion-private-media-'+key,direct.status()===404,{http:direct.status()});}
    if(role==='admin'){const response=await p.goto(B+pre+'admin/catalog/place/'+F.places.owner+'/change/');add('administrator-canonical-editor-allowed',response.status()===200,{width:1440,url:p.url(),screenshot:'administrator-editor-'+lang+'-1440.png'});await p.screenshot({path:D+'administrator-editor-'+lang+'-1440.png',fullPage:true});}
    if(role==='anonymous')for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});await p.goto(B+pre+'specialists/fictional-qa07-person/');const downloads=await p.locator('a[href*="/documents/"]').count(),g=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));add('post-person-deletion-public-certificate-absent',downloads===0,{width,geometry:g,screenshot:'post-deletion-public-person-'+lang+'-'+width+'.png'});await p.screenshot({path:D+'post-deletion-public-person-'+lang+'-'+width+'.png',fullPage:true});}
   }catch(e){rows.push({id:'final-browser-harness-error',status:'NOT RUN',role,lang,width:1440,error:String(e)});}await c.close();
  }
 }return{rows};
}
