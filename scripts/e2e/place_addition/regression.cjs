const H=require('./helpers.cjs');
async function regression(ctx){
 const c=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(c,ctx.fixture,'admin');
  for(const [key,f]of Object.entries(ctx.fixture.fixtures)){
   await p.goto(ctx.fixture.origin+`/admin/catalog/place/${f.id}/change/`);await p.locator('[data-place-accordion-expand-all]').click();
   const before=await p.locator('[name=pricing_plans]').inputValue();
   await require('./pricing.cjs').save(p,'admin');
   H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),JSON.parse(before),`${key}: no-op prices`);
   await p.locator('[data-place-accordion-expand-all]').click();
   await H.select(p,'#id_whatsapp_mode','none');
   await require('./pricing.cjs').save(p,'admin');
   H.assert.deepEqual(JSON.parse(await p.locator('[name=pricing_plans]').inputValue()),JSON.parse(before),`${key}: contact-only prices`);
   ctx.record({id:'E10',role:'admin',status:'PASS',fixture:key,placeId:f.id,assertions:['real no-op save','contact-only save','same complete pricing payload after reload']});
  }
 }catch(error){ctx.record({id:'E10',role:'admin',status:'FAIL',error:String(error)});throw error;}finally{await c.close();}
 const other=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(other,ctx.fixture,'other');const r=await p.goto(ctx.fixture.origin+`/ru/account/places/${ctx.fixture.fixtures.direct.id}/edit/`);H.assert([403,404].includes(r.status())||(r.status()===200&&new URL(p.url()).pathname==='/ru/account/places/'&&await p.locator('#id_name_az').count()===0&&(await p.locator('body').innerText()).includes('Карточка не найдена или не привязана')));ctx.record({id:'A07',role:'other',status:'PASS',assertions:['actual denial or safe dashboard redirect','no access to foreign owner form']});}finally{await other.close();}
 const anon=await H.context(ctx.browser,ctx.fixture.origin);
 try{const r=await anon.request.get(ctx.fixture.origin+ctx.fixture.fixtures.draft.public);H.assert([403,404].includes(r.status()));ctx.record({id:'F05',role:'anonymous',status:'PASS',assertions:['draft is not publicly readable']});}finally{await anon.close();}
 const item=await require('./create.cjs').create(ctx,'owner');
 const owner=await H.context(ctx.browser,ctx.fixture.origin);
 try{const p=await H.login(owner,ctx.fixture,'owner');await p.goto(item.editUrl);const title=await p.locator('#id_name_az').inputValue();
  const oldDescription=await p.locator('#id_description_az').inputValue();await H.fill(p,'#id_description_az',oldDescription+' Retry check.');
  const pattern='**/account/places/*/save-photos/';await p.route(pattern,route=>route.abort('failed'));
  await p.locator('[name=form_action][value=save_draft]').click();
  const retry=p.locator('[data-photo-save-status] button');await retry.waitFor({state:'visible'});
  H.assert.equal(await p.locator('#id_name_az').inputValue(),title);H.assert((await p.locator('#id_description_az').inputValue()).endsWith('Retry check.'));
  await p.unroute(pattern);const loaded=p.waitForEvent('domcontentloaded');await retry.click();await loaded;
  H.assert.equal(p.url(),item.editUrl);H.assert((await p.locator('#id_description_az').inputValue()).endsWith('Retry check.'));
  ctx.record({id:'G09',role:'owner',status:'PASS',assertions:['actual save transport failure','retained text and place ID','retry succeeds and reloads retained description']});
  await p.locator('[data-place-photos-picker]').setInputFiles({name:'damaged.png',mimeType:'image/png',buffer:Buffer.from('not a PNG')});
  await p.locator('[data-photo-id][data-state=error] .pw-photo-item-status').filter({hasText:/./}).first().waitFor({state:'visible'});
  H.assert.equal(await p.locator('#id_name_az').inputValue(),title);
  const bad=p.locator('[data-photo-id][data-state=error]');if(await bad.count())await bad.locator('[data-photo-action=remove]').click();
  ctx.record({id:'D07',role:'owner',status:'PASS',assertions:['real malformed file rejected','existing text and saved photos retained']});
 }catch(error){const p=owner.pages().at(-1);if(p){await p.screenshot({path:H.path.join(ctx.out,'failure-recovery.png'),fullPage:true});H.fs.writeFileSync(H.path.join(ctx.out,'failure-recovery.txt'),await p.locator('body').innerText());}ctx.record({id:'G09',role:'owner',status:'FAIL',error:String(error)});throw error;}finally{await owner.close();}
}
module.exports={regression};
