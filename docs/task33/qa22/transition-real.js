async(page)=>{
const origin='http://127.0.0.1:8783',errors=[];
page.on('pageerror',error=>errors.push({url:page.url(),message:String(error),stack:error.stack}));
await page.context().unroute('**/*');
await page.context().route('**/*',route=>route.request().url().startsWith(origin+'/')?route.continue():route.fulfill({status:200,body:''}));
for(let index=0;index<8;index++){
 await page.goto(origin+'/a',{waitUntil:'networkidle'});
 const response=page.waitForResponse(response=>response.request().method()==='POST');
 const navigation=page.waitForEvent('framenavigated',{predicate:frame=>frame===page.mainFrame()});
 await page.locator('button').click();await response;await navigation;await page.waitForLoadState('networkidle');
 await page.evaluate(async()=>{for(const path of['/deny','/stale']){const response=await fetch(path,{method:'POST'});await response.text();}});
}
return{application_scripts:false,django:false,database:false,real_loopback_http:true,external_css:'unchanged static/css/motion.css',native_post_redirect:302,cycles:8,errors};
}
