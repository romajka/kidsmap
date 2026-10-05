async(page)=>{
const origin='http://127.0.0.1:8783',errors=[],requests=[];
page.on('pageerror',error=>errors.push({url:page.url(),message:String(error),stack:error.stack}));
await page.context().unroute('**/*');
const html=name=>'<!doctype html><html><head><meta charset="utf-8"><style>@view-transition{navigation:auto}body{font-family:sans-serif}::view-transition-old(root){animation-duration:160ms}::view-transition-new(root){animation-duration:160ms}</style></head><body><h1>QA22 CSS-only '+name+'</h1><form method="post" action="'+(name==='a'?'/b':'/a')+'"><button>Submit synthetic form</button></form></body></html>';
await page.context().route('**/*',async route=>{
 const request=route.request(),url=new URL(request.url());
 if(url.origin!==origin)return route.fulfill({status:200,body:''});
 requests.push({path:url.pathname,method:request.method()});
 if(url.pathname==='/deny')return route.fulfill({status:429,contentType:'application/json',body:'{"ok":false}'});
 if(url.pathname==='/stale')return route.fulfill({status:409,body:''});
 return route.fulfill({status:200,contentType:'text/html',body:html(url.pathname.slice(1))});
});
for(let index=0;index<8;index++){
 await page.goto(origin+'/a',{waitUntil:'networkidle'});
 const response=page.waitForResponse(response=>response.request().method()==='POST');
 const navigation=page.waitForEvent('framenavigated',{predicate:frame=>frame===page.mainFrame()});
 await page.locator('button').click();await response;await navigation;await page.waitForLoadState('networkidle');
 await page.evaluate(async()=>{for(const path of['/deny','/stale']){const response=await fetch(path,{method:'POST'});await response.text();}});
}
return{application_scripts:false,backend:false,pure_synthetic_route_fulfill:true,cycles:8,errors,requests};
}
