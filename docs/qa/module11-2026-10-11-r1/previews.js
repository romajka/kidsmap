async original=>{
 __QA11_COMMON__
 for(const lang of ['ru','az','en']){const {c,p}=await context('guest',lang);for(const kind of ['place','organization','activity','specialist','event'])for(const width of [360,1440]){await p.setViewportSize({width,height:950});const url='/qa/preview/'+kind+'-'+lang+'/',s=await visit(p,url);add('SIMULATED-local-social-preview',s===200&&(await geometry(p)).document<=width+2,{kind,classification:'SIMULATED own rendering of captured OG; external bots/platform NOT RUN'},'guest',lang,width,url,await shot(p,'preview-'+kind+'-'+lang+'-'+width));}await c.close();}return{rows};
}
