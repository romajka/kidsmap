async original=>{
 __QA10_COMMON__
 const{c,p}=await context('admin','ru');for(const [section,field,marker] of [['siteaboutsettings','about_text','ABOUT'],['sitecontactssettings','contacts_text','CONTACT'],['siteemptystatesettings','empty_results_text','EMPTY']]){
 await visit(p,'/admin/catalog/'+section+'/1/change/');await p.reload();const s=(await state(p)).settings;for(const lang of ['ru','az','en']){const val=await p.locator('[name='+field+'_'+lang+']').inputValue();add('trimmed-settings-reload-'+field,val===s[field+'_'+lang]&&val.startsWith('QA10-'+marker+'-'+lang.toUpperCase()),{stored:val},'admin','ru',1440,p.url(),await shot(p,'readback-'+field+'-'+lang));}
 }await c.close();return{rows};
}
