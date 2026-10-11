async original=>{
 __QA10_COMMON__
 const X=__EXTRA_JSON__,admin=await context('admin','ru'),owner=await context('owner','ru'),initial=await state(admin.p);
 const configs=[{field:'organizations_section_enabled',kind:'organization',list:'/organizations/',off:404,admin:'organization',owner:'/account/organizations/'+F.organization+'/'},{field:'specialists_section_enabled',kind:'specialist',list:'/specialists/',off:404,admin:'specialist',owner:'/account/places/specialists/'+F.specialist+'/edit/'},{field:'events_section_enabled',kind:'event',list:'/events/',off:410,admin:'event',owner:'/account/places/events/'+F.event+'/edit/'}];
 for(const config of configs)for(const enabled of [false,true]){
  const before=(await state(admin.p)).settings;await saveSettings(admin.p,'sitevisibilitysettings',{[config.field]:enabled},config.kind+'-'+(enabled?'on':'off'));
  const s=await state(admin.p);add('flag-independent-'+config.kind,configs.filter(x=>x.field!==config.field).every(x=>s.settings[x.field]===before[x.field]),{},'admin');add('flag-data-preserved-'+config.kind,JSON.stringify({...s,settings:null})===JSON.stringify({...initial,settings:null}),{},'admin');
  for(const lang of ['ru','az','en']){const{c,p}=await context('guest',lang);for(const width of [360,390,768,1024,1280,1440]){
   await p.setViewportSize({width,height:950});await visit(p,prefix(lang)+'/');const ss=await shot(p,'flag-'+config.kind+'-'+enabled+'-'+lang+'-'+width),href=prefix(lang)+config.list;
   const links=await p.locator('a[href="'+href+'"]').count();add('flag-home-menu-'+config.kind,enabled?links>0:links===0,{links,enabled},'guest',lang,width,p.url(),ss);
   for(const [type,path] of [['list',prefix(lang)+config.list],['detail',F.urls[lang][config.kind]]]){const status=await visit(p,path),es=await shot(p,'flag-'+config.kind+'-'+enabled+'-'+type+'-'+lang+'-'+width);add('flag-direct-'+config.kind+'-'+type,status===(enabled?200:config.off),{http:status,enabled},'guest',lang,width,p.url(),es);if(config.kind==='event'&&!enabled){add('disabled-event-readable-error',((await p.locator('body').innerText()).trim().length)>0,{bodyLength:(await p.locator('body').innerText()).trim().length,http:status},'guest',lang,width,p.url(),es);}}
   const catalogStatus=await visit(p,prefix(lang)+'/catalog/?q=QA10');add('flag-catalog-preserved',catalogStatus===200&&await p.locator('a[href="'+F.urls[lang].place+'"]').count()>0,{enabled,kind:config.kind},'guest',lang,width,p.url(),ss);
   if(config.kind==='organization')add('flag-search-organization-links',enabled?await p.locator('a[href="'+F.urls[lang].organization+'"]').count()>0:await p.locator('a[href="'+F.urls[lang].organization+'"]').count()===0,{enabled},'guest',lang,width,p.url(),ss);
   const map=await(await p.request.get(B+prefix(lang)+'/api/catalog/map/?q=QA10')).json(),ids=map.points.flatMap(x=>x.members.map(m=>m.id));add('flag-map-place-preserved',ids.includes(F.places.live),{ids,kind:config.kind,enabled},'guest',lang,width,B+prefix(lang)+'/api/catalog/map/?q=QA10',ss);
   if(config.kind==='event'){add('flag-map-temporary',enabled?ids.includes(X.temporary):!ids.includes(X.temporary),{ids,enabled},'guest',lang,width,B+prefix(lang)+'/api/catalog/map/?q=QA10',ss);const ts=await visit(p,X.urls[lang]);add('flag-temporary-public',ts===(enabled?200:404),{http:ts,enabled},'guest',lang,width,p.url(),ss);}
  }await c.close();}
  const os=await visit(owner.p,'/ru'+config.owner);add('flag-owner-'+config.kind,os===(config.kind==='organization'||enabled?200:404),{http:os,enabled},'owner','ru',1440,owner.p.url(),await shot(owner.p,'flag-owner-'+config.kind+'-'+enabled));
  const id=F[config.kind],as=await visit(admin.p,'/admin/catalog/'+config.admin+'/'+id+'/change/');add('flag-admin-edit-preserved',as===200&&await admin.p.locator('button[name=_continue]').count()>0,{http:as,enabled,kind:config.kind},'admin','ru',1440,admin.p.url(),await shot(admin.p,'flag-admin-'+config.kind+'-'+enabled));
 }
 // Source states differ from section visibility: initial draft/inactive/archive/deleted never become public after ON.
 const {c,p}=await context('owner','ru');await visit(p,'/ru/account/favorites/');const text=await p.locator('body').innerText();for(const label of ['draft','inactive','archived','deleted'])add('lifecycle-not-republished-'+label,!text.includes('QA10 '+label),{},'owner','ru',1440,p.url(),await shot(p,'lifecycle-favorites'));
 await c.close();await owner.c.close();await admin.c.close();return{rows,changes,final:await state(original)};
}
