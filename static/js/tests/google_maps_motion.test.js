'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function setup({reduced=false,vector=true}={}) {
 const frames=new Map(), listeners={}, domListeners={}; let id=0;
 const map={zoom:11,center:{lat:()=>40,lng:()=>49},moves:[],fits:0,
 getZoom(){return this.zoom},getCenter(){return this.center},getRenderingType(){return vector?'VECTOR':'RASTER'},get(){return vector},
 getDiv(){return {clientWidth:390,clientHeight:500,addEventListener(n,fn){domListeners[n]=fn}}},
 addListener(n,fn){listeners[n]=fn;return {remove(){delete listeners[n]}}},
 moveCamera(p){this.moves.push(p);this.zoom=p.zoom;this.center={lat:()=>p.center.lat,lng:()=>p.center.lng}},
 fitBounds(bounds){this.fits++;this.lastBounds=bounds},getProjection(){return {fromLatLngToPoint(p){return {x:p.lng(),y:p.lat()}},fromPointToLatLng(p){return {lat:()=>p.y,lng:()=>p.x}}}}};
 const scope={window:{matchMedia:()=>({matches:reduced,addEventListener(){}})},document:{addEventListener(){}},performance:{now:()=>0},requestAnimationFrame(fn){frames.set(++id,fn);return id},cancelAnimationFrame(id){frames.delete(id)},google:{maps:{Point:function(x,y){this.x=x;this.y=y},LatLng:function(p){this.lat=()=>p.lat;this.lng=()=>p.lng},LatLngBounds:function(sw,ne){this.getSouthWest=()=>sw;this.getNorthEast=()=>ne}}},Map,Set,Math};
 const file='static/js/google_maps_motion.js';if(fs.existsSync(file))vm.runInNewContext(fs.readFileSync(file,'utf8'),scope);
 function tick(t){const callbacks=[...frames.values()];frames.clear();callbacks.forEach(fn=>fn(t));}
 return {api:scope.window.KidsMapGoogleMotion,map,frames,domListeners,tick};
}
test('new camera target cancels old work; manual input leaves no scheduled frames',()=>{
 const s=setup();assert.ok(s.api,'Shared cancellable camera controller is missing');const c=s.api.create(s.map);
 c.moveTo({center:{lat:41,lng:50},zoom:14});s.tick(100);c.moveTo({center:{lat:42,lng:51},zoom:15});assert.equal(s.frames.size,1);
 s.domListeners.wheel({});assert.equal(s.frames.size,0);const count=s.map.moves.length;s.tick(700);assert.equal(s.map.moves.length,count);
});
test('vector camera finishes at target without zooming out or leaving a loop',()=>{
 const s=setup();assert.ok(s.api);const c=s.api.create(s.map);c.moveTo({center:{lat:41,lng:50},zoom:15});
 [0,130,260,390,520,900].forEach(s.tick);assert.equal(s.map.zoom,15);assert.equal(s.frames.size,0);
 assert.ok(s.map.moves.every((m,i,a)=>i===0||m.zoom>=a[i-1].zoom));
});
test('reduced motion uses one instant camera update',()=>{
 const s=setup({reduced:true});assert.ok(s.api);s.api.create(s.map).moveTo({center:{lat:41,lng:50},zoom:15});assert.equal(s.frames.size,0);assert.equal(s.map.moves.length,1);
});
test('coincident cluster offers places instead of moving their real coordinates or zooming',()=>{
 const s=setup();assert.ok(s.api);const a={getPosition:()=>({lat:()=>40,lng:()=>49})},b={getPosition:()=>({lat:()=>40,lng:()=>49})};let choices;
 s.api.create(s.map).expand({markers:[a,b]},items=>choices=items);assert.equal(choices.length,2);assert.equal(s.map.moves.length,0);assert.equal(s.map.fits,0);
});
test('membership delta preserves unchanged markers and renders once per change',()=>{
 const s=setup();assert.ok(s.api);const a={},b={},c={};let removes=[],adds=[],renders=0;
 const cluster={removeMarkers(ms,noDraw){removes.push(...ms);assert.equal(noDraw,true)},addMarkers(ms,noDraw){adds.push(...ms);assert.equal(noDraw,true)},render(){renders++}};
 const update=s.api.membership(cluster);update([a,b]);adds=[];update([b,c]);assert.deepEqual(removes,[a]);assert.deepEqual(adds,[c]);assert.equal(renders,2);update([b,c]);assert.equal(renders,2);
});

test('nearly coincident native fit uses expanded camera bounds, capped at useful zoom',()=>{
 const s=setup({vector:false});assert.ok(s.api);
 const sw={lat:()=>40,lng:()=>49},ne={lat:()=>40.000001,lng:()=>49.000001};
 const bounds={getSouthWest:()=>sw,getNorthEast:()=>ne};
 const markers=[{getPosition:()=>sw},{getPosition:()=>ne}];
 s.api.create(s.map).expand({markers,bounds},()=>assert.fail('Near points can still zoom'));
 assert.equal(s.map.fits,1);
 assert.notEqual(s.map.lastBounds,bounds,'Native fit must not jump to maximum zoom');
 assert.ok(s.map.lastBounds.getNorthEast().lng()-s.map.lastBounds.getSouthWest().lng()>.0001,'Expand camera footprint while leaving marker positions exact');
 assert.equal(markers[0].getPosition().lat(),40);
});
