async (page) => {
  const item=__CASE__, mode='__MODE__';
  const origin='http://127.0.0.1:33271',context=page.context();
  const a=context.pages()[0];
  let b=context.pages().slice(1).find(p=>p.url()===origin+item.url);
  const errors=[],consoleErrors=[],failed=[],posts=[];
  const onError=e=>errors.push({name:e.name,message:e.message});
  const onConsole=m=>{if(m.type()==='error')consoleErrors.push(m.text());};
  const onFailed=r=>failed.push({url:r.url(),error:r.failure()?.errorText});
  const onResponse=r=>{if(r.request().method()==='POST')posts.push({status:r.status(),url:r.url()});};
  if(mode!=='finish') {
    const ready=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
    if(ready.retry_after>0)return{item,stage:'WAIT_REAL_COOLDOWN',retry_after:ready.retry_after};
    if(b)await b.close();
    await a.setViewportSize({width:item.width,height:item.width<768?844:900});
    await a.goto(origin+item.url);
    if(await a.getByRole('combobox').inputValue()!==(mode==='recheck'?'5':'4'))throw new Error('Fixture rating mismatch');
    b=await context.newPage();
    await b.setViewportSize({width:item.width,height:item.width<768?844:900});
    await b.goto(origin+item.url);
    await b.getByRole('combobox').selectOption('2');
    await b.getByRole('textbox').fill('Unsaved draft B');
  }
  for(const p of [a,b]) {p.on('pageerror',onError);p.on('console',onConsole);p.on('requestfailed',onFailed);p.on('response',onResponse);}
  try {
    if(mode!=='finish') {
      const prior=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
      await a.getByRole('combobox').selectOption('5');
      await a.getByRole('textbox').fill('Latest private candidate A');
      await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('form[data-review-edit] button').click()]);
      const saved=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
      if(!posts.some(p=>p.status===302)||saved.candidate_id===prior.candidate_id)throw new Error('A POST did not create a new candidate');
    }
    const before=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
    if(before.candidate_rating!==5 || before.candidate_text!=='Latest private candidate A')throw new Error('A submit did not save expected candidate');
    if(mode==='prep')return {item,stage:'A-prepared-B-open',before,posts,pageerrors:errors};
    if(item.kind==='place'&&before.retry_after>0)return {item,stage:'WAIT_REAL_COOLDOWN',retry_after:before.retry_after};
    await b.getByRole('textbox').focus();
    await b.keyboard.press('Tab');
    const keyboardSubmit=await b.evaluate(()=>document.activeElement.tagName==='BUTTON');
    const [response]=await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
    if(response.status()!==409)return{item,stage:'UNEXPECTED_B_STATUS',status:response.status(),posts};
    await b.waitForLoadState('load');
    const initialFocus=await b.evaluate(()=>document.activeElement.id);
    const after=await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
    const stable=s=>{const {retry_after,...rest}=s;return rest;};
    const ui=await b.evaluate(()=>{
      const form=document.querySelector('form[data-review-edit]'),text=form?.querySelector('textarea'),rating=form?.querySelector('select');
      const alert=document.querySelector('[data-review-conflict]');
      const rgb=s=>(s.match(/[\d.]+/g)||[]).slice(0,3).map(Number);
      const luminance=values=>values.map(v=>{v/=255;return v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[0.2126,0.7152,0.0722][i],0);
      const message=document.querySelector('#review-conflict-message');
      let parent=message,bg='rgb(255,255,255)';
      while(parent){const color=getComputedStyle(parent).backgroundColor;if(color!=='rgba(0, 0, 0, 0)'&&color!=='transparent'){bg=color;break;}parent=parent.parentElement;}
      const fg=message?getComputedStyle(message).color:'rgb(0,0,0)',l1=luminance(rgb(fg)),l2=luminance(rgb(bg));
      return {editor:!!form,text:text?.value,rating:rating?.value,token:form?.querySelector('[name=expected_revision_id]')?.value,
        latest:document.querySelector('[data-review-latest]')?.textContent,
        navigation:!!document.querySelector('header a'),alert:alert?.getAttribute('role'),
        described:text?.getAttribute('aria-describedby')==='review-conflict-message'&&rating?.getAttribute('aria-describedby')==='review-conflict-message',
        labels:!!text?.labels?.length&&!!rating?.labels?.length,
        no_overflow:document.documentElement.scrollWidth<=innerWidth,
        contrast:(Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05),
        reload:document.querySelector('[data-review-reload]')?.textContent,
        bodyText:document.body.textContent};
    });
    const checks={
      actual409:response.status()===409&&posts.some(p=>p.status===409),
      no_write:JSON.stringify(stable(before))===JSON.stringify(stable(after)),
      current_public_preserved:after.current_rating===4&&after.public.average===4&&after.public.count===1,
      candidate_a_preserved:after.candidate_rating===5&&after.candidate_text==='Latest private candidate A',
      editor_b_rating_text:ui.editor&&ui.rating==='2'&&ui.text==='Unsaved draft B',
      latest_a_visible:ui.latest?.trim()==='Latest private candidate A',fresh_cas:ui.token===String(after.candidate_id),
      navigation:ui.navigation,alert:ui.alert==='alert',labels:ui.labels,field_error_description:ui.described,
      initial_focus:initialFocus==='review-text',keyboard_submit:keyboardSubmit,no_horizontal_overflow:ui.no_overflow,
      message_contrast:ui.contrast>=4.5,reload_warns:!!ui.reload&&ui.reload.includes(item.lang==='ru'?'сброшен':item.lang==='en'?'discard':'silinəcək')
    };
    const hitChecks={};
    for(const [name,selector] of [['message','#review-conflict-message'],['textarea','#review-text'],['submit','form[data-review-edit] button'],['reload','[data-review-reload]']]){
      const locator=b.locator(selector);
      await locator.scrollIntoViewIfNeeded();
      hitChecks[name]=await locator.evaluate(el=>[...el.getClientRects()].every(r=>{const x=r.left+r.width/2,y=r.top+r.height/2;const hit=document.elementFromPoint(x,y);return r.left>=-1&&r.right<=innerWidth+1&&r.top>=-1&&r.bottom<=innerHeight+1&&(el===hit||el.contains(hit));}));
    }
    checks.controls_scroll_reachable=Object.values(hitChecks).every(Boolean);
    const png=`/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/png/conflict-${item.kind}-${item.lang}-${item.width}.png`;
    await b.screenshot({path:png,fullPage:true});
    const row={item,stage:'conflict',status:response.status(),checks,hitChecks,contrast:ui.contrast,before,after,
      initial_focus:initialFocus,pageerrors:errors,console_errors:consoleErrors,request_failed:failed,posts,png,browser:context.browser().version()};
    if(![390,1440].includes(item.width))await b.close();
    return row;
  }finally{for(const p of [a,b]){p.off('pageerror',onError);p.off('console',onConsole);p.off('requestfailed',onFailed);p.off('response',onResponse);}}
}
