async page=>{
 const B='http://127.0.0.1:59505',O='/home/ramin/kidsmap/output/playwright/admin-moderation-audit-2026-10-16-r1',f=await(await page.request.get(B+'/qa/fixtures/')).json();
 await page.context().addCookies([{name:'django_language',value:'ru',url:B}]);await page.setViewportSize({width:1440,height:950});
 const before=await page.goto(B+'/ru/reviews/place/target/'+f.place+'/');
 const publicFirst=await page.locator('[aria-labelledby="published-reviews"]').textContent().catch(()=>null);
 await page.screenshot({path:O+'/public-after-bulk.png'});
 await page.goto(B+'/admin/catalog/placereview/'+f.reviews[3].head+'/hide/');await page.getByRole('button',{name:'Скрыть',exact:true}).waitFor();
 await page.screenshot({path:O+'/hide-confirm.png'});
 await page.getByRole('button',{name:'Скрыть',exact:true}).click();await page.waitForURL(u=>!u.pathname.endsWith('/hide/'));
 const hideAlerts=await page.locator('.messagelist,.alert').allTextContents();
 await page.goto(B+'/ru/reviews/place/target/'+f.place+'/');await page.locator('h1').waitFor();
 const afterHide=await page.locator('[aria-labelledby="published-reviews"]').textContent();await page.screenshot({path:O+'/public-after-hide.png'});
 await page.goto(B+'/admin/catalog_moderation/moderationplace/'+f.pending_place+'/change/');await page.locator('button[name="_publish_place"]').first().waitFor();
 await page.screenshot({path:O+'/place-before-publish.png'});await page.locator('button[name="_publish_place"]').filter({visible:true}).first().click();
 await page.waitForLoadState('domcontentloaded');await page.screenshot({path:O+'/place-after-publish.png'});
 const publishAlerts=await page.locator('.messagelist,.alert').allTextContents();
 const publicUrl=B+'/ru/place/'+f.pending_place+'-uydurma-mekan/';const r=await page.goto(publicUrl);await page.locator('h1').first().waitFor();await page.screenshot({path:O+'/place-public.png'});
 return {publicAfterBulk:publicFirst,hideAlerts,hiddenTextStillPublished:afterHide.includes('Fictional EDIT awaiting approval 3'),publishAlerts,publicPlaceStatus:r.status(),publicPlaceHeading:await page.locator('h1').first().innerText()};
}
