from pathlib import Path
import shutil
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
common='''
const B='http://127.0.0.1:33810',G={organization:2},rows=[],consoleRows=[],network=[],blocked=[],contexts=[];
const check=(id,ok,detail={})=>{rows.push({id,checks:{ok},detail});if(!ok)throw new Error(id)};
async function actor(role){const c=await original.context().browser().newContext({viewport:{width:1440,height:950},userAgent:'Mozilla/5.0 Chrome/153.0.0.0 Safari/537.36'});contexts.push(c);await c.route('**/*',r=>{if(new URL(r.request().url()).hostname==='127.0.0.1')return r.continue();blocked.push(new URL(r.request().url()).hostname);return r.abort()});const p=await c.newPage();p.setDefaultTimeout(15000);p.on('pageerror',e=>consoleRows.push(String(e)));p.on('dialog',d=>d.accept());p.on('response',r=>{if(r.status()>=500)network.push({status:r.status(),path:new URL(r.url()).pathname})});if(role)await p.goto(B+'/qa/m13/login/'+role+'/');return p}
async function post(p,selector){await Promise.all([p.waitForNavigation({waitUntil:'domcontentloaded'}),p.locator(selector).first().click()])}
async function draft(p){await post(p,'[name=form_action][value=save_draft]:visible')}
async function step(p,i){await p.locator('[data-owner-step-target="'+i+'"]').click()}
async function snap(p,id){await p.screenshot({path:'/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1/png/event-lifecycle-'+id+'.png',fullPage:true})}
async function close(){for(const c of contexts)await c.close()}
'''
t=(R/'docs/qa/module04-full-2026-10-13-r1/lifecycle.js').read_text().replace('__COMMON__',common).replace('__ASSETS__/photo.png',str(Q/'assets/event-photo.png')).replace('module04','module13')
# Stable details locators do not change indexing as summaries open.
t=t.replace("for(const d of await a.locator('details:not([open]) > summary').all())await d.click();","while(await a.locator('details:not([open]) > summary').count())await a.locator('details:not([open]) > summary').first().click();")
(O/'browser-event-lifecycle.js').write_text(t)
print('Adapted prior lifecycle to fresh Module13 entities, roles, assets and canonical native forms.')
