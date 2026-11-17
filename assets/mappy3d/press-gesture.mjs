// A tap is completed only by its own pointer, without scrolling or dragging.
export function bindPressGesture(target, { pick, start, release, cancel, threshold = 12 }) {
  let active = null;
  const pointer = (event) => event.pointerId ?? 0;
  const moved = (event) => Math.hypot(event.clientX - active.x, event.clientY - active.y) > threshold;
  function abort() {
    if (!active) return;
    active = null;
    cancel();
  }
  function down(event) {
    if (active || event.isPrimary === false || (event.button != null && event.button !== 0)) return;
    const hit = pick(event);
    if (!hit) return;
    active = { id: pointer(event), x: event.clientX, y: event.clientY, hit };
    start(hit);
  }
  function move(event) {
    if (active && pointer(event) === active.id && moved(event)) abort();
  }
  function up(event) {
    if (!active || pointer(event) !== active.id) return;
    if (moved(event)) return abort();
    const { hit } = active;
    active = null;
    release(hit);
  }
  function canceled(event) {
    if (active && pointer(event) === active.id) abort();
  }
  const handlers = { pointerdown: down, pointermove: move, pointerup: up, pointercancel: canceled, scroll: abort };
  for (const [name, handler] of Object.entries(handlers)) target.addEventListener(name, handler, { capture: true, passive: true });
  return () => {
    abort();
    for (const [name, handler] of Object.entries(handlers)) target.removeEventListener(name, handler, true);
  };
}
