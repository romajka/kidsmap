async original=>{
 const B='http://127.0.0.1:46131',H='/home/ramin/kidsmap/docs/qa/social-qa01-recheck-2026-10-16-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json();
 const rows=[],diagnostics=[],states={},contexts=[];let kind='';
 const add=(id,ok,extra={})=>rows.push({id,kind,language:'ru',width:390,status:ok?'PASS':'FAIL',...extra});
 async function actor(role){
  const c=await original.context().browser().newContext({viewport:{width:390,height:950}});contexts.push(c);
  await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
  const p=await c.newPage();p.on('pageerror',e=>diagnostics.push({type:'pageerror',role,text:String(e).split('\n')[0]}));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)diagnostics.push({type:'http',role,status:r.status(),path:new URL(r.url()).pathname});});p.on('requestfailed',r=>diagnostics.push({type:'requestfailed',role,local:r.url().startsWith(B+'/'),host:new URL(r.url()).host,error:r.failure()?.errorText}));p.on('console',m=>{if(m.type()==='error')diagnostics.push({type:'console',role,local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]')});});
  await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.actors[role].username);await p.locator('[name=password]').fill(F.password);
  await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/'),{waitUntil:'domcontentloaded'}),p.locator('form.auth-form button[type=submit]').click()]);return p;
 }
 try{
 const p=await actor('author'),m=await actor('moderator');
 for(kind of ['place','specialist','activity','event']){
  const url=B+'/ru/reviews/'+kind+'/target/'+F.targets[kind]+'/';await p.goto(url);await p.locator('[data-review-edit]').waitFor();
  add('new review starts with empty required rating',await p.locator('#review-rating').inputValue()===''&&await p.locator('#review-rating').getAttribute('required')!==null);
  await p.locator('#review-rating').selectOption('4');const text='Fictional SOCIAL01 '+kind+' <script>window.SOCIAL01_XSS=1</script> & <b>literal</b>';
  await p.locator('#review-text').fill(text);await p.locator('[data-review-edit] button').focus();
  await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.keyboard.press('Enter')]);await p.locator('[data-candidate-status]').waitFor();await p.reload();
  const s=await(await p.request.get(B+'/qa/state/')).json();states[kind+'-pending']=s;
  const head=s.reviews[kind].heads[0],value=await p.locator('#review-rating').inputValue();
  add('native submit persists pending rating4',head.candidate_rating===4&&head.current_id===null&&s.reviews[kind].summary.count===0,{db_rating:head.candidate_rating});
  add('pending saved rating restored after reload',value==='4',{actual:value,expected:'4'});
  add('pending text retained and HTML does not execute',await p.locator('#review-text').inputValue()===text&&await p.evaluate(()=>window.SOCIAL01_XSS===undefined));
  await p.locator('[data-review-edit]').scrollIntoViewIfNeeded();await p.screenshot({path:H+'/screenshots/pending-'+kind+'-ru-390.png'});
  await m.goto(url);await m.locator('[data-candidate-id] form[action$="/approve/"]').waitFor();
  await Promise.all([m.waitForNavigation({waitUntil:'domcontentloaded'}),m.locator('[data-candidate-id] form[action$="/approve/"] button').click()]);
  await p.reload();const approved=await(await p.request.get(B+'/qa/state/')).json();states[kind+'-approved']=approved;
  const h=approved.reviews[kind].heads[0],av=await p.locator('#review-rating').inputValue();
  add('native moderation publishes rating4 once',h.current_id!==null&&h.candidate_id===null&&h.rating===4&&approved.reviews[kind].summary.count===1&&approved.reviews[kind].summary.average===4);
  add('approved saved rating restored after reload',av==='4',{actual:av,expected:'4'});
  add('public text escaped and editor text retained',await p.locator('#review-text').inputValue()===text&&await p.locator('.review-item blockquote').innerText()===text&&await p.evaluate(()=>window.SOCIAL01_XSS===undefined));
  await p.locator('[data-review-edit]').scrollIntoViewIfNeeded();await p.screenshot({path:H+'/screenshots/approved-'+kind+'-ru-390.png'});
 }
 return{complete:true,rows,states,diagnostics,browser_version:original.context().browser().version(),scope:'SOCIAL-QA-01 only; native create/reload/approve/reload, four types, RU390. Application unchanged.'};
 }catch(e){return{complete:false,error:String(e),rows,states,diagnostics};}finally{for(const c of contexts)await c.close();}
}
