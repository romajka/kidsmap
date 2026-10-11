/* LOCAL QA ADAPTER ONLY. No SDK, tile geography, clustering or Google claims. */
(() => {
 class MVC {constructor(){this.events={};}addListener(n,f){(this.events[n]??=[]).push(f);return{remove:()=>{this.events[n]=this.events[n].filter(x=>x!==f);}};}}
 const trigger=(o,n,...a)=>(o.events?.[n]||[]).forEach(f=>f(...a));
 class LatLng {constructor(a,b){this.a=typeof a==='object'?(typeof a.lat==='function'?a.lat():a.lat):a;this.b=typeof a==='object'?(typeof a.lng==='function'?a.lng():a.lng):b;}lat(){return this.a;}lng(){return this.b;}toJSON(){return{lat:this.a,lng:this.b};}}
 class Bounds {constructor(){this.p=[];}extend(p){this.p.push(new LatLng(p));return this;}getCenter(){return this.p[0]||new LatLng(40.41,49.87);}getNorthEast(){return this.getCenter();}getSouthWest(){return this.getCenter();}}
 class MapView extends MVC {
  constructor(el,options){super();this.el=el;this.center=new LatLng(options.center);this.zoom=options.zoom;this.overlays=[];el.innerHTML='';el.style.background='#e8eee4';el.style.position='relative';const label=document.createElement('p');label.textContent='SIMULATED local adapter — no map SDK or tiles';label.style.cssText='position:absolute;top:8px;left:10px;pointer-events:none;font-size:12px';el.append(label);this.pane=document.createElement('div');this.pane.style.cssText='position:absolute;inset:0;pointer-events:auto';el.append(this.pane);}
  getDiv(){return this.el;}getCenter(){return this.center;}getZoom(){return this.zoom;}getRenderingType(){return'RASTER';}get(){return false;}getBounds(){return new Bounds().extend(this.center);}
  getProjection(){return{fromLatLngToPoint:p=>({x:p.lng(),y:p.lat()}),fromPointToLatLng:p=>new LatLng(p.y,p.x)};}
  project(p){return{x:this.el.clientWidth/2+(p.lng()-this.center.lng())*2500,y:this.el.clientHeight/2+(p.lat()-this.center.lat())*2500};}
  redraw(){this.overlays.forEach(o=>o.draw?.());}
  panTo(p){this.center=new LatLng(p);this.redraw();trigger(this,'idle');}setCenter(p){this.panTo(p);}setZoom(z){this.zoom=z;trigger(this,'zoom_changed');}moveCamera(o){if(o.center)this.center=new LatLng(o.center);if(o.zoom)this.zoom=o.zoom;this.redraw();trigger(this,'idle');}fitBounds(b){this.center=b.getCenter();this.redraw();trigger(this,'idle');}setOptions(){}
 }
 class Overlay extends MVC {setMap(map){if(this.map)this.onRemove?.();this.map=map;if(map){map.overlays.push(this);this.onAdd?.();this.draw?.();}}getPanes(){return{overlayMouseTarget:this.map.pane,overlayLayer:this.map.pane};}getProjection(){return{fromLatLngToDivPixel:p=>this.map.project(p),fromLatLngToContainerPixel:p=>this.map.project(p)};}}
 class Marker extends MVC {constructor(o){super();this.pos=new LatLng(o.position);this.map=o.map||null;this.z=o.zIndex;}getPosition(){return this.pos;}setPosition(p){this.pos=new LatLng(p);}getMap(){return this.map;}setMap(m){this.map=m;trigger(this,'map_changed');}getZIndex(){return this.z;}setZIndex(z){this.z=z;trigger(this,'zindex_changed');}setIcon(){}setVisible(){}setAnimation(){}}
 window.google={maps:{Map:MapView,Marker,MVCObject:MVC,OverlayView:Overlay,LatLng,LatLngBounds:Bounds,Size:class{constructor(width,height){this.width=width;this.height=height;}},Point:class{constructor(x,y){this.x=x;this.y=y;}},ControlPosition:{RIGHT_TOP:1},event:{trigger,addListener:(o,n,f)=>o.addListener(n,f),addListenerOnce:(o,n,f)=>o.addListener(n,f)}}};window.markerClusterer={dummy:true};
})();
