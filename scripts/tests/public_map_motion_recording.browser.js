async page => {
  const output='/home/ramin/kidsmap/output/playwright';
  const videos=[];
  for(const width of [1440,390]) {
    const height=width===390?844:900;
    const ctx=await page.context().browser().newContext({viewport:{width,height},recordVideo:{dir:output,size:{width,height}}});
    const p=await ctx.newPage();const recordingStarted=Date.now();p.setDefaultTimeout(6000);
    const errors=[];p.on('pageerror',e=>errors.push(e.message));
    await p.addInitScript(()=>{let api;Object.defineProperty(window,'KidsMapGoogleMotion',{get:()=>api,set:v=>{api=v;const create=v.create;v.create=m=>{window.__map=m;return create(m)};}});});
    const visible=async cluster=>{
      const label=await p.locator('.kidsmap-marker-button').evaluateAll((es,cluster)=>es.filter(e=>/^\d/.test(e.getAttribute('aria-label'))===cluster).find(e=>{const r=e.getBoundingClientRect(),m=__map.getDiv().getBoundingClientRect();return r.x>m.x&&r.right<m.right&&r.y>Math.max(110,m.y)&&r.bottom<Math.min(innerHeight,m.bottom)-10})?.getAttribute('aria-label'),cluster);
      if(!label)throw Error('Missing visible '+(cluster?'cluster':'pin'));
      return p.locator('.kidsmap-marker-button[aria-label='+JSON.stringify(label)+']');
    };
    try {
      await p.goto('http://127.0.0.1:8773/ru/');await p.locator('#home-map').scrollIntoViewIfNeeded();await p.evaluate(()=>scrollBy(0,-120));
      await p.waitForFunction(()=>window.__map&&document.querySelector('.kidsmap-marker-button'));await p.waitForTimeout(1500);
      const trimStartSeconds=Math.max(0,(Date.now()-recordingStarted)/1000-.2);
      await p.evaluate(()=>{window.__cameraSamples=[];window.__cameraRecording=true;let last=performance.now();function sample(now){if(!window.__cameraRecording)return;__cameraSamples.push({t:Math.round(now),dt:Math.round(now-last),zoom:__map.getZoom(),pins:document.querySelectorAll('.kidsmap-marker-button').length});last=now;requestAnimationFrame(sample)}requestAnimationFrame(sample);});
      const cluster=await visible(true);await cluster.hover();await p.waitForTimeout(450);await cluster.click();await p.waitForTimeout(1300);
      const pin=await visible(false);await pin.hover();await p.waitForTimeout(450);await pin.click();await p.waitForTimeout(1700);
      await p.screenshot({path:output+'/map-motion-'+width+'.png'});
      await p.keyboard.press('Escape');await p.waitForTimeout(500);
      const zoomLabel=await p.locator('#home-map button').evaluateAll(es=>es.map(e=>e.getAttribute('aria-label')).find(s=>s&&/Уменьш|Zoom out/i.test(s)));
      if(zoomLabel){await p.getByRole('button',{name:zoomLabel,exact:true}).click();await p.waitForTimeout(1000);}
      const metrics=await p.evaluate(()=>{window.__cameraRecording=false;const s=__cameraSamples;return {samples:s.length,emptyFrames:s.filter(x=>x.pins===0).length,maxFrameGap:Math.max(...s.map(x=>x.dt)),rendering:__map.getRenderingType()}});
      videos.push({width,errors,metrics,trimStartSeconds,path:output+'/map-motion-'+width+'.webm'});
    } finally {
      const video=p.video();await ctx.close();await video.saveAs(output+'/map-motion-'+width+'.webm');
    }
  }
  return {videos};
}
