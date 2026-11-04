const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
let JSDOM;
try { ({JSDOM} = require('jsdom')); }
catch { ({JSDOM} = require('../../.tmp/coordinate-location/dom/node_modules/jsdom')); }
const script = path.join(__dirname, '../../static/js/specialist_detail.js');
const source = fs.existsSync(script) ? fs.readFileSync(script, 'utf8') : '';

function setup(payload, provider = true) {
  const dom = new JSDOM('<div id="specialist-map" hidden></div><p data-specialist-map-fallback>Map unavailable; see address above.</p><script id="specialist-map-locations" type="application/json"></script>', {runScripts:'outside-only', url:'http://localhost/ru/specialists/test/'});
  const w=dom.window, calls={maps:[],markers:[],windows:[],bounds:[]};
  w.document.getElementById('specialist-map-locations').textContent=typeof payload==='string'?payload:JSON.stringify(payload);
  function installProvider() {
    w.google={maps:{
      Map:class {constructor(element,options){this.element=element;this.options=options;calls.maps.push(this);}fitBounds(bounds,padding){this.fit={bounds,padding};}},
      LatLngBounds:class {extend(position){calls.bounds.push(position);}},
      InfoWindow:class {constructor(options){this.options=options;calls.windows.push(this);}open(options){this.opened=options;}}
    }};
    w.kidsMapCreateGoogleMarker=options=>{const marker={options,addListener(type,handler){this[type]=handler;}};calls.markers.push(marker);return marker;};
  }
  if(provider)installProvider();
  Object.defineProperty(w.document,'readyState',{value:'complete'});
  w.eval(source);
  return {dom,w,calls,installProvider};
}

test('untrusted place names and addresses remain literal DOM text in map popups',()=>{
  const name='<img src=x onerror="window.injected=1">',address='<svg onload="window.injected=2">Street</svg>';
  const t=setup([{lat:40.4,lng:49.86,place_name:name,address}]);
  assert.equal(typeof t.w.kidsMapInitSpecialistMap,'function');
  const content=t.calls.windows[0].options.content;
  assert.equal(content.nodeType,1);
  assert.equal(content.querySelector('img,svg,script'),null);
  assert.equal(content.querySelector('strong').textContent,name);
  assert.equal(content.querySelector('p').textContent,address);
  t.calls.markers[0].click();
  assert.equal(t.calls.windows[0].opened.anchor,t.calls.markers[0]);
  assert.equal(t.w.injected,undefined);t.dom.window.close();
});

test('zero coordinates are valid and repeated callbacks never create duplicate maps',()=>{
  const t=setup([{lat:0,lng:0,place_name:'Zero',address:'Equator'}]);
  assert.equal(typeof t.w.kidsMapInitSpecialistMap,'function');
  t.w.kidsMapInitSpecialistMap();t.w.kidsMapInitSpecialistMap();
  assert.equal(t.calls.maps.length,1);assert.equal(t.calls.markers.length,1);
  assert.equal(t.calls.maps[0].options.center.lat,0);assert.equal(t.calls.maps[0].options.center.lng,0);
  assert.equal(t.w.document.getElementById('specialist-map').hidden,false);t.dom.window.close();
});

test('provider arriving after DOM initialization replaces the fallback successfully',()=>{
  const t=setup([{lat:40.4,lng:49.86,place_name:'Office',address:'Street'}],false);
  assert.equal(typeof t.w.kidsMapInitSpecialistMap,'function');
  assert.equal(t.w.document.querySelector('[data-specialist-map-fallback]').hidden,false);
  t.installProvider();t.w.kidsMapInitSpecialistMap();
  assert.equal(t.calls.maps.length,1);
  assert.equal(t.w.document.querySelector('[data-specialist-map-fallback]').hidden,true);t.dom.window.close();
});

test('invalid coordinates and malformed payloads preserve the readable fallback',()=>{
  for(const payload of ['{bad JSON',{},[],[{lat:null,lng:2}],[{lat:'40,4',lng:49.86}],[{lat:91,lng:180}]]){
    const t=setup(payload);
    assert.equal(typeof t.w.kidsMapInitSpecialistMap,'function');
    assert.equal(t.calls.maps.length,0);
    assert.equal(t.w.document.querySelector('[data-specialist-map-fallback]').hidden,false);t.dom.window.close();
  }
});

test('multiple locations fit numeric coordinates with valid padding',()=>{
  const t=setup([{lat:40.4,lng:49.86},{lat:40.5,lng:49.9}]);
  assert.equal(typeof t.w.kidsMapInitSpecialistMap,'function');
  assert.equal(t.calls.markers.length,2);assert.equal(t.calls.bounds.length,2);
  assert.equal(t.calls.maps[0].fit.padding,30);t.dom.window.close();
});
