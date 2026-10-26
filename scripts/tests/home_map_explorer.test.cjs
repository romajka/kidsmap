const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM || '../../.tmp/phone-dom/node_modules/jsdom');
const source=fs.readFileSync('static/js/home_map.js','utf8');
const paging=fs.readFileSync('static/js/map_paging.js','utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function member(id,name='Place '+id){return{id,name,url:'/ru/places/'+id+'/',image_url:'',price:'от 80 ₼ / месяц',age:'6–12 лет',category:'Sport',location:'Baku / Metro',content_language:'ru'};}
function point(id,members=[member(id)]){return{...members[0],key:'place:'+id,lat:40.4+id/10000,lng:49.8,members};}
function setup(points=[point(1)],{mobile=false,more=false}={}){
 const dom=new JSDOM(`<html lang="ru"><body><form data-home-map-filter-form><input name="q"><select name="category"><option value="">All</option><option value="ART">Art</option><option value="SPORT">Sport</option></select></form>
 <section id="home-map-section" data-home-map-explorer data-select-label="Показать на карте: {name}" data-details-label="Подробнее" data-list-label="Места" data-loading-label="Загрузка мест…" data-error-label="Не удалось обновить места" data-empty-label="Мест пока нет" data-guide-label="Выберите место в списке или на карте" data-selected-label="Выбрано: {name}">
 <div role="tablist"><button data-home-explorer-tab="map" id="map-tab" role="tab" aria-selected="true">Карта</button><button data-home-explorer-tab="list" id="list-tab" role="tab" aria-selected="false">Список</button></div>
 <p data-home-explorer-status role="status"></p><div data-home-explorer-list><ol data-home-map-list></ol><div data-home-explorer-empty hidden><img src="/static/img/mappy/mappy-empty.webp" alt=""><p>Мест пока нет</p></div></div>
 <div data-home-explorer-map><div id="home-map" data-map-endpoint="/api/map/points/" data-details-label="Подробнее" data-empty-label="Мест пока нет"></div><p id="home-map-note" hidden></p></div>
 <div data-home-map-guide><p data-home-map-guide-text></p></div>
 <div data-map-pagination="home" data-map-endpoint="/api/map/points/" data-shown-label="{shown} / {total}" data-loading-label="Загрузка" data-error-label="Не удалось загрузить места" data-more-label="Ещё" data-retry-label="Повторить"><p data-map-status></p><button data-map-more></button></div></section>
 <script type="application/json" id="home-map-data">${JSON.stringify(points)}</script><script type="application/json" id="home-map-page">${JSON.stringify({count:points.reduce((n,p)=>n+p.members.length,0),has_more:more,next_cursor:more?1:null})}</script></body></html>`,{url:'https://kidsmap.example/ru/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window, requests=[];w.HTMLElement.prototype.scrollIntoView=function(){this.dataset.scrolled='1';};
 w.matchMedia=query=>({matches:query.includes('max-width')?mobile:false,addEventListener(){},removeEventListener(){}});
 w.IntersectionObserver=class{observe(){}disconnect(){}};
 w.setTimeout=()=>1;w.clearTimeout=()=>{};
 w.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
 w.eval(paging);w.eval(source);
 return{dom,w,d:w.document,requests,close(){w.close();}};
}
test('list uses every actual member once, including shared-venue members and backend labels',()=>{
 const t=setup([point(1,[member(1),member(2)]),point(3)]);
 assert.equal(t.d.querySelectorAll('[data-home-map-list] li').length,3);
 assert.match(t.d.querySelector('[data-home-map-list]').textContent,/от 80 ₼ \/ месяц/);
 assert.match(t.d.querySelector('[data-home-map-list]').textContent,/6–12 лет/);
 assert.equal(t.d.querySelectorAll('[data-home-map-list] img').length,0,'no invented thumbnail');t.close();
});
test('payload names are text and unsafe image/detail URLs are rejected',()=>{
 const bad=member(7,'<img src=x onerror=alert(1)>');bad.url='javascript:alert(1)';bad.image_url='data:image/svg+xml,<svg onload=alert(1)>';
 const t=setup([point(7,[bad])]);const list=t.d.querySelector('[data-home-map-list]');
 assert.ok(list.textContent.includes(bad.name));assert.equal(list.querySelectorAll('img,a').length,0);assert.equal(list.querySelectorAll('[onerror],[onload]').length,0);t.close();
});
test('list selection before provider load keeps member identity and requests lazy map reveal',()=>{
 const t=setup([point(1,[member(1),member(2)])]);let loads=0;t.w.kidsMapTriggerHomeMapLoad=()=>loads++;
 const selected=t.d.querySelector('[data-home-map-member-id="2"]');assert.ok(selected);selected.click();
 assert.equal(selected.getAttribute('aria-pressed'),'true');assert.equal(t.d.querySelector('[data-home-map-member-id="1"]').getAttribute('aria-pressed'),'false');assert.equal(loads,1);t.close();
});
test('mobile map/list tabs use roving focus and remain operable without a provider',()=>{
 const t=setup(undefined,{mobile:true});const map=t.d.querySelector('[data-home-explorer-tab="map"]'),list=t.d.querySelector('[data-home-explorer-tab="list"]');map.focus();map.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
 assert.equal(t.d.activeElement,list);assert.equal(list.getAttribute('aria-selected'),'true');assert.equal(list.tabIndex,0);assert.equal(map.tabIndex,-1);assert.equal(t.d.querySelector('[data-home-explorer-list]').hidden,false);
 list.dispatchEvent(new t.w.KeyboardEvent('keydown',{key:'Home',bubbles:true}));assert.equal(t.d.activeElement,map);assert.equal(map.getAttribute('aria-selected'),'true');t.close();
});
test('pagination appends and merges real venue members without duplicate cards',async()=>{
 const t=setup([point(1)],{more:true});t.d.querySelector('[data-map-more]').click();assert.equal(t.requests.length,1);
 t.requests[0].resolve({ok:true,json:async()=>({points:[point(1,[member(1),member(2)])],count:2,has_more:false,next_cursor:null})});await tick();
 assert.equal(t.d.querySelectorAll('[data-home-map-list] li').length,2);t.close();
});
test('new filter response wins over a late response and updates map/list together',async()=>{
 const t=setup();const select=t.d.querySelector('select');select.value='ART';select.dispatchEvent(new t.w.Event('change'));select.value='SPORT';select.dispatchEvent(new t.w.Event('change'));assert.equal(t.requests.length,2);assert.equal(t.requests[0].options.signal.aborted,true);
 t.requests[1].resolve({ok:true,json:async()=>({points:[point(9)],count:1,has_more:false})});await tick();t.requests[0].resolve({ok:true,json:async()=>({points:[point(8)],count:1,has_more:false})});await tick();
 assert.ok(t.d.querySelector('[data-home-map-member-id="9"]'));assert.equal(t.d.querySelector('[data-home-map-member-id="8"]'),null);t.close();
});
test('empty server results show explicit empty state and failed refresh reports error',async()=>{
 const t=setup();const select=t.d.querySelector('select');select.dispatchEvent(new t.w.Event('change'));t.requests[0].resolve({ok:true,json:async()=>({points:[],count:0,has_more:false})});await tick();
 assert.equal(t.d.querySelector('[data-home-explorer-empty]').hidden,false);assert.equal(t.d.querySelectorAll('[data-home-map-list] li').length,0);
 select.dispatchEvent(new t.w.Event('change'));t.requests[1].reject(new Error('offline'));await tick();assert.match(t.d.querySelector('[data-home-explorer-status]').textContent,/Не удалось/);t.close();
});

test('loading disables stale list selections and restores them after a failed request',async()=>{
 const t=setup();t.d.querySelector('select').dispatchEvent(new t.w.Event('change'));await tick();
 assert.equal(t.d.querySelector('[data-home-map-member-id="1"]').disabled,true);
 t.requests[0].reject(new Error('offline'));await tick();assert.equal(t.d.querySelector('[data-home-map-member-id="1"]').disabled,false);t.close();
});
function providerHelpers(reduced=false){
 const vm=require('node:vm');const ctx={window:{matchMedia:()=>({matches:reduced})}};vm.createContext(ctx);
 const start=source.indexOf('  function revealHomeLeafletMarker('),end=source.indexOf('  function safeHomeMapUrl(');
 if(start>=0)vm.runInContext(source.slice(start,end),ctx);return ctx;
}
test('cluster reveal waits for visibility and ignores an obsolete selection callback',()=>{
 const ctx=providerHelpers(),callbacks=[],opened=[];let current=1;
 const group={zoomToShowLayer:(_marker,done)=>callbacks.push(done)},map={},first={marker:{id:1},place:{lat:40,lng:49}},second={marker:{id:2},place:{lat:40,lng:49}};
 ctx.revealHomeLeafletMarker(group,map,first,()=>current===1,()=>opened.push(1));assert.deepEqual(opened,[]);
 current=2;ctx.revealHomeLeafletMarker(group,map,second,()=>current===2,()=>opened.push(2));callbacks[1]();callbacks[0]();assert.deepEqual(opened,[2]);
});
test('reduced-motion direct marker reveal does not animate the camera',()=>{
 const ctx=providerHelpers(true),moves=[];let opened=0;
 ctx.revealHomeLeafletMarker({}, {setView:(_center,_zoom,options)=>moves.push(options.animate)}, {marker:{},place:{lat:40,lng:49}},()=>true,()=>opened++);
 assert.deepEqual(moves,[false]);assert.equal(opened,1);
});

test('Leaflet selected marker highlight is cleared without changing keyboard semantics',()=>{
 const ctx=providerHelpers(),dom=new JSDOM('<div role="button" tabindex="0" aria-label="A place"></div>');
 const element=dom.window.document.querySelector('div'),marker={getElement:()=>element};
 ctx.setHomeLeafletMarkerSelected(marker,true);assert.equal(element.classList.contains('is-home-map-selected'),true);assert.equal(element.getAttribute('aria-expanded'),'true');
 ctx.setHomeLeafletMarkerSelected(marker,false);assert.equal(element.classList.contains('is-home-map-selected'),false);assert.equal(element.getAttribute('aria-expanded'),'false');
 assert.equal(element.tabIndex,0);assert.equal(element.getAttribute('aria-label'),'A place');assert.doesNotThrow(()=>ctx.setHomeLeafletMarkerSelected({getElement:()=>null},false));dom.window.close();
});
test('exact matched group ages are displayed verbatim without substituting broad place age',()=>{
 const exact=member(12);exact.age='';exact.matched_offers=[{name:'Математика',groups:[{name:'Младшая группа',age:'4–6'}]}];const t=setup([point(12,[exact])]);
 const label=t.d.querySelector('.home-explorer-matched-group');assert.ok(label);assert.equal(label.textContent,'Математика · Младшая группа · 4–6');assert.equal(t.d.querySelector('.home-explorer-age'),null);t.close();
});

// Exercise the actual Leaflet mounting branch; the provider model deliberately
// implements only its public marker/popup/cluster lifecycle (no external SDK).
function leafletLifecycle(initial=[point(1)],size={width:340,height:430}){
 const vm=require('node:vm'),dom=new JSDOM('<div id="map"></div><p id="note"></p>');
 const d=dom.window.document,maps=[],markers=[],frames=[],viewports=[];let selected=1;
 function events(target={}){const handlers={};return Object.assign(target,{on(names,fn){names.split(' ').forEach(name=>(handlers[name]||=[]).push(fn));return this;},off(name,fn){handlers[name]=(handlers[name]||[]).filter(item=>item!==fn);return this;},fire(name,event={}){(handlers[name]||[]).forEach(fn=>fn(event));}});}
 const map=events({popup:null,addLayer(){},removeLayer(){},invalidateSize(){this.invalidations=(this.invalidations||0)+1;},setView(){},fitBounds(){},getBounds:()=>({getSouthWest:()=>({lat:40,lng:49}),getNorthEast:()=>({lat:41,lng:50})}),closePopup(){const previous=this.popup;this.popup=null;if(previous)previous.fire('popupclose');}});maps.push(map);
 const group=events({layers:[],clearLayers(){map.closePopup();this.layers=[];},addLayers(items){this.layers.push(...items);items.forEach(marker=>marker.fire('add'));},addLayer(marker){this.addLayers([marker]);},hasLayer(marker){return this.layers.includes(marker);},refreshClusters(){},zoomToShowLayer(_marker,done){done();}});
 const L={map:()=>map,markerClusterGroup:()=>group,divIcon:value=>value,marker(_position,options){const element=d.createElement('div');element.tabIndex=0;const marker=events({options,getElement:()=>element,bindPopup(content,options){this.content=content;this.popup={options:{autoPan:true,...options}};return this;},getPopup(){return this.popup;},isPopupOpen(){return map.popup===this;},openPopup(){this.autoPanDuringOpen=this.popup.options.autoPan;map.closePopup();map.popup=this;this.fire('popupopen');return this;}});markers.push(marker);return marker;},latLngBounds:()=>({extend(){},isValid:()=>true})};
 const ctx={window:{L,matchMedia:()=>({matches:false}),requestAnimationFrame:fn=>frames.push(fn),setTimeout:()=>1},L,document:d,DEFAULT_CENTER:{lat:40.4,lng:49.8},DEFAULT_ZOOM:12,SCRIPT_CONFIG:{},createHomeBasemapLayer:()=>events({addTo(){}}),hasValidCoordinates:p=>Number.isFinite(p.lat)&&Number.isFinite(p.lng),buildDynamicMarkerSvg:()=>'',renderPopupContent:p=>p.name,pointMembers:p=>p.members||[p],getFilterState:()=>({}),hasActiveFilters:()=>false,businessCount:points=>points.reduce((sum,p)=>sum+p.members.length,0),updateLiveCount(){},setMapNote(){},bindFilterListeners(){},serverFilterUpdater:()=>()=>{},scrollToMap(){},homePaging:{viewport:bounds=>viewports.push(bounds)},homeExplorer:{selectPoint(p){if(!(p.members||[p]).some(m=>m.id===selected))selected=(p.members||[p])[0].id;},getSelectedMemberId:()=>selected,selectMember(id){selected=id;},clearSelection(){selected=null;}},homeSelectionGeneration:0,pendingFocusPlaceId:null,activeMapFocusHandler:null};
 vm.createContext(ctx);const start=source.indexOf('  function mountLeafletMap('),end=source.indexOf('  function safeHomeMapUrl(');vm.runInContext(source.slice(start,end),ctx);
 const state={mapEl:d.getElementById('map'),mapNoteEl:d.getElementById('note'),places:initial};Object.defineProperties(state.mapEl,{clientWidth:{value:size.width},clientHeight:{value:size.height}});assert.equal(ctx.mountLeafletMap(state),true);
 return{ctx,state,map,markers,viewports,get selected(){return selected;},select(id){selected=id;ctx.activeMapFocusHandler(id);},close(){dom.window.close();}};
}
test('late viewport results retain an open Leaflet popup for the same selected member',async()=>{
 const t=leafletLifecycle();t.select(1);assert.ok(t.map.popup);await tick();
 t.state.applyPage([point(1)],{bounds:{south:40,west:49,north:41,east:50}});
 assert.ok(t.map.popup,'viewport refresh must not discard the open popup');assert.equal(t.map.popup.options.title,'Place 1');assert.equal(t.map.popup.getElement().getAttribute('aria-expanded'),'true');assert.equal(t.map.popup.autoPanDuringOpen,true,'native bounded auto-pan keeps restored edge popups reachable');assert.equal(t.map.popup.getPopup().options.autoPan,true,'future user opens retain native auto-pan');
 t.state.applyPage([point(1),point(2)],{append:true,bounds:null});assert.ok(t.map.popup,'pagination retains the selected popup');t.close();
});
test('filter reset, result removal and explicit close do not resurrect Leaflet popups',()=>{
 const t=leafletLifecycle();t.select(1);t.state.applyPage([point(1)],{bounds:null,append:false});assert.equal(t.map.popup,null,'filter refresh closes popup');assert.equal(t.selected,null,'filter refresh clears stale card selection');
 t.select(1);t.state.applyPage([point(2)],{bounds:{south:40}});assert.equal(t.map.popup,null,'removed member is not restored');
 t.select(2);t.map.closePopup();t.state.applyPage([point(2)],{bounds:{south:40}});assert.equal(t.map.popup,null,'explicit close persists across viewport refresh');t.close();
});

test('viewport popup restoration follows selected shared-venue member when point identity changes',()=>{
 const t=leafletLifecycle([point(1,[member(1),member(2)])]);t.select(2);
 const replacement=point(5,[member(2,'Updated member two'),member(5)]);t.state.applyPage([replacement],{bounds:{south:40}});
 assert.ok(t.map.popup);assert.equal(t.selected,2);assert.equal(t.map.popup.options.title,'Updated member two');t.close();
});

test('Leaflet popup geometry leaves room for marker and controls on compact maps',()=>{
 for(const size of [{width:244,height:430},{width:314,height:430},{width:680,height:560},{width:240,height:240}]){
  const t=leafletLifecycle([point(1)],size),options=t.markers[0].getPopup().options;
  assert.ok(Number.isFinite(options.maxHeight),'content height is bounded before the native auto-pan calculation');
  assert.ok(options.maxHeight>0 && options.maxHeight<=size.height-110,'popup content leaves vertical room for its marker and chrome');
  assert.ok(options.maxWidth>0 && options.maxWidth<=size.width-32,'popup fits map width with safe edge spacing');
  assert.ok(options.minWidth<=options.maxWidth);assert.deepEqual(Array.from(options.autoPanPadding),[16,16]);t.close();
 }
});

test('showing the map panel invalidates Leaflet size synchronously before a card reveal',()=>{
 const t=leafletLifecycle();const before=t.map.invalidations||0;
 t.state.mapEl.dispatchEvent(new t.state.mapEl.ownerDocument.defaultView.Event('kidsmap:home-map-visible'));
 assert.equal(t.map.invalidations,before+1,'must not defer hidden-panel geometry repair to a later frame');t.close();
});
test('Leaflet card reveal, popup auto-pan and manual camera movement never filter homepage results',()=>{
 const t=leafletLifecycle([point(1),point(2)]);
 try {
  t.select(1);t.map.fire('moveend');t.map.fire('zoomend');
  t.map.fire('autopanstart');t.map.fire('moveend');
  t.map.fire('movestart',{originalEvent:{type:'pointermove'}});t.map.fire('moveend');
  t.map.fire('zoomstart',{originalEvent:{type:'wheel'}});t.map.fire('zoomend');
  assert.equal(t.viewports.length,0,'camera navigation must not replace the search result set with viewport results');
  assert.equal(t.selected,1);assert.ok(t.map.popup);
 } finally {t.close();}
});

function guideMotion(reduced=false) {
 const dom=new JSDOM('<aside data-home-map-guide><img></aside>',{runScripts:'outside-only',pretendToBeVisual:true});
 const w=dom.window,el=w.document.querySelector('aside');let reveal,disconnects=0;
 w.matchMedia=()=>({matches:reduced,addEventListener(){}});
 w.IntersectionObserver=class{constructor(cb){reveal=cb;}observe(){}disconnect(){disconnects++;}};
 w.eval(source.slice(source.indexOf('  function initHomeMapGuideMotion('),source.indexOf('  function createHomeMapExplorer(')));
 w.initHomeMapGuideMotion(el);
 return{w,el,reveal:()=>reveal([{isIntersecting:true}]),disconnects:()=>disconnects,close:()=>w.close()};
}
test('guide reveals once, cleans up finite motion and greets on pointer entry',()=>{
 const t=guideMotion();t.reveal();assert.ok(t.el.classList.contains('is-guide-entering'));assert.equal(t.disconnects(),1);
 t.el.dispatchEvent(new t.w.Event('animationend',{bubbles:true}));assert.equal(t.el.classList.contains('is-guide-entering'),false);
 t.el.dispatchEvent(new t.w.Event('pointerenter'));assert.ok(t.el.classList.contains('is-guide-greeting'));
 t.el.dispatchEvent(new t.w.Event('animationend',{bubbles:true}));assert.equal(t.el.classList.contains('is-guide-greeting'),false);t.close();
});
test('guide reduced motion suppresses reveal and hover motion',()=>{
 const t=guideMotion(true);t.el.dispatchEvent(new t.w.Event('pointerenter'));assert.equal(t.el.className,'');t.close();
});

// Native SDK transport is substituted; the production homepage mounting and
// camera/selection event handlers run unchanged.
function googleLifecycle(initial=[point(1),point(2)]){
 const vm=require('node:vm'),dom=new JSDOM('<div id="map"></div><p id="note"></p>');
 const d=dom.window.document,viewports=[],timers=[],markers=[],reveals=[];
 function events(target={}){const handlers={};return Object.assign(target,{addListener(name,fn){(handlers[name]||=[]).push(fn);return{remove(){handlers[name]=handlers[name].filter(item=>item!==fn);}};},fire(name){(handlers[name]||[]).slice().forEach(fn=>fn());}});}
 const map=events({zoom:12,center:{lat:40.4,lng:49.8},getCenter(){return{lat:()=>this.center.lat,lng:()=>this.center.lng};},getZoom(){return this.zoom;},setCenter(center){this.center=center;},setZoom(zoom){this.zoom=zoom;this.fire('zoom_changed');},getBounds:()=>({getSouthWest:()=>({lat:()=>40,lng:()=>49}),getNorthEast:()=>({lat:()=>41,lng:()=>50})})});
 const popup=events({close(){this.opened=false;},setOptions(){},setContent(content){this.content=content;},open(){this.opened=true;}});
 const google={maps:{Map:function(){return map;},InfoWindow:function(){return popup;},ControlPosition:{RIGHT_TOP:1},event:{addListenerOnce(_map,_event,fn){reveals.push(fn);}}}};
 const ctx={window:{google,setTimeout:fn=>timers.push(fn),KidsMapGoogleMotion:{create:()=>({cancel(){},select(){}}),chooser:()=>({close(){},show(){}}),reduced:()=>false}},google,document:d,DEFAULT_CENTER:{lat:40.4,lng:49.8},DEFAULT_ZOOM:12,SCRIPT_CONFIG:{},hasValidCoordinates:p=>Number.isFinite(p.lat)&&Number.isFinite(p.lng),buildGoogleMarkerIcon:()=>({}),renderPopupContent:p=>p.name,pointMembers:p=>p.members||[p],getFilterState:()=>({}),businessCount:points=>points.reduce((n,p)=>n+p.members.length,0),updateLiveCount(){},setMapNote(){},bindFilterListeners(){},serverFilterUpdater:()=>()=>{},scrollToMap(){},homePaging:{viewport:bounds=>viewports.push(bounds)},homeExplorer:{selectPoint(p){ctx.selected=p.members[0].id;}},homeSelectionGeneration:0,pendingFocusPlaceId:null,activeMapFocusHandler:null};
 ctx.window.kidsMapCreateGoogleMarker=()=>{const marker=events({setMap(){}});markers.push(marker);return marker;};
 vm.createContext(ctx);vm.runInContext(source.slice(source.indexOf('  function mountGoogleMap('),source.indexOf('  // ── Coordinate helpers')),ctx);
 const state={mapEl:d.getElementById('map'),mapNoteEl:d.getElementById('note'),places:initial};ctx.mountGoogleMap(state);timers.splice(0).forEach(fn=>fn());
 return{ctx,state,map,popup,viewports,select(id){ctx.activeMapFocusHandler(id);map.fire('idle');reveals.splice(0).forEach(fn=>fn());},close(){dom.window.close();}};
}
test('Google wheel or keyboard gestures cannot turn a later card selection into a viewport filter',()=>{
 for(const gesture of ['wheel','keydown','dragstart']){
  const t=googleLifecycle();
  try {
   if(gesture==='dragstart')t.map.fire(gesture);
   else t.state.mapEl.dispatchEvent(new t.state.mapEl.ownerDocument.defaultView.Event(gesture));
   t.select(2);t.map.fire('idle');
   assert.equal(t.viewports.length,0,gesture+' must not shrink or reorder the homepage search results');
   assert.equal(t.ctx.selected,2);assert.equal(t.popup.opened,true);
  } finally {t.close();}
 }
});
test('repeated card selections preserve every result node and its order',()=>{
 const t=setup([point(1,[member(1),member(2)]),point(3)]);
 try {
  const before=[...t.d.querySelectorAll('[data-home-map-list] li')];
  const list=t.d.querySelector('[data-home-map-list]');list.scrollTop=120;
  for(const id of ['2','3','1','2']){
   t.d.querySelector('[data-home-map-member-id="'+id+'"]').click();
   assert.deepEqual([...list.children],before);
   assert.equal(t.d.querySelectorAll('[data-home-map-member-id][aria-pressed="true"]').length,1);
   assert.equal(list.scrollTop,120);
  }
  assert.equal(t.requests.length,0,'selection alone must not fetch new results');
 } finally {t.close();}
});
