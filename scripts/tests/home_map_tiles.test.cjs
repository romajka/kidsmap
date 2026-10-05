const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const {test} = require('node:test');
const source = fs.readFileSync('static/js/home_map.js', 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
function setup(fetch) {
  const start=source.indexOf('  function loadHomeMapTile('), end=source.indexOf('  function createHomeBasemapLayer(');
  assert.ok(start>=0 && end>start, 'Safe HTTP tile loader is not implemented');
  const revoked=[],created=[];
  const context={fetch,AbortController,Error,window:{setTimeout,clearTimeout},URL:{
    createObjectURL(blob){created.push(blob);return 'blob:checked-tile';},
    revokeObjectURL(url){revoked.push(url);}
  }};
  vm.createContext(context);vm.runInContext(source.slice(start,end),context);
  return {...context,revoked,created};
}
test('successful tile is displayed only after checked response, with origin-only referrer and normal caching',async()=>{
  let request;const blob={image:true};
  const c=setup(async(url,options)=>{request={url,options};return {ok:true,blob:async()=>blob};});
  const tile={},completed=[];
  const dispose=c.loadHomeMapTile(tile,'https://tile.openstreetmap.org/11/1307/772.png',(error,t)=>completed.push({error,t}));
  await flush();assert.equal(tile.src,'blob:checked-tile');assert.deepEqual(c.created,[blob]);
  assert.equal(request.options.referrerPolicy,'strict-origin-when-cross-origin');
  assert.equal(request.options.credentials,'omit');assert.equal(request.options.cache,undefined);
  tile.onload();assert.equal(completed.length,1);assert.equal(completed[0].error,null);assert.equal(completed[0].t,tile);
  assert.deepEqual(c.revoked,['blob:checked-tile']);dispose();assert.equal(c.revoked.length,1);
});
test('HTTP 403 with a decodable image body never becomes a visible tile',async()=>{
  let readBody=false;const c=setup(async()=>({ok:false,status:403,blob:async()=>{readBody=true;return {};}}));
  const tile={},errors=[];const dispose=c.loadHomeMapTile(tile,'https://tile.openstreetmap.org/1/1/1.png',error=>errors.push(error));
  await flush();assert.equal(tile.src,undefined);assert.equal(readBody,false);assert.equal(c.created.length,0);
  assert.equal(errors.length,1);assert.match(errors[0].message,/403/);dispose();
});
test('network failure reports unavailable instead of rendering a broken tile',async()=>{
  const c=setup(async()=>{throw new Error('offline');});const tile={},errors=[];
  const dispose=c.loadHomeMapTile(tile,'https://tile.openstreetmap.org/1/1/1.png',error=>errors.push(error));
  await flush();assert.equal(tile.src,undefined);assert.equal(errors.length,1);assert.match(errors[0].message,/offline/);dispose();
});
test('unloaded tile cancels pending transport and ignores late response without allocating a blob',async()=>{
  let resolve,signal;const c=setup((_url,options)=>{signal=options.signal;return new Promise(r=>resolve=r);});
  const tile={},calls=[];const dispose=c.loadHomeMapTile(tile,'https://tile.openstreetmap.org/1/1/1.png',e=>calls.push(e));
  dispose();assert.equal(signal.aborted,true);resolve({ok:true,blob:async()=>({})});await flush();
  assert.equal(tile.src,undefined);assert.equal(c.created.length,0);assert.equal(calls.length,0);
});
