async page=>{
const B='http://127.0.0.1:59505',O='/home/ramin/kidsmap/output/playwright/admin-moderation-audit-2026-10-16-r1',f=await(await page.request.get(B+'/qa/fixtures/')).json();
await page.goto(B+'/admin/catalog_moderation/moderationplace/'+f.pending_place+'/change/');await page.locator('button[name="_publish_place"]').filter({visible:true}).first().click();
const dialog=page.getByRole('dialog');await dialog.waitFor({state:'visible'});await page.screenshot({path:O+'/publish-confirmation.png'});
const response=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/change/'));
await dialog.getByRole('button',{name:'Опубликовать',exact:true}).click();const posted=await response;await page.waitForLoadState('domcontentloaded');
const errors=await page.locator('.errornote,.errorlist,.alert').allTextContents();await page.screenshot({path:O+'/publish-result.png'});
const r=await page.goto(B+'/ru/place/'+f.pending_place+'-uydurma-mekan/');await page.locator('h1').first().waitFor();await page.screenshot({path:O+'/place-public-final.png'});
return{postStatus:posted.status(),editorUrl:posted.url(),errors,publicStatus:r.status(),heading:await page.locator('h1').first().innerText(),fullConfirmationCompleted:true};
}
