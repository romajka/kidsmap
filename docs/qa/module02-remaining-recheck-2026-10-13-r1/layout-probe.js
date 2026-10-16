async(page)=>{
 const B='__BASE__',ROOT='__HERE__',rows=[];
 for(const lang of ['ru','az','en']){
  await page.context().addCookies([{name:'django_language',value:lang,url:B}]);
  for(const width of [360,390,768,1024,1280,1440]){
   await page.setViewportSize({width,height:950});await page.goto(B+'/admin/catalog/place/?q=QA02+LOCAL+BULK');
   await page.addStyleTag({content:'.km-toolbar #changelist-search.km-search-form {flex-wrap:wrap!important;}'});
   await page.waitForTimeout(150);
   for(const sidebar of ['default','toggled']){
    if(sidebar==='toggled'){await page.locator('[data-widget=pushmenu]').first().click();await page.waitForTimeout(350);}
    const g=await page.evaluate(()=>{const f=document.querySelector('#changelist-search');return{viewport:innerWidth,document:document.documentElement.scrollWidth,formWidth:f.getBoundingClientRect().width,formScroll:f.scrollWidth,wrap:getComputedStyle(f).flexWrap,bodyClasses:document.body.className};});
    rows.push({lang,width,sidebar,geometry:g,status:g.document<=width+1&&g.formScroll<=g.formWidth+1?'PASS':'FAIL'});
   }
   if(width===1024){const screenshot='screenshots/'+lang+'-1024-proposed-wrap.png';await page.screenshot({path:ROOT+'/'+screenshot});rows[rows.length-1].screenshot=screenshot;}
  }
 }
 return{mode:'QA ONLY temporary addStyleTag; application unchanged',rows};
}
