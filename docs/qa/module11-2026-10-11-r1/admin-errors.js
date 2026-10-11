async original=>{
 __QA11_COMMON__
 const a=await context('admin'),p=a.p;
 const r=await p.goto(B+'/admin/catalog/catalogcontentsettings/1/change/');
 const diag={status:r.status(),exception:await p.locator('pre.exception_value').allTextContents(),type:await p.locator('#summary h1').allTextContents()};
 for(const lang of ['ru','az','en'])for(const width of [360,390,768,1024,1280,1440]){await a.c.addCookies([{name:'django_language',value:lang,domain:'localhost',path:'/'}]);await p.setViewportSize({width,height:950});const response=await p.goto('http://localhost:8828/admin/catalog/catalogcontentsettings/1/change/');add('admin-SEO-config-editor',response.status()===200,{responseStatus:response.status(),exception:diag.exception,type:diag.type},'admin',lang,width,p.url(),await shot(p,'admin-SEO-config-error-'+lang+'-'+width));}
 await a.c.close();return {rows,diag};
}
