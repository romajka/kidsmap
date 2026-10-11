async original=>{
 __QA10_COMMON__
 const{c,p}=await context('admin','ru');
 const values={brand_name:'QA10 Guide',home_hero_show_decor:false};
 for(const lang of ['ru','az','en'])for(const [field,mark] of [['home_title','HERO'],['home_subtitle','SUBTITLE'],['home_search_label','SEARCH-LABEL'],['home_search_placeholder','SEARCH-PLACEHOLDER'],['home_cta_text','CTA']])values[field+'_'+lang]='QA10-'+mark+'-'+lang.toUpperCase();
 await saveSettings(p,'sitebrandingsettings',values,'branding-filled');
 for(const [section,field,mark] of [['siteaboutsettings','about_text','ABOUT'],['sitecontactssettings','contacts_text','CONTACT'],['siteemptystatesettings','empty_results_text','EMPTY']]){
  const v={};for(const lang of ['ru','az','en'])v[field+'_'+lang]='QA10-'+mark+'-'+lang.toUpperCase()+' '+('Synthetic fictional text. '.repeat(mark==='ABOUT'?14:2));
  await saveSettings(p,section,v,mark.toLowerCase());
 }
 await saveSettings(p,'sitefootersettings',{footer_phone:'+994000000011',footer_email:'edited10@example.invalid',footer_instagram:'@qa10_fictional',footer_telegram:'https://example.invalid/qa10-telegram-edited',footer_whatsapp:'https://example.invalid/qa10-chat-edited'},'footer');
 await visit(p,'/admin/catalog/sitegalleryimage/');
 for(const [field,file] of [['logo','logo.png'],['home_hero_image','hero-pc.png'],['home_hero_mobile_image','hero-mobile.png'],['about_hero_image','hero-pc.png'],['about_hero_mobile_image','hero-mobile.png'],['empty_results_image','fixture.png'],['header_background_image','hero-pc.png'],['header_background_mobile_image','hero-mobile.png'],['footer_background_image','hero-pc.png'],['footer_background_mobile_image','hero-mobile.png']]){
  const before=(await state(p)).settings[field],row=p.locator('.km-media-row[data-field="'+field+'"]');const response=p.waitForResponse(r=>r.url().includes('ajax-upload/')&&r.request().method()==='POST');
  await row.locator('input[type=file]').setInputFiles(ASSET+'/'+file);const r=await response,data=await r.json();await p.waitForTimeout(100);const after=(await state(p)).settings[field];
  const ss=await shot(p,'image-'+field);add('native-image-upload-'+field,r.status()===200&&data.success&&after!==before&&after.includes(file.replace('.png','')), {http:r.status(),before,after},'admin','ru',1440,p.url(),ss);changes.push({label:field,method:'native file chooser/upload',before,after});
 }
 await p.reload();add('image-reload-all-persisted',(await state(p)).settings.home_hero_mobile_image.includes('hero-mobile'),{},'admin','ru',1440,p.url());
 const s=await state(p);await c.close();return{rows,changes,state:s};
}
