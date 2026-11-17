const {test} = require('node:test');
const assert = require('node:assert/strict');
const gestureModule = import('../../assets/mappy3d/press-gesture.mjs');

async function setup() {
  const {bindPressGesture} = await gestureModule;
  const listeners = new Map(), calls = [];
  const target = {
    addEventListener(name, handler) { listeners.set(name, handler); },
    removeEventListener(name, handler) { if (listeners.get(name) === handler) listeners.delete(name); },
  };
  const cleanup = bindPressGesture(target, {
    pick: event => event.hit === false ? null : {zone:'belly'},
    start: () => calls.push('start'),
    release: () => calls.push('react'),
    cancel: () => calls.push('cancel'),
  });
  function emit(name, values = {}) {
    listeners.get(name)?.({pointerId:1,clientX:40,clientY:50,button:0,isPrimary:true,...values});
  }
  return {emit, calls, cleanup, listeners};
}

test('a completed tap reacts exactly once', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointerup'); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','react']); s.cleanup();
});
test('pointer cancellation releases the press without a reaction', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointercancel'); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','cancel']); s.cleanup();
});
test('scrolling over the bear does not tickle him', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('scroll'); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','cancel']); s.cleanup();
});
test('a drag cancels the tap even if the pointer returns', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointermove',{clientY:90}); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','cancel']); s.cleanup();
});
test('a release beyond the tap threshold cancels without a move event', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointerup',{clientX:80});
  assert.deepEqual(s.calls,['start','cancel']); s.cleanup();
});
test('a small finger movement still completes a tap', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointermove',{clientX:44,clientY:53}); s.emit('pointerup',{clientX:44,clientY:53});
  assert.deepEqual(s.calls,['start','react']); s.cleanup();
});
test('a second pointer cannot start, release, or cancel the first tap', async () => {
  const s=await setup(); s.emit('pointerdown'); s.emit('pointerdown',{pointerId:2,isPrimary:false});
  s.emit('pointerup',{pointerId:2}); s.emit('pointercancel',{pointerId:2}); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','react']); s.cleanup();
});
test('a miss and a secondary mouse button do not activate the bear', async () => {
  const s=await setup(); s.emit('pointerdown',{hit:false}); s.emit('pointerup'); s.emit('pointerdown',{button:2}); s.emit('pointerup');
  assert.deepEqual(s.calls,[]); s.cleanup();
});
test('destroying the gesture clears a held press and all listeners', async () => {
  const s=await setup(); s.emit('pointerdown'); s.cleanup(); s.emit('pointerup');
  assert.deepEqual(s.calls,['start','cancel']); assert.equal(s.listeners.size,0);
});
