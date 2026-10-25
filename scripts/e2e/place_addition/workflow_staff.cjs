const H=require('./helpers.cjs');
const {fillPlace}=require('./create.cjs');
const {fillVolunteer,saveVolunteer}=require('./roles.cjs');

const formSelector=role=>role==='admin'?'#place_form':'[data-volunteer-admin-form]';
async function expanded(p,role){await p.locator(role==='admin'?'[data-place-accordion-expand-all]':'[data-editor-expand]').click();}
async function nativeState(p,role){return p.locator(formSelector(role)).evaluate(form=>form.kmNativeMedia.captureState());}
async function waitSaved(p,role){await p.waitForFunction(selector=>{const form=document.querySelector(selector);return form?.querySelector('.km-staff-save-panel')?.dataset.state==='saved'&&!form.kmDraftHasPending();},formSelector(role),{timeout:35000});}
async function addGallery(p,ctx,role,indexes){const files=indexes.map(index=>H.path.join(ctx.fixtureDir,ctx.fixture.images[index]));
  await p.locator(role==='admin'?'[data-gallery-root] > input[type=file][multiple]':'[name=gallery_images]').setInputFiles(files);
}
async function saveNative(p,role){
  if(role==='volunteer'){await saveVolunteer(p);return;}
  const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.request().isNavigationRequest());
  await p.locator('[name=_save_draft]').first().click();const r=await response;H.assert(r.status()<400,`Admin private draft HTTP${r.status()}`);
  await p.waitForLoadState('networkidle');H.assert(/\/place\/\d+\/change\//.test(new URL(p.url()).pathname),'Native admin draft creates an editable private card');
  H.assert.equal(await p.locator('.errornote').count(),0,'No admin validation error');
}
async function unlimitedStable(p,ctx,role){
  await expanded(p,role);
  const control=p.locator('[data-tariff-key=is_unlimited]').first();await H.reveal(control);await control.scrollIntoViewIfNeeded();await control.focus();
  const before=await control.boundingBox();const y=await p.evaluate(()=>window.scrollY);
  await control.check();await p.waitForTimeout(350);
  const after=await control.boundingBox();H.assert(await control.isChecked());H.assert(await control.evaluate(el=>el===document.activeElement),'Unlimited keeps focus on the same control');
  H.assert(Math.abs(after.y-before.y)<8,'Unlimited does not relocate its field');H.assert(Math.abs((await p.evaluate(()=>window.scrollY))-y)<8,'Unlimited does not jump the viewport');
  await H.select(p,'[data-tariff-key=billing_mode]','one_time');await H.select(p,'[data-tariff-key=validity_interval]','month');await H.fill(p,'[data-tariff-key=validity_interval_count]','1');
  const billing=p.locator('[data-tariff-key=billing_mode]').first();H.assert(await billing.isVisible());H.assert.equal(await billing.locator('xpath=ancestor::details').count(),0,'Required billing is not hidden in advanced');
  const plan=JSON.parse(await p.locator('[name=pricing_plans]').inputValue())[0];H.assert.equal(plan.billing_mode,'one_time');H.assert.equal(plan.validity_interval,'month');H.assert.equal(Number(plan.validity_interval_count),1);H.assert.equal(plan.is_unlimited,true);H.assert(!plan.valid_from&&!plan.valid_until,'Prepaid month needs no calendar dates');
  ctx.record({id:'STAFF_UNLIMITED_STABLE',role,status:'PASS',deltaY:after.y-before.y,assertions:['same checkbox node keeps focus','no viewport jump','one payment plus one month remains canonical','required payment outside advanced']});
}
async function workflowStaff(ctx){
  for(const role of (ctx.roles || ['volunteer','admin'])){
    const context=await H.context(ctx.browser,ctx.fixture.origin,1440);let p;
    try{
      await context.addCookies([{name:'django_language',value:'ru',url:ctx.fixture.origin}]);
      p=await H.login(context,ctx.fixture,role);p.on('dialog',dialog=>dialog.accept());const watched=H.watch(p,ctx.fixture.origin);
      await p.goto(ctx.fixture.origin+(role==='admin'?'/admin/catalog/place/add/?type=permanent':'/admin/volunteer/add/'));
      await p.waitForFunction(selector=>!!document.querySelector(selector)?.kmDraftSave,formSelector(role));
      const name=`Staff mixed gallery ${role} ${Date.now()}`;
      if(role==='volunteer')await fillVolunteer(p,ctx,name);else{await fillPlace(p,'admin',name);await p.locator('#id_photo').setInputFiles(H.path.join(ctx.fixtureDir,ctx.fixture.images[0]));}
      // Separate picker visits must append, not replace the first photo.
      await addGallery(p,ctx,role,[0]);await addGallery(p,ctx,role,[1]);
      H.assert.equal((await nativeState(p,role)).gallery_order.length,2,'Two independent selections are retained');
      await p.locator(role==='admin'?'[data-gallery-card]:visible [data-media-main]':'.km-native-gallery [data-media-main]').first().click();
      await p.waitForFunction(selector=>!document.querySelector(selector).kmNativeMedia.blocking(),formSelector(role));
      const mediaIds=await p.locator(formSelector(role)).evaluate(form=>form.kmNativeMedia.snapshotMedia().map(row=>row.id));H.assert.equal(new Set(mediaIds).size,mediaIds.length,'Main and retained gallery upload have distinct media IDs');
      await unlimitedStable(p,ctx,role);await waitSaved(p,role);await saveNative(p,role);await expanded(p,role);
      const editUrl=p.url(),initial=await nativeState(p,role);H.assert.equal(initial.gallery_order.length,2);H.assert(initial.gallery_order.every(key=>/^(saved:|candidate:)/.test(key)),'Existing gallery has real persisted keys');
      ctx.record({id:'STAFF_GALLERY_MATERIALIZED',role,status:'PASS',editUrl,name,assertions:['two separate file selections','real native draft POST','reopened candidate gallery uses stored keys']});
      if(role==='volunteer'){
        const gallery=p.locator('.km-native-gallery');await gallery.locator('article').first().locator('[data-media-move="1"]').click();
        H.assert.deepEqual((await nativeState(p,role)).gallery_order,[initial.gallery_order[1],initial.gallery_order[0]]);
        await gallery.locator('article').first().locator('[data-media-remove]').click();
        await gallery.locator('article').first().locator('[data-media-main]').click();
      }else{
        const cards=p.locator('[data-gallery-card]:visible').filter({has:p.locator('[data-gallery-initial-url]')});
        const first=cards.first();await first.locator('[name$="-caption"]').fill('Preserved candidate caption');await first.locator('[data-gallery-drag-handle]').focus();await first.locator('[data-gallery-drag-handle]').press('ArrowRight');
        H.assert.deepEqual((await nativeState(p,role)).gallery_order,[initial.gallery_order[1],initial.gallery_order[0]]);
        await cards.first().locator('[data-gallery-remove]').click();await cards.first().locator('[data-media-main]').click();
      }
      await p.waitForFunction(selector=>document.querySelector(selector)?.elements.namedItem('photo').files.length===1,formSelector(role));
      await addGallery(p,ctx,role,[2]);await waitSaved(p,role);
      const mixed=await nativeState(p,role);
      // Admin swaps the former cover into the chosen gallery slot, matching
      // the owner editor. Both replaced/removed stored rows need delete tokens.
      H.assert.deepEqual(mixed.gallery_order,role==='admin'?['new:0','new:1']:[initial.gallery_order[0],'new:0']);
      H.assert.equal(mixed.delete_gallery_ids.length,role==='admin'?2:1);
      const savedPricing=JSON.parse(await p.locator('[name=pricing_plans]').inputValue());
      const resume=p.url();H.assert(new URL(resume).searchParams.get('draft_id'),'Saved private working copy has a resume identifier');
      await p.reload();await waitSaved(p,role);await expanded(p,role);
      H.assert.deepEqual(await nativeState(p,role),mixed,'Mixed saved/new gallery, deletions and captions survive reload');
      if(role==='admin'){
        const caption=p.locator('[data-gallery-card]:visible [name$="-caption"]');
        const restored=await caption.evaluateAll(inputs=>inputs.find(input=>input.value==='Preserved candidate caption')?.closest('label')?.querySelector('[data-km-counter]')?.textContent);
        H.assert(restored?.includes('27 / 255'),'Restored gallery caption counter shows its actual 27 characters');
      }
      H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),savedPricing,'Canonical tariff survives restore');
      H.assert(await p.locator('[data-tariff-key=is_unlimited]').first().isChecked(),'Restored tariff control matches the saved JSON');
      if(role==='volunteer'){
        const progress=await p.locator('[data-progress-pct]').allTextContents();H.assert.equal(progress.length,2);H.assert.equal(progress[0],progress[1],'Header and sidebar show the same authoritative readiness');
      }
      for(const width of [1440,390,320]){
        await p.setViewportSize({width,height:1000});await p.locator(role==='admin'?'[data-gallery-root]':'.km-native-gallery').scrollIntoViewIfNeeded();
        if(role==='admin'){
          const duplicateAlert=p.locator('[data-place-duplicate-alert]');
          if(await duplicateAlert.isVisible())H.assert(await duplicateAlert.evaluate(el=>{const bounds=el.getBoundingClientRect();return [...el.querySelectorAll('strong,p,ul,li,a')].every(child=>{const r=child.getBoundingClientRect();return r.left>=bounds.left&&r.right<=bounds.right;});}),`Admin ${width}: duplicate warning content fits inside the alert`);
        }
        await H.inspect(p,ctx.out,`staff-${role}-gallery-${width}`);
        await p.locator('[data-tariff-key=is_unlimited]').first().scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`staff-${role}-tariff-${width}`);
        const fit=await p.locator('.pw-price-choices button').evaluateAll(buttons=>buttons.every(button=>{const label=button.querySelector('.pw-price-choice-label'),b=button.getBoundingClientRect(),l=label.getBoundingClientRect();return l.left>=b.left+2&&l.right<=b.right-2&&label.scrollWidth<=label.clientWidth+1;}));H.assert(fit,`${role} ${width}: price choice labels fit inside their buttons`);
      }
      await p.setViewportSize({width:1440,height:1000});
      const popupPromise=context.waitForEvent('page');await p.locator('[data-km-preview]').click();const popup=await popupPromise;await popup.waitForLoadState('domcontentloaded');
      H.assert((await popup.locator('body').innerText()).includes(name),'Actual current-data preview includes the working title');H.assert(await popup.locator('.site-preview-bar').isVisible(),'Preview is private');await popup.close();
      await saveNative(p,role);await expanded(p,role);const final=await nativeState(p,role);H.assert.equal(final.gallery_order.length,2);H.assert(final.gallery_order.every(key=>!key.startsWith('new:')),'Explicit save materializes only the intended two gallery images');
      H.assert.deepEqual(watched.errors,[],'No JS runtime errors');
      ctx.record({id:'STAFF_MIXED_GALLERY_RESTORE',role,status:'PASS',editUrl:p.url(),assertions:['existing photo keyboard/button reorder','existing deletion and make-main','new photo appended','private draft round-trip retains exact order/captions','visible tariff restore','real preview','native resave preserves two intended images','320/390/1440 screenshots with no horizontal overflow','duplicate warning content stays inside its alert']});
    }catch(error){ctx.record({id:'STAFF_WORKFLOW',role,status:'FAIL',error:String(error),url:p?.url()});if(p&&!p.isClosed()){await p.screenshot({path:H.path.join(ctx.out,`staff-${role}-failure.png`),fullPage:false});H.fs.writeFileSync(H.path.join(ctx.out,`staff-${role}-failure.txt`),await p.locator('body').innerText());H.fs.writeFileSync(H.path.join(ctx.out,`staff-${role}-overflow.json`),JSON.stringify(await p.evaluate(()=>({scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,items:[...document.querySelectorAll('body *')].filter(el=>{const r=el.getBoundingClientRect();return r.width&&r.right>document.documentElement.clientWidth+1;}).map(el=>({tag:el.tagName,id:el.id,cls:el.className,right:el.getBoundingClientRect().right,width:el.getBoundingClientRect().width}))})),null,2));}throw error;}
    finally{await context.close();}
  }
}
module.exports={workflowStaff};

if(require.main===module){
  const fixturePath=process.argv[2]||'.tmp/place-implementation-20261023/fixture-feedback-frozen.json',fixture=JSON.parse(H.fs.readFileSync(fixturePath,'utf8'));
  H.assert(fixture.synthetic&&fixture.database==='qa_stage04','Only synthetic isolated QA fixture');
  const out=H.path.resolve(process.argv[3]||'output/playwright/workflow-staff');H.fs.mkdirSync(out,{recursive:true});const results=[];
  const record=row=>{results.push(row);H.fs.writeFileSync(H.path.join(out,'results.json'),JSON.stringify({synthetic:true,externalMaps:'NOT RUN: external transport blocked',results},null,2));console.log(row.status,row.id,row.role,row.error||'');};
  (async()=>{const build=await(await fetch(fixture.origin+'/__qa__/build/')).json();H.assert(build.synthetic,'Synthetic server attestation');const browser=await H.launch();try{await workflowStaff({browser,fixture,fixtureDir:H.path.dirname(H.path.resolve(fixturePath)),out,record});}finally{await browser.close();}})().catch(error=>{console.error(error);process.exitCode=1;});
}
