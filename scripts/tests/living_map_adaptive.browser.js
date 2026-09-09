async page => {
 const context=await page.context().browser().newContext({viewport:{width:1440,height:1000}});
 try {
  const tab=await context.newPage();
  await tab.addInitScript(()=>{
   const raf=window.requestAnimationFrame, arc=CanvasRenderingContext2D.prototype.arc;
   let time=0,arcs=0;
   window.__densitySamples=[];
   // Count the small ambient particles; destination badges and arrival rings
   // are narrative UI decoration and should not disappear with lower density.
   CanvasRenderingContext2D.prototype.arc=function(...args){if(this.canvas.hasAttribute('data-living-map')&&args[2]<=2.8)arcs++;return arc.apply(this,args);};
   window.requestAnimationFrame=callback=>{
    const living=new Error().stack.includes('living_map_background.js');
    return raf.call(window,living?()=>{arcs=0;callback(time+=34);if(arcs)__densitySamples.push(arcs);}:callback);
   };
  });
  await tab.goto('http://127.0.0.1:8773/ru/');
  await tab.waitForFunction(()=>__densitySamples.length>=95);
  const samples=await tab.evaluate(()=>__densitySamples);
  const median=a=>a.toSorted((a,b)=>a-b)[Math.floor(a.length/2)];
  const initial=median(samples.slice(2,12)),adapted=median(samples.slice(-10));
  if(adapted>=initial*.8)throw new Error(`Sustained 34ms frames must reduce density: ${initial} -> ${adapted}`);
  return {passed:true,initialArcs:initial,adaptedArcs:adapted};
 }finally{await context.close();}
}
