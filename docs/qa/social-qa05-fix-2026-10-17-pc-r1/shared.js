async (page) => {
  const origin='http://127.0.0.1:33326',rows=[],errors=[],http=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('response',r=>{if(r.status()>=400)http.push({url:r.url(),status:r.status()});});
  const finite=async()=>{await page.evaluate(()=>document.fonts.ready);await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running'&&Number.isFinite(a.effect?.getComputedTiming().endTime)).map(a=>a.finished.catch(()=>{}))));};
  await page.goto(origin+'/qa/login/author/');
  try {
    for(const kind of ['place','activity','specialist','event']){
      for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']]){
        for(const width of [390,768,1440]){
          await page.setViewportSize({width,height:844});
          const response=await page.goto(origin+prefix+'/reviews/'+kind+'/target/1/');
          await finite();await page.locator('#review-text').scrollIntoViewIfNeeded();await finite();
          const facts=await page.evaluate(()=>{
            const e=document.querySelector('#review-text'),r=e.getBoundingClientRect();
            return {document:document.documentElement.scrollWidth,width:innerWidth,heading:document.querySelector('h1').textContent,
              fieldFits:r.left>=-1&&r.right<=innerWidth+1,fieldVisible:r.top<innerHeight&&r.bottom>0,
              siteScopedRulesMatch:document.querySelectorAll('.site-reviews-page .review-form-grid').length,
              csrf:Boolean(e.form.querySelector('[name=csrfmiddlewaretoken]'))};
          });
          const png='/mnt/c/kidsmap/.tmp/social05-pc-fix-r1/png/shared-'+kind+'-'+lang+'-'+width+'.png';
          await page.screenshot({path:png});
          rows.push({kind,lang,width,png,facts,checks:{status200:response.status()===200,
            target_heading:facts.heading.includes('Fictional shared '+kind),document_fits:facts.document<=width+1,
            textarea_fits:facts.fieldFits,textarea_visible:facts.fieldVisible,
            site_rules_not_matched:facts.siteScopedRulesMatch===0,csrf:facts.csrf}});
        }
      }
    }
    return {rows,pageerrors:errors,http_failures:http};
  }catch(e){return {rows,pageerrors:errors,http_failures:http,fatal:{message:e.message}};}
}
