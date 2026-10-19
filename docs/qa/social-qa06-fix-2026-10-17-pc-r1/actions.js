async (page) => {
  const origin='http://127.0.0.1:33337',rows=[],pngs=[],errors=[],failed=[];
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  const selected=async()=>await page.locator('[data-review-stars]').evaluate(p=>{
    const s=[...p.querySelectorAll('[role=radio]')];return {rating:Number(p.parentElement.querySelector('[name=rating]').value),
      checked:s.filter(e=>e.getAttribute('aria-checked')==='true').map(e=>Number(e.dataset.value)),
      tab:s.filter(e=>e.tabIndex===0).map(e=>Number(e.dataset.value)),focus:Number(document.activeElement.dataset.value||0)};
  });
  const agrees=(s,n)=>s.rating===n&&JSON.stringify(s.checked)==='['+n+']'&&JSON.stringify(s.tab)==='['+n+']';
  const shot=async n=>{const p='/mnt/c/kidsmap/.tmp/social06-pc-fix-r1/png/'+n+'.png';await page.screenshot({path:p});pngs.push(p);};
  page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));
  try {
    for(const [lang,prefix,rating,width] of [['ru','/ru',3,390],['az','',1,768],['en','/en',5,1440]]){
      await page.goto(origin+'/qa/login/'+lang+'/');await page.setViewportSize({width,height:844});
      const ssr=await page.request.get(origin+prefix+'/reviews/');
      const markup=await ssr.text();
      const ssrFacts=await page.evaluate(html=>{
        const doc=new DOMParser().parseFromString(html,'text/html'),p=doc.querySelector('[data-review-stars]');
        const radios=[...p.querySelectorAll('[role=radio]')];return {count:radios.length,
          checked:radios.filter(e=>e.getAttribute('aria-checked')==='true').map(e=>e.dataset.value),
          tab:radios.filter(e=>e.getAttribute('tabindex')==='0').map(e=>e.dataset.value),
          hidden:p.parentElement.querySelector('[name=rating]').value};
      },markup);
      await page.goto(origin+prefix+'/reviews/');await finite();
      const form=page.locator('#site-reviews form.review-form'),picker=page.locator('[data-review-stars]');
      await page.locator('.review-reactions-form').last().locator('button').last().focus();
      await page.keyboard.press('Tab');const tabEntry=await selected();
      await picker.locator('[data-value="'+rating+'"]').focus();await page.keyboard.press('Space');
      const space=await selected();
      await page.keyboard.press('Enter');const enter=await selected(),ax=await picker.ariaSnapshot();
      await picker.scrollIntoViewIfNeeded();await finite();await shot('selected-'+lang+'-'+width);
      await form.locator('[name=text]').fill('Fictional native '+lang+' rating '+rating);
      await form.locator('[name=author_name]').fill('Fictional '+lang);
      const before=await state(),action=new URL(await form.getAttribute('action'),origin).href;
      let posts=0;const onRequest=r=>{if(r.url()===action&&r.method()==='POST')posts++;};page.on('request',onRequest);
      const pending=page.waitForResponse(r=>r.url()===action&&r.request().method()==='POST');
      await form.locator('button[type=submit]').click();const response=await pending,payload=await response.json();
      const data=response.request().postData()||'';
      const expectedPart=new RegExp('name="rating"\\r?\\n\\r?\\n'+rating+'\\r?\\n');
      await page.locator('[data-review-live]:not([hidden])').waitFor();
      await page.waitForFunction(()=>document.querySelector('#site-reviews [name=rating]').value==='5'&&document.querySelector('[data-review-stars] [data-value="5"]').getAttribute('aria-checked')==='true');
      const after=await state(),reset=await selected();page.off('request',onRequest);
      await shot('submit-success-'+lang+'-'+width);
      rows.push({id:'native-submit-'+lang,checks:{
        ssr_default5:ssrFacts.count===5&&JSON.stringify(ssrFacts.checked)==='["5"]'&&JSON.stringify(ssrFacts.tab)==='["5"]'&&ssrFacts.hidden==='5',
        tab_entry_selected5:agrees(tabEntry,5)&&tabEntry.focus===5,
        space_and_enter:agrees(space,rating)&&agrees(enter,rating)&&enter.focus===rating,
        ax_selected:ax.includes('radio "'+rating+' / 5" [checked]'),
        actual_payload_rating:expectedPart.test(data),response200:response.status()===200,payload_ok:payload.ok===true,
        one_post:posts===1,pending_created:after.pending===before.pending+1&&after.reviews===before.reviews+1,
        own_rating_persisted:after.own_pending_rating===rating,approved_unchanged:after.approved===2,
        reset_semantics5:agrees(reset,5),success_hidden_composer:await form.isHidden()
      },facts:{rating,before,after,ssr:ssrFacts,ax,reset}});
      await page.reload();await finite();
      const reloaded=await state();
      rows.push({id:'native-reload-'+lang,checks:{new_form_default5:agrees(await selected(),5),
        pending_rating_persisted:reloaded.own_pending_rating===rating,
        public_projection_unchanged:await page.locator('.review-item').count()===2,
        no_overflow:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)}});
    }
    // Supplementary actual API range/CSRF guards on the last fictional author.
    const form=page.locator('#site-reviews form.review-form'),action=new URL(await form.getAttribute('action'),origin).href;
    const csrf=await form.locator('[name=csrfmiddlewaretoken]').inputValue(),before=await state();
    const headers={'X-Requested-With':'XMLHttpRequest','Accept':'application/json'};
    const zero=await page.request.post(action,{headers,form:{rating:'0',text:'Fictional rejected zero',csrfmiddlewaretoken:csrf}});
    const six=await page.request.post(action,{headers,form:{rating:'6',text:'Fictional rejected six',csrfmiddlewaretoken:csrf}});
    const bad=await page.request.post(action,{headers,form:{rating:'2',text:'Fictional blocked CSRF',csrfmiddlewaretoken:'invalid'}});
    rows.push({id:'API-range-CSRF',checks:{rating0_rejected:zero.status()===400,rating6_rejected:six.status()===400,
      csrf403:bad.status()===403,no_writes:JSON.stringify(before)===JSON.stringify(await state())}});
    // SIMULATED request held and aborted before delivery: rating2/input retained.
    await page.setViewportSize({width:390,height:844});await page.goto(origin+'/en/reviews/');await finite();
    const f=page.locator('#site-reviews form.review-form'),p=page.locator('[data-review-stars]');
    await p.locator('[data-value="2"]').click();await f.locator('[name=text]').fill('Fictional retained rating two');
    const noWriteBefore=await state();let release,entered,n=0;
    const held=new Promise(r=>release=r),caught=new Promise(r=>entered=r);
    const blocker=async route=>{n++;entered();await held;await route.abort('failed');};
    await page.route(action,blocker);await f.locator('button[type=submit]').click();await caught;
    const pendingChecks={busy:await f.getAttribute('aria-busy')==='true',disabled:await f.locator('button[type=submit]').isDisabled(),
      selected2_while_pending:agrees(await selected(),2),no_write_pending:JSON.stringify(noWriteBefore)===JSON.stringify(await state())};
    await shot('SIMULATED-submit-pending-en-390');release();
    await page.locator('[data-review-live][role=alert]:not([hidden])').waitFor();
    await page.waitForFunction(()=>!document.querySelector('#site-reviews form button[type=submit]').disabled);
    await shot('SIMULATED-submit-error-en-390');
    rows.push({id:'SIMULATED-submit-delay-abort',checks:{...pendingChecks,one_request:n===1,
      selected2_after_error:agrees(await selected(),2),text_retained:await f.locator('[name=text]').inputValue()==='Fictional retained rating two',
      button_reenabled:!(await f.locator('button[type=submit]').isDisabled()),
      no_write_after:JSON.stringify(noWriteBefore)===JSON.stringify(await state())}});
    await page.unroute(action,blocker);
    await page.goto(origin+'/qa/login/guest/');await page.goto(origin+'/ru/reviews/');await finite();
    const guestBefore=await state(),cookies=await page.context().cookies(origin),token=cookies.find(c=>c.name==='csrftoken').value;
    const guest=await page.request.post(origin+'/ru/review/',{headers,form:{rating:'3',text:'Fictional blocked guest',csrfmiddlewaretoken:token}});
    rows.push({id:'guest-guard',checks:{no_rating_group:await page.locator('[data-review-stars]').count()===0,
      no_composer:await page.locator('#site-reviews form.review-form').count()===0,
      server401:guest.status()===401,no_write:JSON.stringify(guestBefore)===JSON.stringify(await state())}});
    return {rows,pngs,pageerrors:errors,request_failed:failed,final:await state()};
  }catch(e){return {rows,pngs,pageerrors:errors,request_failed:failed,fatal:{message:e.message,stack:e.stack}};}
}
