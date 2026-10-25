const H=require('./helpers.cjs'),crypto=require('node:crypto');
const fixturePath=process.argv[2],fixture=JSON.parse(H.fs.readFileSync(fixturePath,'utf8'));
const out=H.path.resolve(process.argv[3]||'.tmp/place-smoothness-20261025/browser');H.fs.mkdirSync(out,{recursive:true});
const results=[];const record=row=>{results.push(row);H.fs.writeFileSync(H.path.join(out,'results.json'),JSON.stringify({synthetic:true,sources:fixture.sources,externalMaps:'NOT RUN',results},null,2));console.log(row.status,row.id,row.lang||'',row.width||'');};
function checkSources(){for(const [name,digest]of Object.entries(fixture.sources))H.assert.equal(crypto.createHash('sha256').update(H.fs.readFileSync(name)).digest('hex'),digest,name);}
(async()=>{H.assert(fixture.synthetic&&fixture.database==='qa_stage04');checkSources();H.assert.deepEqual((await(await fetch(fixture.origin+'/__qa__/build/')).json()).sources,fixture.sources);
 const b=await H.launch();try{
 for(const lang of ['ru','az','en']){const c=await H.context(b,fixture.origin,320);try{const p=await H.login(c,fixture,'owner',lang);await p.emulateMedia({reducedMotion:'no-preference'});const errors=[],failedAssets=[];p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(fixture.origin)&&r.status()>=400&&['script','stylesheet','image'].includes(r.request().resourceType()))failedAssets.push({url:r.url(),status:r.status()});});
 for(const width of [320,360,390,768,1024,1280,1440]){
  let mascotRequests=0;const onRequest=r=>{if(r.url().includes('/img/mappy/'))mascotRequests++;};p.on('request',onRequest);
  await p.setViewportSize({width,height:1000});await p.goto(fixture.origin+`/${lang==='az'?'':lang+'/'}account/places/create/?type=permanent&fresh=1`);await p.waitForTimeout(450);
  const mascot=p.locator('[data-pc-mappy]');H.assert.equal(await mascot.isVisible(),width>960);
  if(width<=960){H.assert.equal(await mascot.locator('img').getAttribute('src'),null);H.assert.equal(mascotRequests,0,'mobile must not fetch mascot images');}
  else{await p.waitForFunction(()=>document.querySelector('[data-mappy-sprite]')?.naturalWidth>0);const box=await mascot.boundingBox(),last=await p.locator('.pc-nav a').last().boundingBox();H.assert(box.y>=last.y+last.height,'mascot is below desktop steps');await p.locator('[data-pc-mappy-wave]').click();H.assert(await mascot.evaluate(node=>node.classList.contains('is-waving')));await p.waitForTimeout(2050);H.assert.equal(await mascot.evaluate(node=>node.classList.contains('is-waving')),false,'no endless waving');}
  await H.inspect(p,out,`smooth-${lang}-${width}`);p.off('request',onRequest);
  record({id:'RESPONSIVE_MASCOT',status:'PASS',lang,width,mobileRequests:width<=960?mascotRequests:undefined});
 }
 if(lang==='ru'){
  const name=p.locator('#id_name_az');await name.fill('Smooth browser synthetic');const description=p.locator('#id_description_az');await description.click();await description.pressSequentially('A useful description for families and children.',{delay:30});await p.waitForTimeout(1500);
  H.assert.equal(await p.locator('[data-pc-mappy]').getAttribute('data-pose'),'writing');await H.inspect(p,out,'smooth-writing-ru-1440');
  await p.mouse.wheel(0,900);await p.waitForTimeout(500);const before=await p.evaluate(()=>scrollY);
  await p.locator('.pc-savebar').evaluate(node=>node.style.width='65%');await p.waitForTimeout(350);const after=await p.evaluate(()=>scrollY);H.assert(Math.abs(after-before)<=1,`resizing background panel moved viewport ${before}→${after}`);await p.locator('.pc-savebar').evaluate(node=>node.style.removeProperty('width'));
  record({id:'NO_BACKGROUND_SCROLL',status:'PASS',before,after});
  const real=await p.evaluate(()=>JSON.parse(document.getElementById('pc-readiness').textContent));
  await p.evaluate(()=>window.KidsMapOwnerWorkflow.setReadiness({required_count:10,completed_count:10,is_ready:true,error_count:0,items:[],sections:[]}));
  H.assert.equal(await p.locator('[data-pc-mappy]').getAttribute('data-pose'),'ready');await p.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await H.inspect(p,out,'smooth-ready-ru-1440');
  await p.emulateMedia({reducedMotion:'reduce'});await p.locator('[data-pc-mappy-wave]').click();H.assert.equal(await p.locator('[data-pc-mappy]').evaluate(node=>node.classList.contains('is-waving')),false);H.assert.equal(await p.locator('[data-mappy-sprite]').evaluate(node=>getComputedStyle(node).animationName),'none');await p.evaluate(data=>window.KidsMapOwnerWorkflow.setReadiness(data),real);
  record({id:'READY_POSE_AND_REDUCED_MOTION',status:'PASS',visualStateOnly:true});
 }
 H.assert.deepEqual(errors,[]);H.assert.deepEqual(failedAssets,[]);
 }finally{await c.close();}}
 checkSources();record({id:'FINAL_SOURCE_ATTESTATION',status:'PASS',browser:b.version()});
 }finally{await b.close();}
})().catch(error=>{record({id:'SMOOTHNESS',status:'FAIL',error:String(error)});console.error(error);process.exitCode=1;});
