async (page) => {
 const base='http://127.0.0.1:33780',mode='disabled',rows=[],errors=[],pageerrors=[];
 await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());page.on('pageerror',e=>pageerrors.push(String(e)));
 function ratio(fg,bg){const l=c=>{const a=c.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4});return .2126*a[0]+.7152*a[1]+.0722*a[2]};const a=l(fg),b=l(bg);return(Math.max(a,b)+.05)/(Math.min(a,b)+.05)}
 try{
  await page.goto(base+'/qa/m12/login/admin/');const initial=await (await page.request.get(base+'/qa/m12/state/')).json();
  for(const lang of ['az','ru','en']){
   await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);
   for(const width of [360,390,768,1024,1280,1440]){
    await page.setViewportSize({width,height:900});const response=await page.goto(base+'/admin/catalog/siteanalytics/?period=90');
    const info=await page.evaluate(()=>{const root=document.querySelector('.km-statistics-page');const notice=root?.querySelector('[role=status]');const active=root?.querySelector('.km-period-selector .is-active');function colors(e){if(!e)return null;let n=e,bg='rgb(255,255,255)';while(n){const c=getComputedStyle(n).backgroundColor;if(c!=='rgba(0, 0, 0, 0)'&&c!=='transparent'){bg=c;break}n=n.parentElement}return{color:getComputedStyle(e).color,background:bg}}return{state:root?.dataset.analyticsState,values:[...document.querySelectorAll('[data-kpi-value]')].map(e=>e.textContent.trim()),notice:notice?{height:notice.getBoundingClientRect().height,...colors(notice)}:null,active:colors(active),loaded:!!root?.querySelector('time'),overflow:document.documentElement.scrollWidth>innerWidth+1,main:document.querySelectorAll('main').length,canvas:!!document.querySelector('#km-visits-chart'),text:root?.textContent||''}});
    const ready=['filled','empty'].includes(mode),expectedState=ready?'ready':mode==='disabled'?'disabled':'unavailable',expected=mode==='filled'?['90','91','92']:mode==='empty'?['0','0','0']:['—','—','—'];
    const checks={http200:response.status()===200,state:info.state===expectedState,kpi:JSON.stringify(info.values)===JSON.stringify(expected),successful_timestamp_only:info.loaded===ready,chart_only_when_loaded:info.canvas===(mode==='filled'),safe_error:!info.text.includes('FICTIONAL_PROVIDER_SECRET_MARKER'),no_overflow:!info.overflow,active_period_contrast:!!info.active&&ratio(info.active.color,info.active.background)>=4.5,notice_compact:ready||!!info.notice&&info.notice.height<=120,notice_contrast:ready||!!info.notice&&ratio(info.notice.color,info.notice.background)>=4.5};
    if(lang==='az')checks.az_labels=info.text.includes('Aktiv istifadəçilər')&&info.text.includes('Səhifə baxışları')&&!/[А-Яа-яЁё]/.test(info.text);
    rows.push({id:mode+'-'+lang+'-'+width,mode,lang,width,role:'admin',checks,geometry:{notice:info.notice,active:info.active}});
    if([360,1440].includes(width))await page.screenshot({path:'/mnt/c/kidsmap/docs/qa/module12-repair-2026-10-18-pc-r1/png/report-'+mode+'-'+lang+'-'+width+'.png',fullPage:true});
   }
  }
  const final=await(await page.request.get(base+'/qa/m12/state/')).json();rows.push({id:mode+'-read-only',checks:{entities_unchanged:initial.sha===final.sha,events_unchanged:initial.events_total===final.events_total,media_unchanged:JSON.stringify(initial.media)===JSON.stringify(final.media)}});
 }catch(e){errors.push(String(e))}
 return{rows,errors,pageerrors,provider:mode==='disabled'?'disabled; no Google connection':'Explicitly SIMULATED GA snapshot: '+mode};
}
