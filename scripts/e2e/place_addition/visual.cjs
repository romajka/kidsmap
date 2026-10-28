const H=require('./helpers.cjs');
const {feedbackWatch}=require('./response_watch.cjs');
async function visual(ctx){
 for(const role of ['admin','owner']){
  const c=await H.context(ctx.browser,ctx.fixture.origin);await H.login(c,ctx.fixture,role);
  try{for(const lang of ['az','ru','en'])for(const width of [320,360,390,768,1024,1280,1440]){
   await c.addCookies([{name:'django_language',value:lang,url:ctx.fixture.origin}]);
   const p=await c.newPage();await p.setViewportSize({width,height:1000});const w=feedbackWatch(p,ctx.fixture.origin);
   const response=await p.goto(ctx.fixture.origin+(role==='admin'?'/admin/catalog/place/add/?type=permanent':`/${lang==='az'?'':lang+'/'}account/places/create/?type=permanent&fresh=1`));H.assert.equal(response.status(),200);
   H.assert.equal(await p.locator('html').getAttribute('lang'),lang,'Requested UI language is rendered');
   H.assert.equal(await p.locator('.km-place-photo-picker strong').innerText(),{ru:'Добавить фотографии',az:'Şəkillər əlavə et',en:'Add photos'}[lang],'New photo picker is translated');
   H.assert((await p.locator('[data-km-preview]').innerText()).includes({ru:'Просмотреть перед публикацией',az:'Dərc etməzdən əvvəl bax',en:'Preview before publishing'}[lang]),'Full preview action is translated');
   H.assert.equal(await p.locator('[data-km-check]').innerText(),{ru:'Проверить заполнение',az:'Doldurulmanı yoxla',en:'Check required entries'}[lang],'Read-only validation action is translated');
   if(role==='admin')await p.locator('[data-place-accordion-expand-all]').click();
   if(role==='admin'){
    const description=p.locator('#id_description_az').locator('xpath=ancestor::*[@data-pf-field][1]');
    H.assert.equal(await description.locator('.km-pf-counter,[data-km-counter]').count(),1,'Description has one authoritative character/line counter');
    H.assert((await p.locator('#id_category').locator('xpath=ancestor::div[contains(@class,"km-pf-native-select")][1]/following-sibling::div[contains(@class,"km-pf-picker-wrap")][1]').innerText()).includes({az:'Kateqoriyanı seçin',ru:'Выберите категорию',en:'Select a category'}[lang]),'Category placeholder follows the selected language');
    if(width<=390)H.assert.deepEqual(await p.locator('.km-pf-section__copy,.km-pf-section__missing').evaluateAll(es=>es.filter(e=>e.checkVisibility()&&e.getBoundingClientRect().width<140).map(e=>e.className)),[],'Section titles and missing-field explanations keep a readable mobile column');
   }
   await p.locator('[data-tariff-add]').click();await H.select(p,'[data-tariff-key=editor_kind]','monthly');await H.fill(p,'[data-tariff-key=price]','120');await H.fill(p,'[data-tariff-key=quantity]','12');
   const blocks=role==='admin'?['#basics','#location','#pricing','#media']:['#pc-section-1','#pc-section-2','#pc-section-3','#pc-section-4'];
   for(let i=0;i<blocks.length;i++){
    const block=p.locator(blocks[i]);await block.scrollIntoViewIfNeeded();await H.inspect(p,ctx.out,`visual-${role}-${lang}-${width}-${i+1}`);
   }
   await p.waitForLoadState('networkidle');
   H.assert.deepEqual(w.errors,[]);const expected=await w.verify();
   const clipping=await p.locator('[data-tariff-editor] input:not([type=hidden]),[data-tariff-editor] select').evaluateAll(es=>es.filter(e=>e.checkVisibility()&&e.getBoundingClientRect().width>5).map(e=>({key:e.dataset.tariffKey,left:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right})).filter(e=>e.left < -1||e.right>innerWidth+1));H.assert.deepEqual(clipping,[],'Pricing controls fit viewport');
   ctx.record({id:'G01',role,lang,width,status:'PASS',readiness422:expected,assertions:['four real rendered blocks','document fits viewport','pricing controls not clipped','no JS errors','no unexpected local HTTP errors; check-only 422 responses have structured errors'],externalMap:'blocked; not a provider integration test'});
   await p.close();
  }}finally{await c.close();}
 }
}
module.exports={visual};
