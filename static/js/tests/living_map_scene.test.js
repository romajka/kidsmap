'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const file = 'static/js/living_map_scene.js';
const scope = {window:{},Math};
if (fs.existsSync(file)) vm.runInNewContext(fs.readFileSync(file,'utf8'),scope);
const scene = scope.window.KidsMapLivingScene;

test('scene connects visible destinations outside protected content', () => {
  assert.ok(scene, 'Living map needs a destination/route scene, not only particles');
  const masks=[{left:70,right:650,top:180,bottom:650},{left:780,right:1360,top:220,bottom:680}];
  const routes=scene.create({width:1440,height:2200,bands:[130,760,1480],masks});
  assert.ok(routes.length>=3);
  assert.ok(routes[0].points.at(-1).x-routes[0].points[0].x>700, 'Hero route must read across open space');
  assert.ok(routes.flatMap(r=>r.nodes).some(n=>n.kind==='map'));
  assert.ok(routes.some(r=>r.bottom-r.top>500), 'The map must continue around the hero, not look like separate horizontal dividers');
  for(const route of routes)for(const n of route.nodes){
    assert.ok(n.x>=20&&n.x<=1420,'Destination must stay in viewport');
    assert.ok(!masks.some(r=>n.x+20>r.left&&n.x-20<r.right&&n.y+20>r.top&&n.y-20<r.bottom),'Destination must not collide with content');
  }
});
test('route visibly grows, reaches its destination, and fades before repeating', () => {
  assert.ok(scene);
  const a=scene.timeline(1000,0),b=scene.timeline(4500,0),c=scene.timeline(8500,0);
  assert.ok(b.progress>a.progress+.3,'A visitor must see the route advance within a few seconds');
  assert.equal(c.progress,1);
  assert.ok(scene.timeline(11999,0).opacity<.01,'Cycle must not snap back at full opacity');
});
test('reduced motion shows a complete, stable journey',()=>{
  assert.ok(scene);
  const a=scene.timeline(10,3,true),b=scene.timeline(9000,3,true);
  assert.deepEqual(a,b);assert.equal(a.progress,1);assert.equal(a.opacity,1);
});
test('the traveling light interpolates between route samples instead of jumping',()=>{
  assert.equal(typeof scene.pointAt,'function');
  const point=scene.pointAt([{x:0,y:0},{x:100,y:50}],.25);
  assert.equal(point.x,25);assert.equal(point.y,12.5);
});
test('mobile destinations fit even when only narrow vertical gaps remain',()=>{
  assert.ok(scene);
  const routes=scene.create({width:390,height:1800,bands:[95,900,1500],masks:[{left:18,right:372,top:160,bottom:850}]});
  assert.ok(routes.length>0);
  for(const route of routes)for(const n of route.nodes)assert.ok(n.x>=20&&n.x<=370);
});

test('vertical journeys span a long page and enter the footer, with safe landmarks',()=>{
  assert.equal(typeof scene.createVertical,'function');
  const masks=[{left:70,right:1370,top:180,bottom:6500}];
  const routes=scene.createVertical({width:1440,top:900,bottom:6800,gutter:70,masks});
  assert.equal(routes.length,2);
  for(const route of routes){
    assert.equal(route.points[0].y,900);
    assert.equal(route.points.at(-1).y,6800);
    assert.ok(route.nodes.length>=4,'Landmarks must continue below the hero');
    for(const n of route.nodes)assert.ok(!masks.some(r=>n.x+n.radius>r.left&&n.x-n.radius<r.right&&n.y+n.radius>r.top&&n.y-n.radius<r.bottom));
    assert.ok(route.points.at(-1).x>=70&&route.points.at(-1).x<=1370,'Trail must turn into the footer');
  }
});
test('narrow screens keep continuous side trails without squeezing icons into content',()=>{
  const routes=scene.createVertical({width:390,top:120,bottom:4200,gutter:14,masks:[{left:14,right:376,top:100,bottom:4300}]});
  assert.equal(routes.length,2);
  for(const route of routes){
    assert.equal(route.nodes.length,0);
    assert.ok(route.points.every(p=>p.x>=0&&p.x<=390));
    assert.equal(route.points.at(-1).y,4200);
  }
});

test('footer turns have a continuous tangent and finish horizontally even in wide gutters',()=>{
  for(const [width,gutter] of [[390,14],[1440,70],[1920,310],[2560,630]]){
    for(const route of scene.createVertical({width,top:120,bottom:3000,gutter,masks:[]})){
      const points=route.points.filter(p=>p.y>2500);
      const angles=points.slice(1).map((p,i)=>Math.atan2(p.y-points[i].y,Math.abs(p.x-points[i].x)));
      const maxJump=Math.max(...angles.slice(1).map((a,i)=>Math.abs(a-angles[i])));
      assert.ok(maxJump<.12,`Visible corner at width ${width}: ${maxJump} radians`);
      assert.ok(angles.at(-1)<.06,`Footer entry must end horizontally: ${width}`);
    }
  }
});

test('traveling light uses distance along the curved footer route',()=>{
  assert.equal(typeof scene.pointAtDistance,'function');
  const route=scene.createVertical({width:1920,top:120,bottom:3000,gutter:310,masks:[]})[0];
  const length=route.distances.at(-1);
  for(let d=length-260;d<length-20;d+=10){
    const a=scene.pointAtDistance(route,d),b=scene.pointAtDistance(route,d+10);
    const step=Math.hypot(b.x-a.x,b.y-a.y);
    assert.ok(step>9.8&&step<=10.01,`Light must not jump/accelerate through the bend: ${step}`);
  }
});
