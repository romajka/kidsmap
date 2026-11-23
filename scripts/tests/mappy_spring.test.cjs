const { test } = require('node:test');
const assert = require('node:assert/strict');

test('press and ear springs settle even when the render budget is six frames per second', async () => {
  const { advanceSpring } = await import('../../assets/mappy3d/spring.mjs');
  for (const [stiffness, damping] of [[520, 17], [160, 9]]) {
    const state = { v: 0, vel: 0 };
    for (const target of [1, 0]) {
      for (let i = 0; i < 18; i++) {
        advanceSpring(state, target, stiffness, damping, 1 / 6);
        assert.ok(Math.abs(state.v) < 2, 'the model must retain its proportions');
      }
      assert.ok(Math.abs(state.v - target) < 0.001);
    }
  }
});
