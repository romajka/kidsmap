async (page) => {
  const origin='http://127.0.0.1:33326',rows=[],pngs=[],errors=[],requests=[];
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  const shot=async name=>{const p='/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/png/'+name+'.png';await page.screenshot({path:p});pngs.push(p);return p;};
  const record=(id,checks,facts={})=>{rows.push({id,checks,facts});};
  page.on('pageerror',e=>errors.push(e.message));
  page.on('requestfailed',r=>requests.push({url:r.url(),error:r.failure()?.errorText}));
  try {
  await page.goto(origin+'/qa/login/author/');
  for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
    for(const width of [390,768,1440]){
      await page.setViewportSize({width,height:844});await page.goto(origin+prefix+'/reviews/');await finite();
      await page.locator('select[name=sort]').selectOption('likes');
      await Promise.all([page.waitForURL('**/reviews/?sort=likes'),page.locator('.reviews-polished-toolbar button[type=submit]').click()]);
      await finite();
      const order=await page.locator('.review-author').allTextContents();
      const form=page.locator('#site-reviews form.review-form');
      await form.locator('.review-star[data-value="4"]').click();
      await form.locator('[name=author_name]').fill('F'.repeat(80));
      await form.locator('[name=text]').fill('Fictional Azərbaycan русский English '.repeat(35));
      await form.locator('[name=author_name]').focus();await page.keyboard.press('Tab');
      const facts=await form.evaluate(f=>{
        const name=f.querySelector('[name=author_name]'),text=f.querySelector('[name=text]'),grid=f.querySelector('.review-form-grid');
        const n=name.getBoundingClientRect(),t=text.getBoundingClientRect(),g=grid.getBoundingClientRect();
        const focus=getComputedStyle(text);
        return {document:document.documentElement.scrollWidth,viewport:innerWidth,rating:f.querySelector('[name=rating]').value,
          stars:f.querySelectorAll('.review-star.active').length,nameLength:name.value.length,textLength:text.value.length,
          focused:document.activeElement===text,focusOutline:focus.outlineStyle,focusShadow:focus.boxShadow,
          nameFits:n.left>=0&&n.right<=innerWidth+1,textFits:t.left>=0&&t.right<=innerWidth+1,
          gridFits:g.left>=0&&g.right<=innerWidth+1,columns:getComputedStyle(grid).gridTemplateColumns};
      });
      await form.locator('[name=text]').scrollIntoViewIfNeeded();await finite();await shot('form-'+lang+'-'+width);
      const card=page.locator('.review-item').first();await card.scrollIntoViewIfNeeded();await finite();
      const visible=await card.evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.top<innerHeight&&r.bottom>0&&Number(s.opacity)>0&&s.visibility!=='hidden';});
      await shot('cards-'+lang+'-'+width);
      record('native-form-sort-focus-'+lang+'-'+width,{
        native_sort_url:new URL(page.url()).searchParams.get('sort')==='likes',
        sort_selected:await page.locator('select[name=sort]').inputValue()==='likes',
        sort_order:order[0].trim()==='Fictional reviewer 1',rating4:facts.rating==='4'&&facts.stars===4,
        name80:facts.nameLength===80,long_text:facts.textLength>1000,
        keyboard_tab:facts.focused,focus_indicator:facts.focusOutline!=='none'||facts.focusShadow!=='none',
        no_document_overflow:facts.document<=width+1,fields_fit:facts.nameFits&&facts.textFits&&facts.gridFits,
        visible_card_after_scroll:visible,two_public_cards:await page.locator('.review-item').count()===2
      },facts);
    }
  }
  // Native valid submission by the fresh fictional author; no API substitutes.
  await page.setViewportSize({width:768,height:844});await page.goto(origin+'/ru/reviews/');await finite();
  const form=page.locator('#site-reviews form.review-form');
  await form.locator('.review-star[data-value="4"]').click();
  await form.locator('[name=author_name]').fill('F'.repeat(80));
  await form.locator('[name=text]').fill('Fictional pending review '.repeat(50));
  const before=await state();
  const post=page.waitForResponse(r=>new URL(r.url()).pathname==='/ru/review/'&&r.request().method()==='POST');
  await form.locator('button[type=submit]').click();
  const response=await post,payload=await response.json();
  await page.locator('[data-review-live]:not([hidden])').waitFor();await finite();
  const after=await state();await shot('submit-success-ru-768');
  record('native-submit',{response200:response.status()===200,payload_ok:payload.ok===true,
    success_live:await page.locator('[data-review-live]').getAttribute('role')==='status',
    composer_hidden:await form.isHidden(),pending_created:after.pending===before.pending+1&&after.author_pending===1,
    rating_name_saved:after.author_rating4===1&&after.author_name80===1,public_approved_unchanged:after.approved===2,
    only_own_review_added:after.reviews===before.reviews+1},{before,after});
  await page.reload();await finite();
  record('native-submit-reload',{approved_public_only:await page.locator('.review-item').count()===2,
    pending_not_public:!(await page.locator('.reviews-list').innerText()).includes('F'.repeat(80)),
    pending_persisted:(await state()).author_pending===1,document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)});
  // Native vote + readback, then SIMULATED delayed/aborted transport on same action.
  const reaction=page.locator('[data-review-reaction-form]').first(),action=await reaction.getAttribute('action');
  const voteurl=new URL(action,origin).href,prior=await state();
  const voteResponse=page.waitForResponse(r=>r.url()===voteurl&&r.request().method()==='POST');
  await reaction.locator('button[value="1"]').click();
  const vr=await voteResponse,vp=await vr.json();
  await page.waitForFunction(()=>document.querySelector('[data-review-reaction-form] button[value="1"]').getAttribute('aria-pressed')==='true');
  const voted=await state();
  record('native-vote',{response200:vr.status()===200,payload_ok:vp.ok===true,
    active:await reaction.locator('button[value="1"]').getAttribute('aria-pressed')==='true',
    ui_counter:Number(await reaction.locator('[data-review-like-count]').textContent())===vp.likes_count,
    db_reaction_added:voted.reactions===prior.reactions+1,approved_unchanged:voted.approved===prior.approved},{prior,voted,payload:vp});
  await page.reload();await finite();
  const same=page.locator('form[action="'+action+'"]');
  record('native-vote-reload',{active_persisted:await same.locator('button[value="1"]').getAttribute('aria-pressed')==='true',
    counter_persisted:Number(await same.locator('[data-review-like-count]').textContent())===vp.likes_count,
    db_stable:JSON.stringify(voted)===JSON.stringify(await state())});
  let release,entered;const held=new Promise(r=>release=r),caught=new Promise(r=>entered=r);let intercepted=0;
  const blocker=async route=>{intercepted++;entered();await held;await route.abort('failed');};
  await page.route(voteurl,blocker);
  await same.locator('button[value="-1"]').click();await caught;
  const pending={disabled:await same.locator('button:disabled').count()===2,
    pending_class:await same.evaluate(e=>e.classList.contains('is-pending')),
    no_db_write:JSON.stringify(voted)===JSON.stringify(await state())};
  await same.scrollIntoViewIfNeeded();await shot('SIMULATED-vote-pending-ru-768');
  release();
  await page.locator('.form-inline-notice.is-error').waitFor();
  await page.waitForFunction(a=>[...document.querySelectorAll('form[action="'+a+'"] button')].every(b=>!b.disabled),action);
  await shot('SIMULATED-vote-error-ru-768');
  record('SIMULATED-vote-delay-abort',{...pending,one_request:intercepted===1,
    error_visible:await page.locator('.form-inline-notice.is-error').isVisible(),
    buttons_reenabled:await same.locator('button:disabled').count()===0,
    no_db_write_after:JSON.stringify(voted)===JSON.stringify(await state())});
  await page.unroute(voteurl,blocker);
  // API guards supplement native actions; requests carry real session/CSRF.
  const csrf=await same.locator('[name=csrfmiddlewaretoken]').inputValue(),guardBefore=await state();
  const headers={'X-Requested-With':'XMLHttpRequest','Accept':'application/json'};
  const invalid=await page.request.post(voteurl,{form:{value:'0',csrfmiddlewaretoken:csrf},headers});
  const badcsrf=await page.request.post(voteurl,{form:{value:'1',csrfmiddlewaretoken:'invalid'},headers});
  record('API-invalid-CSRF-guards',{invalid_value400:invalid.status()===400,bad_csrf403:badcsrf.status()===403,
    no_write:JSON.stringify(guardBefore)===JSON.stringify(await state())});
  await page.goto(origin+'/qa/login/reviewer/');await page.goto(origin+'/ru/reviews/');await finite();
  const own=page.locator('.review-item').filter({has:page.locator('.review-author',{hasText:'Fictional reviewer 0'})});
  const ownform=own.locator('form'),owncsrf=await ownform.locator('[name=csrfmiddlewaretoken]').inputValue();
  const ownurl=new URL(await ownform.getAttribute('action'),origin).href,ownBefore=await state();
  const selfvote=await page.request.post(ownurl,{form:{value:'1',csrfmiddlewaretoken:owncsrf},headers});
  record('own-review-guard',{native_buttons_disabled:await ownform.locator('button:disabled').count()===2,
    server403:selfvote.status()===403,no_write:JSON.stringify(ownBefore)===JSON.stringify(await state())});
  await page.goto(origin+'/qa/login/guest/');await page.goto(origin+'/ru/reviews/');await finite();
  const guestBefore=await state();await page.locator('[data-auth-required-trigger]').filter({hasText:'Лайк'}).first().click();
  await page.locator('.toast').first().waitFor();
  const cookies=await page.context().cookies(origin),token=cookies.find(c=>c.name==='csrftoken').value;
  const guest=await page.request.post(voteurl,{form:{value:'1',csrfmiddlewaretoken:token},headers});
  const guestsubmit=await page.request.post(origin+'/ru/review/',{form:{rating:'4',text:'Fictional blocked guest',csrfmiddlewaretoken:token},headers});
  record('guest-native-API-guards',{native_auth_toast:await page.locator('.toast').first().isVisible(),
    no_composer:await page.locator('#site-reviews form.review-form').count()===0,
    vote401:guest.status()===401,submit401:guestsubmit.status()===401,
    no_write:JSON.stringify(guestBefore)===JSON.stringify(await state())});
  await shot('guest-auth-ru-768');
  return {rows,pngs,pageerrors:errors,request_failed:requests,final:await state()};
  } catch(e) { return {rows,pngs,pageerrors:errors,request_failed:requests,fatal:{message:e.message,stack:e.stack}}; }
}
