async original=>{
 __QA10_COMMON__
 const pages=['/','/about/','/faq/','/contacts/','/privacy/','/terms/','/review-rules/','/listing-rules/','/add-place/','/catalog/?q=QA10-NO-MATCH','/qa10-no-such-page/'];
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);const errors=[],failed=[];p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(B)&&r.status()>=400&&r.request().resourceType()!=='document')failed.push({url:r.url(),status:r.status()});});
 for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});
 for(const path of pages){errors.length=failed.length=0;const status=await visit(p,prefix(lang)+path),file=await shot(p,'empty-'+lang+'-'+width+'-'+path.replace(/[^a-z0-9]/gi,'_'));const g=await geometry(p),detail={http:status,geometry:g};
 add('empty-page-http',status===(path.includes('no-such')?404:200),detail,'guest',lang,width,p.url(),file);add('empty-page-no-overflow',g.document<=width+2,detail,'guest',lang,width,p.url(),file);add('empty-page-language',(await p.locator('html').getAttribute('lang')).startsWith(lang),{},'guest',lang,width,p.url(),file);add('empty-page-local-assets',failed.length===0,{failures:[...failed]},'guest',lang,width,p.url(),file);add('empty-page-js',errors.length===0,{errors:[...errors]},'guest',lang,width,p.url(),file);
 }
 }
 await c.close();}
 return{rows,diagnostics};
}
