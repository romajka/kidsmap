async original=>{
 __QA10_COMMON__
 const paths=['/','/about/','/contacts/','/catalog/?q=QA10-NO-MATCH'];
 const publicReads=[];
 for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});
 for(const path of paths){const http=await visit(p,prefix(lang)+path),ss=await shot(p,'filled-'+lang+'-'+width+'-'+path.replace(/[^a-z0-9]/gi,'_')),g=await geometry(p),text=await p.locator('body').innerText(),s=(await state(p)).settings;
 add('filled-page-http',http===200,{},'guest',lang,width,p.url(),ss);add('filled-page-no-overflow',g.document<=width+2,{geometry:g},'guest',lang,width,p.url(),ss);
 add('branding-header',await p.locator('.km-brand-title').first().innerText()===s.brand_name,{},'guest',lang,width,p.url(),ss);
 add('footer-updated-email',text.includes(s.footer_email),{},'guest',lang,width,p.url(),ss);add('footer-updated-phone',text.includes(s.footer_phone),{},'guest',lang,width,p.url(),ss);
 if(path==='/'){const copy=await p.locator('.home-hero-copy').innerText();add('hero-saved-title',copy.includes(s['home_title_'+lang]),{},'guest',lang,width,p.url(),ss);add('hero-saved-subtitle',copy.includes(s['home_subtitle_'+lang]),{},'guest',lang,width,p.url(),ss);add('hero-saved-cta',copy.includes(s['home_cta_text_'+lang]),{stored:s['home_cta_text_'+lang],actual:await p.locator('.home-redesign-primary').innerText()},'guest',lang,width,p.url(),ss);add('hero-saved-placeholder',(await p.locator('#home-hero-search-input').getAttribute('placeholder'))===s['home_search_placeholder_'+lang],{stored:s['home_search_placeholder_'+lang],actual:await p.locator('#home-hero-search-input').getAttribute('placeholder')},'guest',lang,width,p.url(),ss);add('hero-saved-search-label',text.includes(s['home_search_label_'+lang]),{},'guest',lang,width,p.url(),ss);add('decor-off',await p.locator('.hero-cloud').count()===0,{},'guest',lang,width,p.url(),ss);
 const imageInfo=await p.evaluate(()=>Array.from(document.querySelectorAll('body,header,footer,.home-hero,.home-hero *')).map(e=>({tag:e.tagName,cls:e.className,bg:getComputedStyle(e).backgroundImage,src:e.getAttribute('src')})).filter(x=>x.bg.includes('url')||x.src));
 const expected=width<768?s.home_hero_mobile_image:s.home_hero_image;add('home-uploaded-background-used',imageInfo.some(x=>(x.bg+' '+x.src).includes(expected)),{expected,imageInfo},'guest',lang,width,p.url(),ss);publicReads.push({lang,width,path,imageInfo});
 }else if(path==='/about/'){const lead=await p.locator('.about-hero-lead').innerText();add('about-saved-text',lead.includes('QA10-ABOUT-'+lang.toUpperCase()),{lead,stored:s['about_text_'+lang]},'guest',lang,width,p.url(),ss);add('footer-about-saved-text',await p.locator('.footer-brand-copy').innerText()===s['about_text_'+lang],{},'guest',lang,width,p.url(),ss);
 }else if(path==='/contacts/'){const main=await p.locator('main').last().innerText();add('contacts-saved-public-text',main.includes('QA10-CONTACT-'+lang.toUpperCase()),{stored:s['contacts_text_'+lang],sample:main.slice(0,380)},'guest',lang,width,p.url(),ss);
 }else{add('empty-saved-text',text.includes('QA10-EMPTY-'+lang.toUpperCase()),{},'guest',lang,width,p.url(),ss);}
 }
 }
 await c.close();}
 for(const lang of ['ru','az','en']){const{c,p}=await context('admin',lang);for(const width of [360,390,768,1024,1280,1440]){await p.setViewportSize({width,height:950});for(const section of ['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings']){
 const http=await visit(p,'/admin/catalog/'+section+'/1/change/'),ss=await shot(p,'admin-'+section+'-'+lang+'-'+width),g=await geometry(p);add('admin-render',http===200,{htmlLang:await p.locator('html').getAttribute('lang')},'admin',lang,width,p.url(),ss);add('admin-no-overflow',g.document<=width+2,{geometry:g},'admin',lang,width,p.url(),ss);
 if(section==='sitevisibilitysettings'){const label=await p.locator('label[for=id_events_section_enabled]').innerText(),expected=lang==='ru'?'Показывать «Афишу»':lang==='en'?'Show “Events”':'“Tədbirlər” bölməsini göstər';add('admin-flag-translated-label',label===expected,{label,expected},'admin',lang,width,p.url(),ss);}
 }
 }
 await c.close();}
 return{rows,publicReads};
}
