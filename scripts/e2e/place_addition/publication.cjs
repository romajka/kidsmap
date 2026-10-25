const H=require('./helpers.cjs');
async function sendForReview(ctx,item){
 const c=await H.context(ctx.browser,ctx.fixture.origin,item.width);
 try{const p=await H.login(c,ctx.fixture,'owner',item.lang);await p.goto(item.editUrl);
 const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/account/places/')&&!r.url().includes('/prepare/'));
 await p.locator('[data-pc-submit]').click();
 const r=await response;if(r.status()>=400)throw new Error(await r.text());
 await p.waitForLoadState('networkidle');
 const errors=await p.locator('[data-pc-errors]').innerText().catch(()=> '');H.assert(!errors.trim(),errors);
 ctx.record({id:'A04',role:'owner',lang:item.lang,status:'PASS',assertions:['real owner submission accepted','owner does not directly publish'],editUrl:item.editUrl});
 }finally{await c.close();}
}
async function publish(ctx,item){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,'admin');
 const id=item.editUrl.match(/\/(\d+)\/(?:edit|change)\//)?.[1];H.assert(id,'Saved place ID');
 const edit=ctx.fixture.origin+`/admin/catalog/place/${id}/change/`;
 await p.goto(edit);await p.locator('[data-place-accordion-expand-all]').click();
 const publish=p.locator('[name=_publish_place]').first();H.assert(await publish.isEnabled(),'Complete candidate can publish');
 const response=p.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes(`/place/${id}/change/`));
 await publish.click();
 const modal=p.locator('.km-modal-backdrop').filter({hasText:'Опубликовать карточку?'});
 await modal.waitFor({state:'visible'});
 await modal.getByRole('button',{name:'Опубликовать',exact:true}).click();
 const r=await response;H.assert(r.status()<400,`Publish response ${r.status()}`);
 await p.waitForLoadState('networkidle');
 const body=await p.locator('body').innerText();H.assert(!body.includes('Проверьте подсвеченные поля формы.'),'Publish did not return form errors');
 const links=await p.locator('a[href]').evaluateAll(es=>es.map(e=>e.href));
 const publicUrl=links.find(url=>new RegExp(`/place/${id}[-/]`).test(url)&&!url.includes('/admin/'));
 H.assert(publicUrl,'Published place has a public link');
 ctx.record({id:item.role==='owner'?'A05':'A02',role:'admin',lang:item.lang,status:'PASS',placeId:id,publicUrl,assertions:['real staff publication','same saved place ID']});
 return {id,publicUrl,name:item.name};
 }catch(error){const p=c.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,`failure-publish-${item.role}-${item.lang}.png`),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,`failure-publish-${item.role}-${item.lang}.txt`),await p.locator('body').innerText());}throw error;}finally{await c.close();}
}
async function publicCheck(ctx,place){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await c.newPage(),w=H.watch(p,ctx.fixture.origin);const r=await p.goto(place.publicUrl);H.assert.equal(r.status(),200);
 H.assert((await p.locator('body').innerText()).includes(place.name));
 const media=await p.locator('main img').evaluateAll(es=>es.map(e=>e.currentSrc||e.src).filter(src=>src.includes('/media/')));
 H.assert(media.length,'Public place shows saved photo');for(const url of [...new Set(media)]){const r=await c.request.get(url);H.assert.equal(r.status(),200,`Saved photo is readable: ${url}`);}
 await H.inspect(p,ctx.out,`public-${place.id}`);H.assert.deepEqual(w.errors,[]);
 const catalog=await p.goto(ctx.fixture.origin+'/ru/catalog/?q='+encodeURIComponent(place.name));H.assert.equal(catalog.status(),200);
 H.assert(await p.locator(`a[href*="/place/${place.id}-"]`).count(),'Published place appears in catalog');
 ctx.record({id:'F01',role:'anonymous',status:'PASS',placeId:place.id,assertions:['public detail 200','saved name','real media HTTP200','catalog contains same place']});
 }finally{await c.close();}
}
module.exports={sendForReview,publish,publicCheck};
