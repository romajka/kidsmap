async (page) => {
  const stale=page.context().pages()[1];
  const result=await stale.evaluate(()=>({state:document.querySelector('[data-pc-save-status]').dataset.state,explicitConflict:document.querySelector('[data-pc-errors]').textContent.includes('Publication source/schema conflict'),inputPreserved:document.querySelector('[name=name_az]').value==='KMFIX Stale input must remain'}));
  if(!result.explicitConflict||!result.inputPreserved)throw new Error('Stale submission was not protected');
  await stale.setViewportSize({width:390,height:900});
  await stale.screenshot({animations:'disabled',path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/stale-conflict-390.png'});
  await stale.close({runBeforeUnload:false});
  return result;
}
