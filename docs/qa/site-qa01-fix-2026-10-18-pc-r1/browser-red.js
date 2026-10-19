async original => {
const base='http://127.0.0.1:33480', O='/mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1', rows=[], browser=original.context().browser();
for(const role of ['none','viewer']) {
 const c=await browser.newContext({viewport:{width:390,height:950},serviceWorkers:'block'});
 await c.route('**/*',r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
 const p=await c.newPage();await p.goto(base+'/qa/site01/login/'+role+'/');
 const response=await p.goto(base+'/admin/catalog/sitegalleryimage/');
 const controls=await p.locator('.km-media-upload-btn,.km-media-delete-btn,.km-gallery-add').count();
 rows.push({role,status:response.status(),controls,checks:{access:role==='none'?response.status()===403:response.status()===200,readonly:role!=='viewer'||controls===0}});
 await p.screenshot({path:O+'/png/red-'+role+'-390.png',animations:'disabled'});await c.close();
}
return {phase:'RED',rows};
}
