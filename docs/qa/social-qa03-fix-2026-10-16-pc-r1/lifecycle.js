async(page)=>{
 const item=__CASE__,phase='__PHASE__',memo=__MEMO__,origin='http://127.0.0.1:33271';
 const context=page.context(),a=context.pages()[0],url=origin+item.url;
 const b=context.pages().slice(1).filter(p=>p.url()===url).at(-1);
 if(!b)throw new Error('Missing retained conflict page');
 const state=async()=>await(await a.request.get(`${origin}/qa/state/${item.cell}/`)).json();
 const stable=s=>{const{retry_after,...rest}=s;return rest;};
 const same=(x,y)=>JSON.stringify(stable(x))===JSON.stringify(stable(y));
 const allow=route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'&&u.port==='33271'?route.continue():route.abort('blockedbyclient');};
 const pageerrors=[],console_errors=[],posts=[];
 const onError=e=>pageerrors.push({name:e.name,message:e.message});
 const onConsole=m=>{if(m.type()==='error')console_errors.push(m.text());};
 const onResponse=r=>{if(r.request().method()==='POST')posts.push({status:r.status(),at_ms:Date.now()});};
 for(const p of [a,b]){p.on('pageerror',onError);p.on('console',onConsole);p.on('response',onResponse);}
 try{
  const before=await state();
  if((phase==='raceprep'||phase==='retry'||(phase==='race'&&item.kind==='place'))&&before.retry_after>0)return{item,phase,stage:'WAIT_REAL_COOLDOWN',retry_after:before.retry_after};
  if(phase==='raceprep'){
   const reloadDeferred=await b.locator('[data-review-reload]').count()===0;
   let reloadFocused=null,focusStyle=null,loaded;
   if(reloadDeferred){loaded=await b.goto(url);}else{
    await b.getByRole('textbox').focus();await b.keyboard.press('Tab');await b.keyboard.press('Tab');
    reloadFocused=await b.evaluate(()=>document.activeElement.matches('[data-review-reload]'));
    focusStyle=await b.locator('[data-review-reload]').evaluate(el=>{const s=getComputedStyle(el);return{outline:s.outlineStyle,width:s.outlineWidth,shadow:s.boxShadow};});
    [loaded]=await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
   }
   const reloaded={rating:await b.getByRole('combobox').inputValue(),text:await b.getByRole('textbox').inputValue(),state:await state()};
   const draft='<script>window.SOCIAL03_EXECUTED=true</script> & <b>literal</b>\n'+('Long fictional draft — Ə Ö İ Ş Ü Ж Я & "quotes". '.repeat(25));
   await b.getByRole('combobox').selectOption('2');await b.getByRole('textbox').fill(draft);
   await a.goto(url);await a.getByRole('combobox').selectOption('1');await a.getByRole('textbox').fill('Newer private candidate C');
   const c_submitted_at_ms=Date.now();
   await Promise.all([a.waitForNavigation({waitUntil:'domcontentloaded'}),a.locator('form[data-review-edit] button').click()]);
   const afterC=await state();
   const checks={reload_no_write:same(before,reloaded.state),
    reload_get_readback:loaded.status()===200&&reloaded.rating===String(before.candidate_rating)&&reloaded.text===before.candidate_text,
    native_c_saved:afterC.candidate_rating===1&&afterC.candidate_text==='Newer private candidate C'&&afterC.revisions===before.revisions+1&&posts.some(p=>p.status===302)};
   if(!reloadDeferred){checks.reload_reached_by_tab=reloadFocused;checks.reload_focus_visible=(focusStyle.outline!=='none'&&parseFloat(focusStyle.width)>0)||focusStyle.shadow!=='none';}
   return{item,phase,stage:'prepared',checks,before,afterC,c_submitted_at_ms,reloadDeferred,focusStyle,posts,pageerrors,console_errors};
  }
  if(phase==='race'){
   const afterC=await state();
   if(afterC.candidate_id!==memo.afterC.candidate_id)throw new Error('Unexpected C drift');
   const draft='<script>window.SOCIAL03_EXECUTED=true</script> & <b>literal</b>\n'+('Long fictional draft — Ə Ö İ Ş Ü Ж Я & "quotes". '.repeat(25));
   await b.getByRole('textbox').focus();await b.keyboard.press('Tab');
   const [conflict]=await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
   const after=await state();
   const checks={...memo.checks,
    new_race_409:conflict.status()===409,new_race_no_write:same(afterC,after),
    draft_script_long_retained:await b.getByRole('textbox').inputValue()===draft.trim(),
    script_not_executed:await b.evaluate(()=>window.SOCIAL03_EXECUTED!==true&&!Array.from(document.scripts).some(s=>s.textContent.includes('window.SOCIAL03_EXECUTED'))),
    latest_c_displayed:(await b.locator('[data-review-latest]').innerText()).trim()==='Newer private candidate C',
    fresh_c_token:await b.locator('form[data-review-edit] [name=expected_revision_id]').inputValue()===String(after.candidate_id),
    public_preserved:after.public.average===4&&after.public.count===1,
    long_form_no_overflow:await b.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)
   };
   const png=`/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/png/race-${item.kind}-${item.lang}-${item.width}.png`;
   await b.screenshot({path:png,fullPage:true});
   if(memo.reloadDeferred){
    await b.getByRole('textbox').focus();await b.keyboard.press('Tab');await b.keyboard.press('Tab');
    checks.reload_reached_by_tab=await b.evaluate(()=>document.activeElement.matches('[data-review-reload]'));
    checks.reload_focus_visible=await b.locator('[data-review-reload]').evaluate(el=>{const s=getComputedStyle(el);return(s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0)||s.boxShadow!=='none';});
    const [loaded]=await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
    checks.reload_discards_b_for_latest=loaded.status()===200&&await b.getByRole('combobox').inputValue()==='1'&&await b.getByRole('textbox').inputValue()==='Newer private candidate C';
    checks.deferred_reload_no_write=same(after,await state());
    await b.getByRole('combobox').selectOption('2');
   }
   await b.getByRole('textbox').fill('Unsaved draft B');
   return{item,phase,stage:'complete',checks,before:memo.before,afterC,after,c_submitted_at_ms:memo.c_submitted_at_ms,focusStyle:memo.focusStyle,posts,pageerrors,console_errors,png};
  }
  if(phase==='guards'){
   const checks={},contexts=[];
   try{
    for(const role of ['outsider','guest']){
     const other=await context.browser().newContext({viewport:{width:item.width,height:item.width<768?844:900},serviceWorkers:'block'});contexts.push(other);
     await other.route('**/*',allow);
     const p=await other.newPage();p.on('pageerror',onError);p.on('console',onConsole);
     if(role==='outsider')await p.goto(origin+'/qa/login/outsider/');
     await p.goto(url);
     const body=await p.locator('body').innerText();
     checks[role+'_private_not_disclosed']=!body.includes('Newer private candidate C')&&!body.includes('Latest private candidate A')&&!body.includes('Unsaved draft B')&&!body.includes('SOCIAL03_EXECUTED');
     checks[role+'_public_four_visible']=body.includes('Public current four');
     checks[role+'_no_conflict_payload']=await p.locator('[data-review-conflict]').count()===0;
     if(role==='outsider'){
      checks.outsider_empty_editor=await p.getByRole('combobox').inputValue()==='';
      const csrf=await p.locator('form[data-review-edit] [name=csrfmiddlewaretoken]').inputValue();
      const response=await other.request.post(url,{form:{rating:'2',text:'Foreign attempt',expected_revision_id:String(before.candidate_id),csrfmiddlewaretoken:csrf}});
      const html=await response.text();
      checks.foreign_token_409=response.status()===409;
      checks.foreign_conflict_private_hidden=!html.includes('Newer private candidate C')&&!html.includes('Latest private candidate A');
     }
    }
    const noCsrf=await context.request.post(url,{form:{rating:'2',text:'Missing CSRF attempt',expected_revision_id:String(before.candidate_id)}});
    checks.missing_csrf_403=noCsrf.status()===403;
    const after=await state();checks.guards_no_write=same(before,after);
    return{item,phase,stage:'complete',checks,before,after,pageerrors,console_errors};
   }finally{for(const other of contexts)await other.close();}
  }
  if(phase==='retry'){
   const pendingBefore=await state();
   let loading=null;
   if(item.lang==='ru'&&((item.kind==='place'&&item.width===1440)||(item.kind!=='place'&&item.width===390))){
    const draftBefore=await b.getByRole('textbox').inputValue();
    loading={simulated:'finite500ms POST transport dispatch delay',draft_before_submit:draftBefore,submitted_payload:false,server_unchanged:false};
    const pattern=url+'*';
    const hold=async route=>{if(route.request().method()==='POST'){
      loading.submitted_payload=new URLSearchParams(route.request().postData()).get('text')==='Unsaved draft B';
      loading.server_unchanged=same(pendingBefore,await state());
      await new Promise(resolve=>setTimeout(resolve,500));
    }await route.continue();};
    await b.route(pattern,hold);
    await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.locator('form[data-review-edit] button').click()]);
    await b.unroute(pattern,hold);
   }else{
    await b.getByRole('textbox').focus();await b.keyboard.press('Tab');
    await Promise.all([b.waitForNavigation({waitUntil:'domcontentloaded'}),b.keyboard.press('Enter')]);
   }
   const b_submitted_at_ms=Date.now(),pending=await state();
   const checks={
    cooldown_expired_before_explicit_action:pendingBefore.retry_after===0,
    explicit_single_b_post:posts.filter(p=>p.status===302).length===1,
    pending_b_saved:pending.candidate_rating===2&&pending.candidate_text==='Unsaved draft B'&&pending.revisions===before.revisions+1,
    public_four_until_approval:pending.public.average===4&&pending.public.count===1&&pending.current_id===before.current_id,
    b_readback_rating:await b.getByRole('combobox').inputValue()==='2',
    pending_status_visible:await b.locator('[data-candidate-status]').count()===1
   };
   if(loading){checks.loading_keeps_draft=loading.draft_before_submit==='Unsaved draft B'&&loading.submitted_payload;checks.loading_no_early_write=loading.server_unchanged;}
   const reviewer=await context.browser().newContext({viewport:{width:item.width,height:item.width<768?844:900},serviceWorkers:'block'});
   try{
    await reviewer.route('**/*',allow);const p=await reviewer.newPage();p.on('pageerror',onError);p.on('console',onConsole);
    await p.goto(origin+'/qa/login/reviewer/');await p.goto(url);
    const approve=p.locator(`article[data-candidate-id="${pending.candidate_id}"] form[action$="/approve/"] button`);
    await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),approve.click()]);
    const approved=await state();
    checks.approval_moves_one_public_contribution=approved.candidate_id===null&&approved.current_id===pending.candidate_id&&approved.public.average===2&&approved.public.count===1&&approved.revisions===pending.revisions;
    await b.reload({waitUntil:'domcontentloaded'});
    checks.approved_author_readback=await b.getByRole('combobox').inputValue()==='2'&&await b.getByRole('textbox').inputValue()==='Unsaved draft B';
    checks.old_private_c_not_public=!(await b.locator('[data-review-id]').innerText()).includes('Newer private candidate C');
    const png=`/mnt/c/kidsmap/.tmp/social03-pc-fix-r1/png/approved-${item.kind}-${item.lang}-${item.width}.png`;
    await b.screenshot({path:png,fullPage:true});
    return{item,phase,stage:'complete',checks,before,pending,approved,b_submitted_at_ms,loading,posts,pageerrors,console_errors,png};
   }finally{await reviewer.close();}
  }
  throw new Error('Unknown lifecycle phase');
 }finally{for(const p of [a,b]){p.off('pageerror',onError);p.off('console',onConsole);p.off('response',onResponse);}}
}
