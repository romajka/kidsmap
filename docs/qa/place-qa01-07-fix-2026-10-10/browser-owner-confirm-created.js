async (page) => {
  await page.goto('http://127.0.0.1:8840/ru/account/places/3/edit/');
  await page.reload();
  const result=await page.evaluate(()=>({placeId:Number(document.querySelector('[data-permanent-place-form]').dataset.targetId),status:document.querySelector('[data-pc-lifecycle]').textContent.trim(),district:document.querySelector('[name=district]').value,latitude:document.querySelector('[name=lat]').value,address:document.querySelector('[name=address]').value}));
  if(result.status!=='На модерации'||result.district!=='baku_yasamal'||result.latitude!=='')throw new Error('Submitted candidate readback failed');
  await page.screenshot({path:'C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/owner-submitted-390.png'});
  return result;
}
