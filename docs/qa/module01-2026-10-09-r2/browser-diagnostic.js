async original=>{
 const rows=[];for(const c of original.context().browser().contexts())for(const p of c.pages()){
  rows.push({url:p.url()});if(p.url().includes('/account/places/2/edit/')){
   await p.locator('[data-photo-items=main] img').scrollIntoViewIfNeeded();rows.push({images:await p.locator('[data-photo-items=main] img').evaluateAll(es=>es.map(e=>({src:e.src,complete:e.complete,width:e.naturalWidth,height:e.naturalHeight,loading:e.loading}))) });const s=await c.newCDPSession(p);try{await s.send('Page.handleJavaScriptDialog',{accept:true});rows.push({nativeDialogAccepted:true});}catch{rows.push({nativeDialogAccepted:false});}finally{await s.detach();}
  }
 }return {rows,scope:'Own module01-r2 browser only; diagnostic recovery from a pending synthetic form dialog'};
}
