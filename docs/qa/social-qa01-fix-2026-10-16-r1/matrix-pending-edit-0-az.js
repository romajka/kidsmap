async original=>{
const B='http://127.0.0.1:33741',H='/home/ramin/kidsmap/docs/qa/social-qa01-fix-2026-10-16-r1',PHASE='matrix-pending-edit',CASE=0,LANG='az';
const F=await(await original.request.get(B+'/qa/fixtures/')).json(),rows=[],diagnostics=[],states=[],contexts=[],KINDS=['place','specialist','activity','event'];let kind='',language=LANG,width=390,scenario=PHASE;
const add=(id,ok,extra={})=>rows.push({id,phase:PHASE,case:CASE,kind,language,width,status:ok?'PASS':'FAIL',...extra});
const prefix=lang=>lang==='az'?'/':'/'+lang+'/';
const url=(f,k,lang=language)=>B+prefix(lang)+'reviews/'+k+'/target/'+f.targets[k]+'/';
async function read(f){return await(await original.request.get(B+'/qa/state/'+f.id+'/')).json();}
const head=(s,k,u)=>s.reviews[k].heads.find(h=>h.author_id===u.id);
function copy(role,f,k,stage){return 'Fictional SOCIAL01 '+f.id+' '+role+' '+k+' '+stage+' <script>window.SOCIAL01_XSS=1</script> & <b>literal</b>'+' LongWord'.repeat(8);}
async function actor(user,lang=language,w=width){
 const c=await original.context().browser().newContext({viewport:{width:w,height:950}});contexts.push(c);
 await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());
 const p=await c.newPage();p.on('pageerror',e=>diagnostics.push({type:'pageerror',text:String(e).split('\n')[0]}));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)diagnostics.push({type:'http',status:r.status(),path:new URL(r.url()).pathname});});p.on('requestfailed',r=>diagnostics.push({type:'requestfailed',local:r.url().startsWith(B+'/'),host:new URL(r.url()).host,error:r.failure()?.errorText}));p.on('console',m=>{if(m.type()==='error')diagnostics.push({type:'console',local:m.location().url.startsWith(B+'/'),text:m.text().replace(/https?:\S+/g,'[URL]')});});
 if(user){await p.goto(B+prefix(lang)+'auth/login/');await p.locator('[name=username]').fill(user.username);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/'),{waitUntil:'domcontentloaded'}),p.locator('form.register-form--login button[type=submit]').click()]);}
 return p;
}
async function shot(p,name){await p.locator('[data-review-edit]').scrollIntoViewIfNeeded();await p.screenshot({path:H+'/screenshots/'+name+'.png'});}
async function submit(p){await p.locator('[data-review-edit] button').focus();await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.keyboard.press('Enter')]);await p.locator('[data-review-edit]').waitFor();}
async function decision(m,f,k,approve){await m.goto(url(f,k));let selector='[data-candidate-id] form[action$="/'+(approve?'approve':'reject')+'/"]';const target=m.locator(selector).filter({has:m.locator('input[name=revision_id][value="'+head(await read(f),k,f.actors.author)?.candidate_id+'"]')});
 // When a first-rejected account is selected, caller supplies its exact candidate ID.
 return selector;
}
async function decide(m,f,k,id,approve){await m.goto(url(f,k));const article=m.locator('[data-candidate-id="'+id+'"]'),form=article.locator('form[action$="/'+(approve?'approve':'reject')+'/"]');if(!approve)await form.locator('[name=reason]').fill('Fictional rejection for rating readback');await Promise.all([m.waitForNavigation({waitUntil:'domcontentloaded'}),form.locator('button').click()]);}
try{
if(PHASE==='create'){
 const f=F.cases[CASE];language=f.lang;width=f.width;
 for(const role of ['author','repeat']){
  const p=await actor(f.actors[role]);
  for(kind of KINDS){await p.goto(url(f,kind));const existing=head(await read(f),kind,f.actors[role]);if(existing){add('resumed persisted pending rating4 text and token',existing.candidate_rating===4&&await p.locator('#review-rating').inputValue()==='4'&&await p.locator('#review-text').inputValue()===copy(role,f,kind,'initial')&&await p.locator('[name=expected_revision_id]').inputValue()===String(existing.candidate_id));if(role==='author')await shot(p,'native-pending-'+CASE+'-'+kind);continue;}add('new editor has empty required rating',await p.locator('#review-rating').inputValue()===''&&await p.locator('#review-rating').getAttribute('required')!==null);
   await p.locator('#review-rating').focus();await p.keyboard.press('4');await p.keyboard.press('Enter');if(await p.locator('#review-rating').inputValue()!=='4')await p.locator('#review-rating').selectOption('4');
   await p.locator('#review-text').fill(copy(role,f,kind,'initial'));await submit(p);await p.reload();const s=await read(f),h=head(s,kind,f.actors[role]);states.push({stage:role+'-pending',kind,state:s});
   add('native create and reload restore rating4 text and revision token',await p.locator('#review-rating').inputValue()==='4'&&await p.locator('#review-text').inputValue()===copy(role,f,kind,'initial')&&await p.locator('[name=expected_revision_id]').inputValue()===String(h.candidate_id)&&h.candidate_rating===4&&h.current_id===null);
   add('pending candidate does not affect public rating count',s.reviews[kind].summary.count===0);
   if(role==='author')await shot(p,'native-pending-'+CASE+'-'+kind);
  }
 }
}
else if(PHASE==='approve'){
 const f=F.cases[CASE];language=f.lang;width=f.width;const m=await actor(F.actors.moderator),p=await actor(f.actors.author);
 for(kind of KINDS){const s=await read(f),h=head(s,kind,f.actors.author);await decide(m,f,kind,h.candidate_id,true);await p.goto(url(f,kind));await p.reload();const a=await read(f),after=head(a,kind,f.actors.author);states.push({stage:'approved',kind,state:a});
  add('native approval and reload restore current rating4 and token',after.candidate_id===null&&after.rating===4&&await p.locator('#review-rating').inputValue()==='4'&&await p.locator('[name=expected_revision_id]').inputValue()===String(after.current_id));
  add('published count1 average4 and escaped text',a.reviews[kind].summary.count===1&&a.reviews[kind].summary.average===4&&await p.locator('.review-item blockquote').first().innerText()===copy('author',f,kind,'initial')&&await p.evaluate(()=>window.SOCIAL01_XSS===undefined));
 }
}
else if(PHASE==='edit-repeat'){
 const f=F.cases[CASE];language=f.lang;width=f.width;const p=await actor(f.actors.author),repeat=await actor(f.actors.repeat);
 for(kind of KINDS){
  for(const [role,actorPage,rating,stage]of[['author',p,2,'candidate-two'],['repeat',repeat,4,'initial']]){
   const before=await read(f),h=head(before,kind,f.actors[role]);const latest=h.revisions.at(-1);if(kind!=='specialist'&&Date.now()-Date.parse(latest.created_at)<121000)throw Error('Real cooldown has not elapsed; defer this phase');
   await actorPage.goto(url(f,kind));if(role==='author'){await actorPage.locator('#review-rating').selectOption('2');await actorPage.locator('#review-text').fill(copy(role,f,kind,stage));}else add('reload retains4 without selecting again before native resubmit',await actorPage.locator('#review-rating').inputValue()==='4');
   await submit(actorPage);await actorPage.reload();const s=await read(f),after=head(s,kind,f.actors[role]);states.push({stage:role+'-edit',kind,state:s});
   add('native '+role+' submit/reload preserves selected rating and advances candidate',after.candidate_rating===rating&&after.candidate_id!==h.candidate_id&&await actorPage.locator('#review-rating').inputValue()===String(rating)&&await actorPage.locator('#review-text').inputValue()===copy(role,f,kind,stage));
   add('candidate edit keeps public rating4 count1',s.reviews[kind].summary.count===1&&s.reviews[kind].summary.average===4&&(role==='repeat'||after.rating===4));
  }
 }
}
else if(PHASE==='reject-edit'){
 const f=F.cases[CASE];language=f.lang;width=f.width;const m=await actor(F.actors.moderator),p=await actor(f.actors.author);
 for(kind of KINDS){const before=head(await read(f),kind,f.actors.author);await decide(m,f,kind,before.candidate_id,false);await p.goto(url(f,kind));await p.reload();const s=await read(f),h=head(s,kind,f.actors.author);states.push({stage:'rejected-edit',kind,state:s});
  add('native rejected edit restores current4 text and token',h.candidate_id===null&&h.current_id===before.current_id&&await p.locator('#review-rating').inputValue()==='4'&&await p.locator('#review-text').inputValue()===copy('author',f,kind,'initial')&&await p.locator('[name=expected_revision_id]').inputValue()===String(h.current_id));
  add('rejected2 remains history while public rating4 count1 remains',h.revisions.some(r=>r.status==='rejected'&&r.rating===2)&&s.reviews[kind].summary.average===4&&s.reviews[kind].summary.count===1);
 }
}
else if(PHASE==='reject-first'){
 const f=F.cases[CASE];language=f.lang;width=f.width;const m=await actor(F.actors.moderator),p=await actor(f.actors.rejected);
 for(kind of KINDS){await p.goto(url(f,kind));await p.locator('#review-rating').selectOption('3');await p.locator('#review-text').fill(copy('rejected',f,kind,'first'));await submit(p);const pending=head(await read(f),kind,f.actors.rejected);await decide(m,f,kind,pending.candidate_id,false);await p.reload();const s=await read(f),h=head(s,kind,f.actors.rejected);states.push({stage:'rejected-first',kind,state:s});
  add('first native rejection restores retained3 without current revision',h.current_id===null&&h.candidate_id===null&&h.rating===3&&await p.locator('#review-rating').inputValue()==='3'&&await p.locator('#review-text').inputValue()===copy('rejected',f,kind,'first')&&await p.locator('[name=expected_revision_id]').inputValue()==='');
  add('first rejected reviewer does not alter public rating count',s.reviews[kind].summary.count===1&&s.reviews[kind].summary.average===4);
 }
}
else if(PHASE==='keyboard-acl'){
 const f=F.cases[0];language=LANG;width=CASE===0?390:1440;const p=await actor(f.actors.author),outsider=await actor(F.actors.outsider),guest=await actor(null);
 for(kind of KINDS){await p.goto(url(f,kind));const before=await p.locator('#review-rating').inputValue();await p.locator('#review-rating').focus();await p.keyboard.press('ArrowDown');await p.keyboard.press('ArrowUp');await p.keyboard.press('Space');await p.keyboard.press('Escape');
  add('native ArrowDown Up Space Escape retain saved rating and select focus',await p.locator('#review-rating').inputValue()===before&&await p.locator('#review-rating').evaluate(e=>e===document.activeElement));
  await p.keyboard.press('Tab');await p.keyboard.press('Tab');add('keyboard reaches submit button',await p.locator('[data-review-edit] button').evaluate(e=>e===document.activeElement));
  await outsider.goto(url(f,kind));const outsiderText=await outsider.locator('main.typed-reviews').innerText();add('outsider editor empty and private candidates absent',await outsider.locator('#review-rating').inputValue()===''&&await outsider.locator('#review-text').inputValue()===''&&await outsider.locator('[name=expected_revision_id]').inputValue()===''&&!['candidate-two',' repeat '+kind+' ',' rejected '+kind+' '].some(t=>(outsiderText).includes(t)));
  await guest.goto(url(f,kind));const guestText=await guest.locator('main.typed-reviews').innerText();add('guest has public reviews without author editor or private candidate',await guest.locator('[data-review-edit]').count()===0&&!['candidate-two',' repeat '+kind+' ',' rejected '+kind+' '].some(t=>(guestText).includes(t))&&await guest.locator('.review-item').count()===1);
 }
}
else if(PHASE==='edges'){
 const f=F.cases[0];language='ru';width=390;kind='specialist';const p=await actor(f.actors.repeat),stale=await actor(f.actors.repeat);const u=url(f,kind);await p.goto(u);await stale.goto(u);const before=head(await read(f),kind,f.actors.repeat);
 await p.locator('#review-rating').selectOption('5');await p.locator('#review-text').fill(copy('repeat',f,kind,'conflict-five'));await submit(p);const fresh=head(await read(f),kind,f.actors.repeat);
 add('first tab persists candidate5 and advances CAS token',fresh.candidate_rating===5&&fresh.candidate_id!==before.candidate_id&&await p.locator('#review-rating').inputValue()==='5');
 const conflict=stale.waitForResponse(r=>r.request().method()==='POST'&&r.url()===u);await stale.locator('[data-review-edit] button').click();const response=await conflict;const after=head(await read(f),kind,f.actors.repeat);
 add('actual stale second tab gets409 without changing candidate5',response.status()===409&&after.candidate_id===fresh.candidate_id&&after.candidate_rating===5,{expected_http:409,known_baseline:'SOCIAL-QA-03 conflict page has no editor; not changed'});
 await stale.screenshot({path:H+'/screenshots/edge-actual-stale409-ru390.png'});await stale.goBack({waitUntil:'domcontentloaded'});await stale.reload();add('Back and reload recover current saved rating5 and text',await stale.locator('#review-rating').inputValue()==='5'&&await stale.locator('#review-text').inputValue()===copy('repeat',f,kind,'conflict-five'));
 await p.goto(u);await p.locator('#review-rating').selectOption('2');await p.locator('#review-text').fill('Fictional unsent transport error text');let release,intercept;const held=new Promise(resolve=>release=resolve),seen=new Promise(resolve=>intercept=resolve);
 await p.route('**/reviews/specialist/target/**',async route=>{if(route.request().method()==='POST'){intercept();await held;await route.abort('failed');}else await route.continue();});
 const navigation=p.waitForNavigation({waitUntil:'domcontentloaded'}).then(()=>({completed:true})).catch(e=>({error:String(e).split('\n')[0]}));const click=p.locator('[data-review-edit] button').click().catch(e=>String(e));await seen;
 add('SIMULATED delayed transport leaves visible input rating2 before navigation',await p.locator('#review-rating').inputValue()==='2'&&await p.locator('#review-text').isVisible(),{simulated:true});await shot(p,'edge-simulated-loading-ru390');release();await click;const nav=await navigation;await p.unroute('**/reviews/specialist/target/**');await p.goto(u);const failed=head(await read(f),kind,f.actors.repeat);
 add('SIMULATED failed transport leaves persisted candidate5 unchanged and recoverable',failed.candidate_id===fresh.candidate_id&&failed.candidate_rating===5&&await p.locator('#review-rating').inputValue()==='5',{simulated:true,navigation:nav});await shot(p,'edge-simulated-error-recovery-ru390');
}
else if(PHASE.startsWith('matrix-')){
 const state=PHASE.slice(7),f=F.cases[0],role=state==='rejected-first'?'rejected':'author';language=LANG;const p=await actor(f.actors[role]);
 for(width of[360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(kind of KINDS){await p.goto(url(f,kind));await p.locator('[data-review-edit]').waitFor();const s=await read(f),h=head(s,kind,f.actors[role]),expected=state==='empty'?'':state==='pending-edit'?'2':state==='rejected-first'?'3':'4';
  const v=await p.locator('#review-rating').inputValue(),text=await p.locator('#review-text').inputValue(),token=await p.locator('[name=expected_revision_id]').inputValue();
  const expectedText=state==='empty'?'':copy(role,f,kind,state==='pending-edit'?'candidate-two':state==='rejected-first'?'first':'initial');
  add('saved rating text and CAS match state',v===expected&&text===expectedText&&token===(h?String(h.candidate_id||h.current_id||''):''),{expected,actual:v,state});
  const count=state==='empty'||state==='pending'?0:1;add('readonly published count matches accepted state',s.reviews[kind].summary.count===count&&(!count||s.reviews[kind].summary.average===4),{state});
  await p.locator('#review-rating').focus();await p.keyboard.press('Tab');let focused=await p.locator('#review-text').evaluate(e=>e===document.activeElement);await p.keyboard.press('Shift+Tab');focused=focused&&await p.locator('#review-rating').evaluate(e=>e===document.activeElement);const style=await p.locator('#review-rating').evaluate(e=>{const s=getComputedStyle(e);return{outline:s.outlineStyle,outlineWidth:s.outlineWidth,shadow:s.boxShadow};});
  add('Tab ShiftTab focus rating and text with visible focus',focused&&(style.outline!=='none'&&style.outlineWidth!=='0px'||style.shadow!=='none'),{style});
  add('safe escaped content and no horizontal document overflow',await p.evaluate(()=>window.SOCIAL01_XSS===undefined&&document.documentElement.scrollWidth<=innerWidth+1));
  await shot(p,state+'-'+language+'-'+width+'-'+kind);
 }}
}
else throw Error('Unknown QA phase');
return{complete:true,rows,states,diagnostics,scope:'Approved SOCIAL-QA-01',browser_version:original.context().browser().version()};
}catch(e){return{complete:false,error:String(e),rows,states,diagnostics};}finally{for(const c of contexts)await c.close();}
}
