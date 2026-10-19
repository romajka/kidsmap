async (page) => {
 const origin='http://127.0.0.1:33348',rows=[],errors=[],failures=[],consoleErrors=[];
 page.on('console',m=>{if(m.type()==='error')consoleErrors.push({text:m.text(),url:m.location().url});});page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failures.push(r.url()));
 const targets=[
  {
    "variant": "escaping",
    "pk": 4,
    "reviews": "/reviews/activity/target/4/",
    "names": {
      "az": "<script>fictional()</script> & class",
      "ru": "<script>fictional()</script> & class",
      "en": "<script>fictional()</script> & class"
    }
  },
  {
    "variant": "empty",
    "pk": 5,
    "reviews": "/reviews/activity/target/5/",
    "names": {
      "az": "",
      "ru": "",
      "en": ""
    }
  },
  {
    "variant": "hidden",
    "pk": 6,
    "reviews": "/reviews/activity/target/6/",
    "names": {
      "az": "",
      "ru": "",
      "en": ""
    }
  },
  {
    "variant": "liveprogram",
    "pk": 7,
    "reviews": "/reviews/activity/target/7/",
    "names": {
      "az": "Live AZ",
      "ru": "Live RU",
      "en": "Live EN"
    }
  }
];
 const state=async()=>await(await page.request.get(origin+'/qa/state/')).json();
 const before=await state();
 for(const target of targets){
  const roles=target.variant==='hidden'?['guest','author','staff']:['guest','author'];
  for(const role of roles)for(const lang of ['az','ru','en']){
   const prefix=lang==='az'?'':'/'+lang,headingPrefix={az:'Rəylər:',ru:'Отзывы:',en:'Reviews:'}[lang];
   await page.goto(origin+'/qa/login/'+role+'/');await page.setViewportSize({width:390,height:844});
   const response=await page.goto(origin+prefix+target.reviews);let checks={},facts={status:response.status()};
   if(target.variant==='hidden'&&role!=='staff')checks={hidden_404:response.status()===404};
   else{
    const heading=(await page.locator('h1').textContent()).trim(),title=await page.title();
    const reloaded=await page.reload();
    checks={status200:response.status()===200&&reloaded.status()===200,
     canonical_heading:heading===(headingPrefix+' '+target.names[lang]).trim(),
     no_object_id:!heading.includes('Activity object ('),reload_stable:(await page.locator('h1').textContent()).trim()===heading,
     no_script_element:await page.locator('h1 script').count()===0,
     no_private_draft:!heading.includes('PRIVATE DRAFT')&&!title.includes('PRIVATE DRAFT'),
     document_fits:await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)};
    facts={...facts,heading,title};
    const png='/mnt/c/kidsmap/.tmp/social07-pc-fix-r1/png/edge-'+target.variant+'-'+role+'-'+lang+'.png';
    await page.locator('h1').scrollIntoViewIfNeeded();await page.screenshot({path:png});facts.png=png;
   }
   rows.push({id:target.variant+'-'+role+'-'+lang,checks,facts});
  }
 }
 const after=await state();const expected404=new Set(targets.filter(t=>t.variant==='hidden').flatMap(t=>['','/ru','/en'].map(p=>origin+p+t.reviews)));const unexpectedConsole=consoleErrors.filter(m=>!(m.text.includes('404')&&expected404.has(m.url)));rows.push({id:'aggregate',checks:{no_business_write:JSON.stringify(before)===JSON.stringify(after),no_pageerrors:errors.length===0,no_requestfailed:failures.length===0,no_unexpected_console_error:unexpectedConsole.length===0},facts:{before,after}});
 return {rows,pageerrors:errors,requestfailed:failures,consoleErrors,unexpectedConsole};
}

