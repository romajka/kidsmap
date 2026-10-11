async (page) => {
  await page.context().grantPermissions([],{origin:'http://127.0.0.1:8840'});
  await page.goto('http://127.0.0.1:8840/ru/account/places/2/edit/');
  const before={lat:await page.locator('[name=lat]').inputValue(),lng:await page.locator('[name=lng]').inputValue()};
  await page.locator('[data-map-locate]').click();
  await page.waitForFunction(()=>document.querySelector('[data-map-status]').textContent.includes('Не удалось'));
  if(await page.locator('[name=lat]').inputValue()!==before.lat||await page.locator('[name=lng]').inputValue()!==before.lng)throw new Error('Native permission denial changed point');
  await page.context().setGeolocation({latitude:40.41,longitude:49.87});
  await page.context().grantPermissions(['geolocation'],{origin:'http://127.0.0.1:8840'});
  await page.locator('[data-map-locate]').click();
  await page.waitForFunction(()=>document.querySelector('[name=lat]').value==='40.410000');
  const late=await page.evaluate(()=> {
    let maps=0,changes=0;
    const root=document.querySelector('[data-permanent-map]'),form=root.closest('form');
    const address=form.querySelector('[name=address]').value;
    form.addEventListener('km:map-change',()=>changes++);
    window.L={map(){maps++;return {on(){},setView(){},getZoom(){return 15;},invalidateSize(){},removeLayer(){},scrollWheelZoom:{enable(){},disable(){}}};},tileLayer(){return {addTo(){}};},marker(){return {addTo(){return this;},on(){},setLatLng(){}};}};
    document.querySelector('[data-owner-map-sdk=leaflet]').dispatchEvent(new Event('load'));
    window.kidsMapInitOwnerMapPickers();window.kidsMapRefreshOwnerMapPickers();
    const silent=changes===0;
    root.querySelector('[data-map-clear]').click();
    return {maps,silent,changes,lat:form.querySelector('[name=lat]').value,lng:form.querySelector('[name=lng]').value,addressPreserved:form.querySelector('[name=address]').value===address,adapter:'synthetic local Leaflet adapter, no external SDK'};
  });
  if(late.maps!==1||!late.silent||late.changes!==1||late.lat||late.lng||!late.addressPreserved)throw new Error('Late SDK load/event contract failed');
  return {nativeBrowserPermissionDenial:true,nativeBrowserGeolocationWithEmulatedPoint:true,late};
}
