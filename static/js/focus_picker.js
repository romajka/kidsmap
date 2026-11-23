/* Focus point picker for event posters (admin + organizer cabinet).
   The photo is shown whole (contain); a click or drag sets the point, measured
   against the real picture inside the frame, not the frame. Live previews show
   how 1:1, 4:3, 16:9 and 3:4 crops will look. Works with mouse, pen and touch;
   arrow keys move the point by 1% (Shift: 10%). */
(() => {
  'use strict';
  const clamp = v => Math.max(0, Math.min(100, Math.round(v)));

  function init(root) {
    if (root.dataset.kmFocusReady) return;
    root.dataset.kmFocusReady = '1';
    const stage = root.querySelector('[data-km-focus-stage]');
    const img = root.querySelector('[data-km-focus-img]');
    const dot = root.querySelector('[data-km-focus-dot]');
    const inX = root.querySelector('[data-km-focus-x] input, input[data-km-focus-x]');
    const inY = root.querySelector('[data-km-focus-y] input, input[data-km-focus-y]');
    const previews = Array.from(root.querySelectorAll('[data-km-focus-preview]'));
    const empty = root.querySelector('[data-km-focus-empty]');
    if (!stage || !img || !dot || !inX || !inY) return;
    let x = clamp(inX.value === '' ? 50 : +inX.value), y = clamp(inY.value === '' ? 50 : +inY.value);

    // The picture's box inside the contain frame.
    function content() {
      const box = stage.getBoundingClientRect();
      const nw = img.naturalWidth, nh = img.naturalHeight;
      if (!nw || !nh) return { left: 0, top: 0, width: box.width, height: box.height, box };
      const scale = Math.min(box.width / nw, box.height / nh);
      const w = nw * scale, h = nh * scale;
      return { left: (box.width - w) / 2, top: (box.height - h) / 2, width: w, height: h, box };
    }
    function render() {
      const c = content();
      dot.style.left = `${c.left + c.width * x / 100}px`;
      dot.style.top = `${c.top + c.height * y / 100}px`;
      dot.setAttribute('aria-valuetext', `${x}% × ${y}%`);
      previews.forEach(p => { p.style.objectPosition = `${x}% ${y}%`; });
    }
    function set(nx, ny, fromInput) {
      x = clamp(nx); y = clamp(ny);
      if (!fromInput) {
        inX.value = x; inY.value = y;
        inX.dispatchEvent(new Event('change', { bubbles: true }));
      }
      render();
    }
    function fromPointer(e) {
      const c = content();
      set((e.clientX - c.box.left - c.left) / c.width * 100, (e.clientY - c.box.top - c.top) / c.height * 100);
    }
    function setSource(src) {
      const has = Boolean(src);
      root.classList.toggle('has-photo', has);
      if (empty) empty.hidden = has;
      if (!has) return;
      img.src = src;
      previews.forEach(p => { p.src = src; });
    }
    let dragging = false;
    stage.addEventListener('pointerdown', e => {
      if (!root.classList.contains('has-photo') || e.button > 0) return;
      dragging = true; stage.setPointerCapture(e.pointerId); fromPointer(e); dot.focus({ preventScroll: true });
      e.preventDefault();
    });
    stage.addEventListener('pointermove', e => { if (dragging) fromPointer(e); });
    const stop = () => { dragging = false; };
    stage.addEventListener('pointerup', stop);
    stage.addEventListener('pointercancel', stop);
    dot.addEventListener('keydown', e => {
      const step = e.shiftKey ? 10 : 1;
      const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (e.key === 'Home') { e.preventDefault(); set(50, 50); return; }
      if (!moves[e.key]) return;
      e.preventDefault(); set(x + moves[e.key][0], y + moves[e.key][1]);
    });
    [inX, inY].forEach(input => input.addEventListener('input', () => set(inX.value === '' ? x : +inX.value, inY.value === '' ? y : +inY.value, true)));
    img.addEventListener('load', render);
    window.addEventListener('resize', render);
    if ('ResizeObserver' in window) new ResizeObserver(render).observe(stage);

    // A new file picked in the related input: preview it and start from the centre.
    const fileInput = root.dataset.fileInput
      ? document.querySelector(root.dataset.fileInput)
      : root.closest('[data-gallery-card]')?.querySelector('input[type="file"]');
    if (fileInput) {
      fileInput.addEventListener('change', () => {
        const file = fileInput.files && fileInput.files[0];
        if (!file || !/^image\//.test(file.type)) return;
        setSource(URL.createObjectURL(file));
        set(50, 50);
      });
    }
    setSource(root.dataset.src || '');
    render();
  }

  const scan = scope => (scope || document).querySelectorAll('[data-km-focus]').forEach(init);
  scan();
  // Gallery cards are added and <details> open later: initialise lazily.
  document.addEventListener('toggle', e => { if (e.target.open) scan(e.target); }, true);
  let queued = false;
  if ('MutationObserver' in window) new MutationObserver(() => {
    if (queued) return; queued = true;
    requestAnimationFrame(() => { queued = false; scan(); });
  }).observe(document.body, { childList: true, subtree: true });
})();
