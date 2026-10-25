const H=require('./helpers.cjs');
async function saveVolunteer(p,action='draft'){
 const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/admin/volunteer/'));
 await p.locator(`button[name=action][value=${action}]`).click();const r=await response;H.assert(r.status()<400,`Volunteer ${action} HTTP${r.status()}`);await p.waitForLoadState('networkidle');
 const error=p.locator('[data-editor-errors]');H.assert(!(await error.count()),await error.innerText().catch(()=>''));
}
async function fillVolunteer(p,ctx,name){
 await p.locator('[data-editor-expand]').click();
 await H.fill(p,'#id_name_az',name);await H.fill(p,'#id_description_az','Uşaqlar üçün yaradıcılıq dərsləri və ailələrin rahat ziyarəti haqqında tam məlumat. Bu kart yalnız yerli sınaq üçün hazırlanıb.');
 await H.select(p,'#id_category','EDU');await p.waitForFunction(()=>document.querySelector('#id_subcategory').options.length>1);
 await H.select(p,'#id_subcategory',await p.locator('#id_subcategory option').evaluateAll(es=>es.find(e=>e.value)?.value));
 for(const [id,value]of Object.entries({age_from:6,age_to:12,address:'Bakı, Nərimanov rayonu, Ağa Neymətulla küçəsi 20',phone1:'+994501234567',lat:'40.4093',lng:'49.8671'}))await H.fill(p,'#id_'+id,value);
 await H.select(p,'#id_region','baku');await H.select(p,'#id_district','baku_narimanov');await H.select(p,'#id_schedule_mode','by_appointment');
 await p.locator('[data-tariff-add]').click();await H.select(p,'[data-tariff-key=editor_kind]','membership');await H.select(p,'[data-tariff-key=billing_mode]','recurring');await H.select(p,'[data-tariff-key=billing_interval]','month');await H.fill(p,'[data-tariff-key=billing_interval_count]','1');await H.fill(p,'[data-tariff-key=price]','150');await H.fill(p,'[data-tariff-key=title_az]','Aylıq yaradıcılıq');
 await p.locator('#id_photo').setInputFiles(H.path.join(ctx.fixtureDir,ctx.fixture.images[0]));await p.locator('#id_cover_photo').setInputFiles(H.path.join(ctx.fixtureDir,ctx.fixture.images[1]));
}
async function roles(ctx){
 const contexts=[];try{
 const v=await H.context(ctx.browser,ctx.fixture.origin,1440);contexts.push(v);const p=await H.login(v,ctx.fixture,'volunteer'),watch=H.watch(p,ctx.fixture.origin);
 await p.goto(ctx.fixture.origin+'/admin/volunteer/add/');const name='Role journey volunteer '+Date.now();await fillVolunteer(p,ctx,name);await saveVolunteer(p);
 const id=p.url().match(/volunteer\/(\d+)\/edit\//)?.[1];H.assert(id,'Saved volunteer place id');
 H.assert.equal(await p.locator('#id_name_az').inputValue(),name);await H.inspect(p,ctx.out,'roles-volunteer-draft');ctx.record({id:'R_VOL_DRAFT',role:'volunteer',status:'PASS',placeId:id,name,editUrl:p.url(),assertions:['real form, monthly tariff, main and cover uploads','draft saved and reopened']});
 await saveVolunteer(p,'submit');ctx.record({id:'R_VOL_SUBMIT',role:'volunteer',status:'PASS',placeId:id,assertions:['real submission accepted']});
 const a=await H.context(ctx.browser,ctx.fixture.origin);contexts.push(a);const admin=await H.login(a,ctx.fixture,'admin');
 await admin.goto(ctx.fixture.origin+`/admin/volunteer/review/${id}/`);H.assert((await admin.locator('body').innerText()).includes(name));
 await H.inspect(admin,ctx.out,'roles-moderation-before');
 const preview=admin.locator('a[data-moderation-full-preview]');H.assert.equal(await preview.count(),1,'Moderation provides a full candidate preview, not just a difference table');
 const inspectionUrl=await preview.getAttribute('href'),revisionId=inspectionUrl.match(/revision\/(\d+)/)[1];
 await inspectCandidate(ctx,a,admin,inspectionUrl,name,'volunteer');
 await assertCatalog(ctx,a,id,false);ctx.record({id:'R_PENDING_PRIVATE',role:'anonymous',status:'PASS',placeId:id});
 await admin.goto(ctx.fixture.origin+`/admin/volunteer/review/${id}/`);
 await postDecision(admin,'reject','note','');H.assert(await admin.locator('.alert-danger').count()>0,'Return needs a reason');
 await postDecision(admin,'reject','note','Уточните описание и подтвердите актуальную цену.');
 await p.goto(ctx.fixture.origin+`/admin/volunteer/${id}/edit/`);H.assert((await p.locator('body').innerText()).includes('Уточните описание'));
 await p.locator('[data-editor-expand]').click();const corrected=name+' corrected';await H.fill(p,'#id_name_az',corrected);await saveVolunteer(p,'submit');
 ctx.record({id:'R_RETURN_RESUBMIT',role:'volunteer',status:'PASS',placeId:id,assertions:['blank return reason rejected','reason visible to author','corrected and resubmitted']});
 const hub=ctx.fixture.origin+`/admin/volunteer/moderation/content/${revisionId}/`;await admin.goto(hub);await inspectCandidate(ctx,a,admin,inspectionUrl,corrected,'corrected');await admin.goto(hub);
 await postDecision(admin,'approve','reason','Проверены описание, тариф и фотографии.');
 await publicSurfaces(ctx,a,id,corrected,'volunteer');
 await p.goto(ctx.fixture.origin+'/admin/volunteer/');H.assert(await p.locator(`a[href*="/volunteer/${id}/"]`).count()>0);ctx.record({id:'R_VOL_PROFILE',role:'volunteer',status:'PASS',placeId:id,assertions:['own published card remains in volunteer workspace']});
 await p.goto(ctx.fixture.origin+`/admin/volunteer/${id}/edit/`);await p.locator('[data-editor-expand]').click();const updated=corrected+' updated';await H.fill(p,'#id_name_az',updated);await saveVolunteer(p,'submit');
 await assertPublicName(ctx,a,id,corrected,updated);await inspectCandidate(ctx,a,admin,inspectionUrl,updated,'published-edit');await admin.goto(hub);await postDecision(admin,'approve','reason','Обновление названия проверено.');await publicSurfaces(ctx,a,id,updated,'volunteer-update');
 ctx.record({id:'R_PUBLISHED_EDIT',role:'volunteer',status:'PASS',placeId:id,assertions:['public version unchanged until approval','full candidate contains new data','approval updates same public card']});
 await p.goto(ctx.fixture.origin+`/admin/volunteer/${id}/edit/`);await p.locator('[data-editor-expand]').click();const declined=updated+' declined';await H.fill(p,'#id_name_az',declined);await saveVolunteer(p,'submit');await admin.goto(hub);await postDecision(admin,'reject','reason','Отклонено: изменение не подтверждено.');await assertPublicName(ctx,a,id,updated,declined);
 ctx.record({id:'R_REJECT',role:'admin',status:'PASS',placeId:id,assertions:['final rejection with reason','public data unchanged']});
 const other=await H.context(ctx.browser,ctx.fixture.origin);contexts.push(other);await H.login(other,ctx.fixture,'volunteer_other');H.assert([403,404].includes((await other.request.get(ctx.fixture.origin+`/admin/volunteer/${id}/edit/`)).status()));H.assert([403,404].includes((await other.request.get(ctx.fixture.origin+inspectionUrl)).status()));ctx.record({id:'R_CROSS_AUTHOR',role:'volunteer_other',status:'PASS',placeId:id});
 await ownerJourney(ctx,a,admin);
 const direct=await require('./create.cjs').create(ctx,'admin');const published=await require('./publication.cjs').publish(ctx,direct);await require('./publication.cjs').publicCheck(ctx,published);await admin.goto(direct.editUrl);await admin.locator('[data-place-accordion-expand-all]').click();await H.fill(admin,'#id_name_az',direct.name+' edited');await require('./pricing.cjs').save(admin,'admin');await assertPublicName(ctx,a,published.id,direct.name,direct.name+' edited');await admin.locator('[data-place-accordion-expand-all]').click();await H.fill(admin,'#id_name_az',direct.name+' edited');const continued=admin.waitForEvent('domcontentloaded');await admin.locator('[name=_continue]').first().click();await continued;await ownerDecision(ctx,admin,published.id,direct.name+' edited','approve');await publicSurfaces(ctx,a,published.id,direct.name+' edited','admin-direct');ctx.record({id:'R_ADMIN_DIRECT',role:'admin',status:'PASS',placeId:published.id,assertions:['new admin place created and published','admin draft edit stays private until explicit publication']});
 H.assert.deepEqual(watch.errors,[]);
 }catch(error){ctx.record({id:'ROLE_JOURNEY',status:'FAIL',error:String(error)});for(const [i,c]of contexts.entries()){const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,`failure-role-${i}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,`failure-role-${i}.txt`),await p.locator('body').innerText());}}throw error;}finally{for(const c of contexts.reverse())await c.close();}
}
async function postDecision(p,action,noteField,note){
 await p.locator(`[name=${noteField}]`).fill(note);const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.request().isNavigationRequest());await p.locator(`button[name=action][value=${action}]`).click();const r=await response;H.assert(r.status()<400,`Decision ${action}: HTTP${r.status()}`);await p.waitForLoadState('networkidle');
}
async function inspectCandidate(ctx,c,p,url,name,label){
 await p.goto(ctx.fixture.origin+url);H.assert((await p.locator('h1').innerText()).includes(name),'Full inspection shows candidate, not saved live values');
 if(await p.locator('[data-preview-expand]').isVisible())await p.locator('[data-preview-expand]').click();
 H.assert(await p.locator('[data-preview-photo]').count()>0,'Full inspection shows candidate media');
 for(const word of ['Тариф','Контакты','Расписание'])H.assert((await p.locator('body').innerText()).includes(word),`Full inspection includes ${word}`);
 await H.inspect(p,ctx.out,'roles-inspection-'+label);
 const site=p.locator('a[href*="/site-preview/"]').first();H.assert(await site.count());const siteUrl=await site.getAttribute('href');const full=await c.newPage();const response=await full.goto(ctx.fixture.origin+siteUrl);H.assert.equal(response.status(),200);H.assert((await full.locator('body').innerText()).includes(name));H.assert(await full.locator('.site-preview-bar').isVisible());H.assert((response.headers()['cache-control']||'').includes('no-store'));await H.inspect(full,ctx.out,'roles-full-site-'+label);await full.close();
 ctx.record({id:'R_MOD_FULL',role:'admin',status:'PASS',candidate:name,assertions:['complete candidate inspection','prices, contacts, schedule and photos','real public template private preview','no public mutation']});
}
async function assertCatalog(ctx,c,id,visible){const anon=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await anon.newPage();await p.goto(ctx.fixture.origin+'/ru/catalog/?q='+encodeURIComponent('Role journey'));const count=await p.locator(`a[href*="/place/${id}-"]`).count();H.assert.equal(count>0,visible,`Catalog visibility ${id}`);}finally{await anon.close();}}
async function assertPublicName(ctx,c,id,yes,no){const anon=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await anon.newPage();await p.goto(ctx.fixture.origin+'/ru/catalog/?q='+encodeURIComponent(yes));const link=p.locator(`a[href*="/place/${id}-"]`).first();H.assert(await link.count());await p.goto(new URL(await link.getAttribute('href'),ctx.fixture.origin).href);const text=await p.locator('body').innerText();H.assert(text.includes(yes));H.assert(!text.includes(no));}finally{await anon.close();}}
async function publicSurfaces(ctx,c,id,name,label){
 const anon=await H.context(ctx.browser,ctx.fixture.origin);try{const p=await anon.newPage();await p.goto(ctx.fixture.origin+'/ru/catalog/?q='+encodeURIComponent(name));const link=p.locator(`a[href*="/place/${id}-"]`).first();H.assert(await link.count());const url=await link.getAttribute('href');await p.goto(new URL(url,ctx.fixture.origin).href);H.assert((await p.locator('body').innerText()).includes(name));H.assert(await p.locator('main img[src*="/media/"]').count());await H.inspect(p,ctx.out,'roles-public-'+label);await p.goto(ctx.fixture.origin+'/ru/');const homeVisible=await p.locator(`a[href*="/place/${id}-"]`).count()>0;ctx.record({id:'R_PUBLIC_SURFACES',role:'anonymous',status:'PASS',placeId:id,publicUrl:new URL(url,ctx.fixture.origin).href,name,homeVisible,assertions:['public detail current title and stored media','same card visible in catalog','home visibility recorded against recommendation ranking']});}finally{await anon.close();}
}
async function ownerJourney(ctx,a,admin){
 const item=await require('./create.cjs').create(ctx,'owner');const id=item.editUrl.match(/places\/(\d+)/)[1];await require('./publication.cjs').sendForReview(ctx,item);
 const hub=await openOwnerModeration(ctx,admin,id,item.name);const url=await admin.locator('[data-moderation-full-preview]').getAttribute('href');await inspectCandidate(ctx,a,admin,url,item.name,'owner');await admin.goto(hub);await postDecision(admin,'approve','reason','Карточка владельца проверена полностью.');await publicSurfaces(ctx,a,id,item.name,'owner');
 const o=await H.context(ctx.browser,ctx.fixture.origin);let p;try{p=await H.login(o,ctx.fixture,'owner');await p.goto(ctx.fixture.origin+'/ru/account/profile/');H.assert(await p.locator(`a[href*="/places/${id}/edit/"]`).count(),'Owner profile links the place');await H.inspect(p,ctx.out,'roles-owner-profile');await p.goto(ctx.fixture.origin+'/ru/account/places/');H.assert(await p.locator(`a[href*="/places/${id}/edit/"]`).count());await p.goto(item.editUrl);await H.fill(p,'#id_name_az',item.name+' corrected');await require('./pricing.cjs').save(p,'owner');H.assert.equal(await p.locator('#id_name_az').inputValue(),item.name+' corrected');await assertPublicName(ctx,a,id,item.name,item.name+' corrected');ctx.record({id:'R_OWNER_PROFILE_EDIT',role:'owner',status:'PASS',placeId:id,assertions:['published place in account profile and dashboard','real subsequent owner edit saves','saved candidate does not leak onto public page']});
 await require('./publication.cjs').sendForReview(ctx,item);await ownerDecision(ctx,admin,id,item.name+' corrected','reject');await assertPublicName(ctx,a,id,item.name,item.name+' corrected');ctx.record({id:'R_OWNER_REJECT',role:'admin',status:'PASS',placeId:id,assertions:['owner proposal rejected through real request decision','public original preserved']});
 await H.fill(p,'#id_name_az',item.name+' accepted');p=await saveOwnerAfterReview(p,ctx,item.name+' accepted');await require('./publication.cjs').sendForReview(ctx,item);await ownerDecision(ctx,admin,id,item.name+' accepted','approve');await publicSurfaces(ctx,a,id,item.name+' accepted','owner-update');ctx.record({id:'R_OWNER_RESUBMIT',role:'owner',status:'PASS',placeId:id,assertions:['rejected proposal corrected and resubmitted','same place updated after approval']});
 }catch(error){if(p&&!p.isClosed()){await p.screenshot({path:H.path.join(ctx.out,'failure-owner-journey.png'),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,'failure-owner-journey.txt'),await p.locator('body').innerText());}throw error;}finally{await o.close();}
}
async function openOwnerModeration(ctx,p,id,candidate){await p.goto(ctx.fixture.origin+`/admin/volunteer/moderation/?place=${id}`);const link=p.locator('a[href*="/moderation/content/"]').filter({hasText:candidate}).first();H.assert(await link.count(),'Owner submission appears in the unified publication queue');await link.click();return p.url();}
async function saveOwnerAfterReview(p,ctx,value){
 const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/save-photos/'));
 await p.locator('[name=form_action][value=save_draft]').first().click();const r=await response;
 const payload=r.status()===422?await r.json():null;
 if(r.status()===422&&payload?.conflict==='candidate_version_conflict'){
  const link=p.locator('[data-pc-conflict-actions]:not([hidden]) a[href*="candidate_current"]');await link.waitFor({state:'visible'});
  H.assert.equal(await p.locator('#id_name_az').inputValue(),value,'Conflict retains the attempted edit');
  const opened=p.context().waitForEvent('page');await link.click();const next=await opened;await next.waitForLoadState('networkidle');await p.close();
  await H.fill(next,'#id_name_az',value);await require('./pricing.cjs').save(next,'owner');p=next;
  ctx.record({id:'R_OWNER_VERSION_RECOVERY',role:'owner',status:'PASS',assertions:['stale candidate rejected with the explicit candidate_version_conflict code (HTTP422)','attempted input retained','current server version opened using visible recovery action','edit reapplied and saved']});
 }else{H.assert.equal(r.status(),200);await p.waitForLoadState('networkidle');await p.reload();}
 H.assert.equal(await p.locator('#id_name_az').inputValue(),value);return p;
}
async function ownerDecision(ctx,p,id,candidate,decision){const hub=await openOwnerModeration(ctx,p,id,candidate);const link=await p.locator('[data-moderation-full-preview]').getAttribute('href');await p.goto(ctx.fixture.origin+link);H.assert((await p.locator('h1').innerText()).includes(candidate));await p.goto(hub);await postDecision(p,decision,'reason',decision==='approve'?'Исправленная карточка проверена.':'Отклонено: предложенное название не подтверждено.');}
module.exports={roles,fillVolunteer,saveVolunteer};
