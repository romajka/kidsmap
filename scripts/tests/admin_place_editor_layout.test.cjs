const test=require('node:test'),assert=require('node:assert/strict');
const fixturePath=process.env.KIDSMAP_ADMIN_EDITOR_FIXTURE;
test('admin verification remains readable and photo entry matches the shared editor',{skip:!fixturePath,timeout:90000},async()=>{
 const H=require('../e2e/place_addition/helpers.cjs'),fixture=JSON.parse(H.fs.readFileSync(fixturePath));
 assert.equal(fixture.synthetic,true);assert.equal(fixture.database,'qa_stage04');
 const b=await H.launch(),c=await H.context(b,fixture.origin);
 try{const p=await H.login(c,fixture,'admin');await p.goto(fixture.origin+'/admin/catalog/place/add/?type=permanent');await p.locator('[data-place-accordion-expand-all]').click();
 for(const width of [1920,1600,1440,1325,1024,768,390,360,320]){await p.setViewportSize({width,height:1000});const m=await p.evaluate(()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return{verify:r('.km-pf-verify').width,body:r('.km-pf-verify__body').width,overflow:document.documentElement.scrollWidth>innerWidth+1};});assert.equal(m.overflow,false,'no admin overflow at '+width);assert(m.body>=m.verify-2,'verification uses available width at '+width);}
 assert.equal(await p.locator('[data-pf-preview]').count(),0,'one real preview, no competing simulated card');
 assert.equal(await p.locator('[data-km-photo-unified] [data-place-photos-picker]').isVisible(),true);
 assert.equal(await p.locator('[data-main-photo-root]').isVisible(),false,'no separate empty cover uploader');
 assert.equal(await p.locator('[data-gallery-add-button-empty]').isVisible(),false,'one entry point for adding photos');
 assert.equal(await p.locator('[data-km-preview]').count(),1);
 await p.locator('#id_name_az').focus();await p.locator('[data-place-media-section]').scrollIntoViewIfNeeded();
 await p.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 const section=await p.locator('[data-place-media-section]').evaluate(e=>e.closest('[data-place-accordion-section]').id);
 assert.equal(await p.locator('[data-pf-section-select]').inputValue(),section,'mobile navigation follows the visible section when the old field is offscreen');
 }finally{await c.close();await b.close();}
});
