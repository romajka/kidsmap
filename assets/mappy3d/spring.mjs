// A slow render frame can cover many physics steps. Draw once after integrating the spring.
export function advanceSpring(state, target, stiffness, damping, dt) {
  const steps = Math.ceil(dt * 60);
  if (steps <= 0) return;
  const step = dt / steps;
  for (let i = 0; i < steps; i++) {
    const acceleration = (target - state.v) * stiffness - state.vel * damping;
    state.vel += acceleration * step;
    state.v += state.vel * step;
  }
}
