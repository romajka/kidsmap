async page=>{
 const B='http://127.0.0.1:40257',P='http://localhost:40257',O='/home/ramin/kidsmap/output/playwright/admin-moderation-fix-2026-10-16-r1';
 const f=await(await page.request.get(B+'/admin/qa/fixtures/')).json(),rows=[],states=[],diagnostics=[],contexts=[];
 const add=(id,ok,data={})=>{rows.push({id,status:ok?'PASS':'FAIL',...data});if(!ok)throw Error(id)};
 const allowed=url=>url.startsWith(B+'/')||url.startsWith(P+'/');
 await page.route('**/*',r=>allowed(r.request().url())?r.continue():r.abort());
 page.on('pageerror',e=>diagnostics.push({type:'pageerror',message:String(e)}));
 page.on('response',r=>{if(allowed(r.url())&&r.status()>=400)diagnostics.push({type:'http',status:r.status(),path:new URL(r.url()).pathname});});
 async function state(stage){const r=await page.request.get(B+'/admin/qa/state/');add('QA readback '+stage,r.status()===200);const s=await r.json();states.push({stage,...s});return s;}
 const head=(s,i)=>s.reviews.find(x=>x.id===f.reviews[i].head);
 const workflow=i=>B+'/admin/catalog/placereview/'+f.reviews[i].head+'/workflow/';
 async function decision(i,action,reason=''){
  await page.goto(workflow(i));await page.locator('[data-review-workflow]').waitFor();
  if(reason)await page.locator('#review-reason').fill(reason);
  const promise=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/'+action+'/'));
  await page.locator('form[action$="/'+action+'/"] button[type=submit]').click();const r=await promise;await page.waitForLoadState('domcontentloaded');
  add('native '+action+' HTTP',r.status()===302,{http:r.status()});await page.locator('[data-review-workflow]').waitFor();
  add('native '+action+' stays on admin host',page.url().startsWith(B+'/admin/'));
 }
 async function bulk(i){
  await page.goto(B+'/admin/catalog_moderation/moderationreview/');await page.locator('#result_list').waitFor();
  await page.locator('input.action-select[value="'+f.reviews[i].head+'"]').check();
  const promise=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/moderationreview/'));
  await page.locator('[data-bulk-submit="approve_selected"]').click();const r=await promise;await page.waitForLoadState('domcontentloaded');
  add('native bulk approval HTTP',r.status()===302,{http:r.status()});
 }
 async function author(i){
  const c=await page.context().browser().newContext({viewport:{width:390,height:950}});contexts.push(c);await c.route('**/*',r=>allowed(r.request().url())?r.continue():r.abort());const p=await c.newPage();
  await p.goto(P+'/ru/auth/login/');await p.locator('[name=username]').fill('fictional_author_'+i);await p.locator('[name=password]').fill(f.password);
  await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/'),{waitUntil:'domcontentloaded'}),p.locator('form.register-form--login button[type=submit]').click()]);return p;
 }
 async function edit(p,text,rating){await p.goto(P+'/ru/reviews/place/target/'+f.place+'/');await p.locator('#review-rating').selectOption(String(rating));await p.locator('#review-text').fill(text);await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator('form[data-review-edit] button').click()]);}
 const guestContext=await page.context().browser().newContext({viewport:{width:1440,height:950}});contexts.push(guestContext);await guestContext.route('**/*',r=>allowed(r.request().url())?r.continue():r.abort());const guest=await guestContext.newPage();
 try{
  await page.goto(B+'/admin/');if(page.url().includes('/login/')){await page.locator('[name=username]').fill(f.username);await page.locator('[name=password]').fill(f.password);await Promise.all([page.waitForURL(B+'/admin/',{waitUntil:'domcontentloaded'}),page.getByRole('button',{name:'Войти',exact:true}).click()]);}
  await page.context().addCookies([{name:'django_language',value:'ru',url:B}]);await page.setViewportSize({width:1440,height:950});
  const initial=await state('initial');add('four initial pending candidates',initial.reviews.filter(x=>x.candidate).length===4);
  await page.goto(B+'/admin/catalog_moderation/moderationreview/');await page.locator('#result_list').waitFor();add('AM03 queue includes first reviews and edits',await page.locator('#result_list tbody tr').count()===4);await page.screenshot({path:O+'/queue-four-candidates.png'});
  await page.goto(workflow(1));await page.locator('[data-candidate-id]').waitFor();add('AM01 workflow stays admin',page.url().startsWith(B+'/admin/'));add('candidate and published versions both readable',await page.locator('[data-current-revision]').count()===1&&(await page.locator('[data-candidate-id]').innerText()).includes('Fictional EDIT awaiting approval 1'));await page.screenshot({path:O+'/review-before-decision.png'});
  await guest.goto(P+'/ru/reviews/place/target/'+f.place+'/');add('guest cannot read pending candidates',await guest.locator('[data-candidate-id]').count()===0&&!((await guest.locator('main.typed-reviews').innerText()).includes('Fictional EDIT awaiting approval')));
  await decision(0,'approve');let s=await state('single-approved');add('single approval binds exact candidate',head(s,0).current===f.reviews[0].candidate&&head(s,0).candidate===null&&head(s,0).public);
  await decision(1,'reject','Fictional reason: clarify submitted text');s=await state('edit-rejected');add('rejection preserves old public version',head(s,1).current===head(initial,1).current&&head(s,1).candidate===null&&head(s,1).public);
  await bulk(2);s=await state('bulk-approved');add('AM04 bulk fully approves revision',head(s,2).current===f.reviews[2].candidate&&head(s,2).candidate===null&&head(s,2).revisions.some(x=>x.id===f.reviews[2].candidate&&x.status==='approved'));
  const writer=await author(3);await page.goto(workflow(3));await page.locator('[data-candidate-id]').waitFor();
  await edit(writer,'Fictional replacement from author <script>window.REVIEW_XSS=1</script>',3);s=await state('candidate-replaced');const replacement=head(s,3).candidate;
  add('author native edit replaced candidate',replacement!==f.reviews[3].candidate);
  const stale=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/approve/'));await page.locator('form[action$="/approve/"] button').click();const staleResponse=await stale;add('stale admin tab refuses replacement',staleResponse.status()===409);s=await state('stale-refused');add('stale decision made no change',head(s,3).candidate===replacement&&head(s,3).current===head(initial,3).current);
  await decision(3,'approve');s=await state('replacement-approved');const published=head(s,3).current;add('fresh review selects replacement',published===replacement&&head(s,3).candidate===null);
  await edit(writer,'Fictional pending correction retained during hide',4);s=await state('correction-pending');const pending=head(s,3).candidate;
  await decision(3,'hide');s=await state('hidden');add('AM05 hidden review leaves public query',!head(s,3).public);add('AM05 hide preserves current and candidate',head(s,3).current===published&&head(s,3).candidate===pending&&head(s,3).revisions.some(x=>x.id===pending&&x.status==='pending'));
  await guest.reload();add('hidden text absent from guest website',!((await guest.locator('main.typed-reviews').innerText()).includes('Fictional replacement from author')));await page.screenshot({path:O+'/review-hidden-with-pending.png'});
  await decision(3,'restore');s=await state('restored');add('restore retains undecided edit',head(s,3).public&&head(s,3).current===published&&head(s,3).candidate===pending);
  await guest.reload();add('restored text visible; pending text private',(await guest.locator('main.typed-reviews').innerText()).includes('Fictional replacement from author')&&!((await guest.locator('main.typed-reviews').innerText()).includes('Fictional pending correction')));add('literal review HTML is not executable',await guest.evaluate(()=>window.REVIEW_XSS===undefined));
  await decision(3,'approve');s=await state('correction-approved');add('final edit approved completely',head(s,3).current===pending&&head(s,3).candidate===null&&head(s,3).rating===4);
  const beforePreview=JSON.stringify(s.places);const pr=await page.goto(B+'/admin/catalog/place/'+f.pending_place+'/site-preview/');await page.locator('h1').first().waitFor();add('AM02 private full preview renders',pr.status()===200&&page.url().startsWith(B+'/admin/'));add('private preview noindex and no-store',pr.headers()['x-robots-tag'].includes('noindex')&&pr.headers()['cache-control'].includes('no-store'));await page.screenshot({path:O+'/pending-place-preview.png'});
  s=await state('after-preview');add('preview changed no place fields',JSON.stringify(s.places)===beforePreview);let g=await guest.goto(P+'/ru/place/'+f.pending_place+'-uydurma-mekan/');add('pending public place remains hidden',g.status()===404);
  await page.goto(B+'/admin/catalog/placeownershiprequest/');await page.locator('#result_list').waitFor();const staleRow=page.locator('#result_list tbody tr').filter({has:page.locator('a[href*="/'+f.ownership_request+'/change/"]')});add('AM07 stale list states block',await staleRow.count()===1&&(await staleRow.innerText()).includes('Заявка устарела')&&await staleRow.locator('a[href*="/approve/"]').count()===0);await page.screenshot({path:O+'/stale-request-list.png'});
  await page.goto(B+'/admin/catalog_moderation/moderationplace/'+f.pending_place+'/change/');await page.locator('button[name="_publish_place"]').filter({visible:true}).first().click();const dialog=page.getByRole('dialog');await dialog.waitFor();const post=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/change/'));await dialog.getByRole('button',{name:'Опубликовать',exact:true}).click();add('publish POST succeeded',(await post).status()===302);await page.waitForURL(B+'/admin/catalog/place/'+f.pending_place+'/change/',{waitUntil:'domcontentloaded'});add('AM08 concrete editor after publish',!(await page.locator('body').innerText()).includes('Возможно оно было удалено'));await page.screenshot({path:O+'/published-place-editor.png'});
  g=await guest.goto(P+'/ru/place/'+f.pending_place+'-uydurma-mekan/');add('published place visible to guest',g.status()===200);s=await state('final');add('final state: published place and no pending reviews',s.public_places.includes(f.pending_place)&&s.reviews.every(x=>x.candidate===null));await guest.screenshot({path:O+'/published-place-public.png'});
  return {complete:true,rows,states,diagnostics,browser:page.context().browser().version(),hosts:{admin:B,public:P}};
 }catch(e){return{complete:false,error:String(e),rows,states,diagnostics,url:page.url()};}finally{for(const c of contexts)await c.close();}
}
