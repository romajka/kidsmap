async page=>{
 const context=await page.context().browser().newContext({viewport:{width:1440,height:1000},reducedMotion:'no-preference'});
 try{
  const tab=await context.newPage();
  await tab.addInitScript(()=>{
   const raf=requestAnimationFrame,clear=CanvasRenderingContext2D.prototype.clearRect;
   let queued,time=1000,draws=0;
   window.requestAnimationFrame=callback=>{
    if(new Error().stack.includes('living_map_background.js')){queued=callback;return -1;}
    return raf(callback);
   };
   CanvasRenderingContext2D.prototype.clearRect=function(x,y,w,h){
    if(this.canvas.hasAttribute('data-living-map')&&x===0&&y===0&&w===innerWidth&&h===innerHeight)draws++;
    return clear.call(this,x,y,w,h);
   };
   window.__sampleCadence=()=>{
    queued(time);draws=0;
    for(let i=0;i<45;i++)queued(time+=1000/90);
    return draws;
   };
  });
  await tab.goto('http://127.0.0.1:8773/ru/');await tab.waitForTimeout(200);
  const draws=await tab.evaluate(()=>__sampleCadence());
  if(draws<28||draws>31)throw new Error(`90Hz display should paint about 30 frames per half second; got ${draws}`);
  return {passed:true,draws,simulatedHz:90,seconds:.5};
 }finally{await context.close();}
}
