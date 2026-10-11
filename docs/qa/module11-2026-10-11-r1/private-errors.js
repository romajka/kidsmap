async original=>{
 __QA11_COMMON__
 for(const lang of ['ru','az','en']){const {c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});const path=prefix(lang)+'/place/2/',r=await p.goto('http://localhost:8828'+path),body=await p.locator('body').innerText();add('native-private-error',r.status()===404&&!body.includes('QA11 draft'),{responseStatus:r.status(),privateMarker:false},'guest',lang,width,p.url(),await shot(p,'error-private-'+lang+'-'+width));}await c.close();}return {rows};
}
