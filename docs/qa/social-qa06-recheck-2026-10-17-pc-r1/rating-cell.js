async (page) => {
  const item=__ITEM__,origin='http://127.0.0.1:33336',errors=[],http=[],failed=[];
  const onError=e=>errors.push(e.message),onHTTP=r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()});},onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  page.on('pageerror',onError);page.on('response',onHTTP);page.on('requestfailed',onFailed);
  const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  await page.setViewportSize({width:item.width,height:844});await page.goto(origin+'/qa/login/author/');
  const before=await state(),response=await page.goto(origin+item.url);await finite();
  const picker=page.locator('[data-review-stars]'),name=page.locator('#site-reviews [name=author_name]');
  const snapshot=async()=>await picker.evaluate(e=>{
    const stars=[...e.querySelectorAll('.review-star')],input=e.parentElement.querySelector('[name=rating]');
    return {rating:input.value,active:stars.filter(s=>s.classList.contains('active')).map(s=>s.dataset.value),
      groupRole:e.getAttribute('role'),groupName:e.getAttribute('aria-label'),
      roles:stars.map(s=>s.getAttribute('role')),checked:stars.map(s=>s.getAttribute('aria-checked')),
      names:stars.map(s=>s.getAttribute('aria-label')),tabIndices:stars.map(s=>s.tabIndex),
      focused:stars.find(s=>s===document.activeElement)?.dataset.value||null};
  });
  const semantic=s=>s.roles.every(v=>v==='radio')&&s.checked.filter(v=>v==='true').length===1&&s.checked[Number(s.rating)-1]==='true'&&s.checked.every(v=>v==='true'||v==='false');
  const initial=await snapshot();
  await picker.locator('[data-value="3"]').focus();await page.keyboard.press('Space');
  const space=await snapshot(),spaceAX=await picker.ariaSnapshot();
  await picker.scrollIntoViewIfNeeded();await finite();
  const spacePNG='/mnt/c/kidsmap/.tmp/social06-pc-plan-r1/png/space-'+item.lang+'-'+item.width+'.png';
  await page.screenshot({path:spacePNG});
  await picker.locator('[data-value="3"]').focus();await page.keyboard.press('Tab');
  const tabExits=await name.evaluate(e=>e===document.activeElement);
  await name.focus();await page.keyboard.press('Shift+Tab');
  const shiftBack=await snapshot();
  await picker.locator('[data-value="3"]').focus();await page.keyboard.press('Enter');
  const enter=await snapshot(),enterAX=await picker.ariaSnapshot();
  const enterPNG='/mnt/c/kidsmap/.tmp/social06-pc-plan-r1/png/enter-'+item.lang+'-'+item.width+'.png';
  await page.screenshot({path:enterPNG});
  await picker.locator('[data-value="5"]').hover();
  const hover=await snapshot();
  await name.hover();
  const restoredHover=await snapshot();
  await picker.locator('[data-value="3"]').focus();await page.keyboard.press('ArrowRight');
  const arrow=await snapshot(),after=await state();
  const form=page.locator('#site-reviews form.review-form');
  const controls={http200:response.status()===200,five_stars:initial.roles.length===5,
    group_named:initial.groupRole==='radiogroup'&&initial.groupName===item.groupName,
    default5:initial.rating==='5'&&initial.active.length===5,
    space_native_changes_rating3:space.rating==='3'&&space.active.length===3,
    enter_native_changes_rating3:enter.rating==='3'&&enter.active.length===3,
    native_focus_retained:space.focused==='3'&&enter.focused==='3',
    hover_not_committed:hover.rating==='3'&&restoredHover.rating==='3'&&restoredHover.active.length===3,
    csrf_post:await form.locator('[name=csrfmiddlewaretoken]').count()===1&&await form.getAttribute('method')==='post',
    document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),
    no_business_write:JSON.stringify(before)===JSON.stringify(after)};
  const source={default_single_selected_radio:semantic(initial),space_selected_radio_matches_hidden:semantic(space),
    enter_selected_radio_matches_hidden:semantic(enter),single_tab_stop:space.tabIndices.filter(v=>v===0).length===1,
    scale_names:space.names.every((s,i)=>s===(i+1)+' / 5'),
    tab_exits_group:tabExits,shift_tab_returns_selected:shiftBack.focused==='3',arrow_selects_next:arrow.rating==='4'&&arrow.focused==='4'};
  page.off('pageerror',onError);page.off('response',onHTTP);page.off('requestfailed',onFailed);
  return {item,controls,source,facts:{initial,space,spaceAX,enter,enterAX,shiftBack,arrow},before,after,
    pngs:[spacePNG,enterPNG],pageerrors:errors,http_failures:http,request_failed:failed};
}
