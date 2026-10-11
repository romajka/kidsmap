"""Produce bounded continuation scripts without repeating completed transitions."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'favorites-notifications.js').read_text(encoding='utf-8')
s=s.split("try{\nawait a.goto(base+'/ru/account/notifications/');")[0]
s=s.replace("base+'/ru/places/'","base+'/ru/catalog/'")
s+="const s=await state(o);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};\n}"
(P/'favorites-finish.js').write_text(s,encoding='utf-8')
s=(P/'decisions.js').read_text(encoding='utf-8').split('for(const [kind,pk]')[0]
s+='''try{let s=await state(m),h=s.site.find(x=>x.user_id===F.actors.author.id);for(const status of ['rejected','approved','pending','approved']){
await m.goto(base+'/ru/admin/catalog/sitereview/'+h.id+'/change/');m.on('dialog',d=>d.accept());await m.locator('#id_status').selectOption(status);await m.locator('#id_rejection_reason').fill(status==='rejected'?'QA09 SITE REASON':'');await m.locator('input[name=_save],button[name=_save]').filter({visible:true}).first().click();await m.waitForLoadState('domcontentloaded');s=await state(m);h=s.site.find(x=>x.id===h.id);add('site-save-'+status+'-'+rows.length,h.status===status&&h.is_approved===(status==='approved'),{role:'moderator',head:h,screenshot:await shot(m,'site-status-'+status)});await g.goto(base+'/ru/reviews/');add('site-public-'+status,(await g.locator('body').innerText()).includes('QA09 SITE NATIVE')===(status==='approved'),{role:'guest',screenshot:await shot(g,'site-public-status-'+status)});
}}catch(err){rows.push({id:'site-editor-harness',status:'NOT RUN',role:'moderator',lang:'ru',width:1440,error:String(err).slice(0,450)});}
const s=await state(m);for(const c of contexts)await c.close();return{rows,state:s,utc:new Date().toISOString()};
}'''
(P/'site-finish.js').write_text(s,encoding='utf-8')
