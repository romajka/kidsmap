const test=require('node:test'),assert=require('node:assert/strict');
const fixturePath=process.env.KIDSMAP_CONTACT_LAYOUT_FIXTURE;
// Rendered regression: run against the isolated local fixture, never a production URL.
test('owner form aligns with the header and keeps compact accessible contacts', {skip:!fixturePath,timeout:90000}, async()=>{
 const H=require('../e2e/place_addition/helpers.cjs'),fixture=JSON.parse(H.fs.readFileSync(fixturePath));
 assert.equal(fixture.synthetic,true);assert.equal(fixture.database,'qa_stage04');
 const browser=await H.launch(),c=await H.context(browser,fixture.origin);try{
 const p=await H.login(c,fixture,'owner');await c.route('**/api/drafts/**',r=>r.request().method()==='GET'?r.continue():r.abort());
 await p.goto(fixture.origin+'/ru/account/places/create/?type=permanent&fresh=1');
 for(const width of [1440,1280,1024,768,390,360]){await p.setViewportSize({width,height:1000});
 const m=await p.evaluate(()=>{const r=s=>document.querySelector(s).getBoundingClientRect();return{header:{x:r('.km-header-inner').x,right:r('.km-header-inner').right},workspace:{x:r('.pc-workspace').x,right:r('.pc-workspace').right},fieldBoxes:Array.from(document.querySelectorAll('.pc-contacts .pw-field,.pc-socials .pw-field')).map(e=>e.getBoundingClientRect()).filter(b=>b.width>0&&b.height>0).map(b=>({left:b.left,right:b.right,top:b.top,bottom:b.bottom})),overflow:document.documentElement.scrollWidth>innerWidth+1};});
 assert.equal(m.overflow,false,'no horizontal overflow at '+width);
 // Readable hints may wrap: the user explicitly requested more text spacing.
 // Verify collisions instead of imposing an arbitrary total section height.
 for(let i=0;i<m.fieldBoxes.length;i++)for(let j=i+1;j<m.fieldBoxes.length;j++){const a=m.fieldBoxes[i],b=m.fieldBoxes[j];assert(!(Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1),'contact fields do not overlap at '+width);}
 if(width>=1024){assert(Math.abs(m.workspace.x-m.header.x)<=1,'left form/header edges at '+width);assert(Math.abs(m.workspace.right-m.header.right)<=1,'right form/header edges at '+width);}
 }
 await p.setViewportSize({width:1440,height:1000});assert((await p.locator('[data-pw-field=whatsapp_mode] .km-custom-select__trigger').boundingBox()).height>=44,'WhatsApp visible control preserves 44px target');const add=p.locator('[data-km-phone-add]');await add.focus();await add.press('Enter');assert.equal(await p.locator('[name=phone2]').isVisible(),true);assert.equal(await p.locator('[name=phone2]').evaluate(e=>e===document.activeElement),true);await p.locator('[name=phone2]').fill('+994551112244');await add.focus();await add.press('Enter');await p.locator('[name=phone3]').fill('+994701112255');assert.equal(await add.isDisabled(),true);
 for(const name of ['phone1','phone2','phone3','instagram','website'])assert.equal(await p.locator('[name='+name+']').isVisible(),true,name+' remains visible');
 await p.locator('[name=instagram]').fill('@synthetic');await p.locator('[name=website]').fill('https://example.com');
 const remove=p.locator('[data-km-phone-slot]').first().locator('[data-km-phone-remove]');await remove.focus();await remove.press('Enter');assert.equal(await p.locator('[name=phone2]').inputValue(),'');assert.equal(await p.locator('[name=phone3]').inputValue(),'+994701112255');assert.equal(await p.locator('[name=phone3]').isVisible(),true);
 assert.equal(await p.locator('[name=instagram]').inputValue(),'@synthetic');assert.equal(await p.locator('[name=website]').inputValue(),'https://example.com');
 H.fs.mkdirSync('output/playwright/contact-layout',{recursive:true});for(const width of [1440,390]){await p.setViewportSize({width,height:1000});await p.locator('.pc-contacts').scrollIntoViewIfNeeded();await H.inspect(p,'output/playwright/contact-layout','contacts-'+width);}
 }finally{await c.close();await browser.close();}
});
