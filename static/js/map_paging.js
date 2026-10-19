/* Bounded, explicit map loading shared by both public map views. */
(() => {
  'use strict';
  function merge(previous, incoming) {
    const points = new Map(previous.map(point => [point.key || String(point.id), {...point, members: [...(point.members || [point])]}]));
    incoming.forEach(point => {
      const key = point.key || String(point.id), existing = points.get(key);
      if (!existing) points.set(key, {...point, members: [...(point.members || [point])]});
      else {
        const ids = new Set(existing.members.map(member => member.id));
        (point.members || [point]).forEach(member => { if (!ids.has(member.id)) { existing.members.push(member); ids.add(member.id); } });
      }
    });
    return [...points.values()];
  }
  function create({control, initial, getParams, onChange}) {
    const status = control.querySelector('[data-map-status]'), button = control.querySelector('[data-map-more]');
    let points = merge([], initial.points || []), count = initial.count || 0;
    let cursor = initial.next_cursor, more = !!initial.has_more, bounds = null;
    let viewportKey = null;
    let generation = 0, controller = null, busy = false, failed = null, timer = null, destroyed = false;
    function render() {
      const shown = points.reduce((sum, point) => sum + point.members.length, 0);
      status.textContent = failed ? control.dataset.errorLabel : (control.dataset.shownLabel || '{shown} / {total}').replace('{shown}', shown).replace('{total}', count);
      button.hidden = !more && !failed;
      button.disabled = busy;
      button.textContent = busy ? control.dataset.loadingLabel || '…' : failed ? control.dataset.retryLabel || 'Retry' : control.dataset.moreLabel || 'More';
      control.setAttribute('aria-busy', busy ? 'true' : 'false');
    }
    async function request(append, windowBounds) {
      if (destroyed) return;
      const current = ++generation;
      if (controller) controller.abort();
      controller = new AbortController(); busy = true; failed = null; render();
      const params = new URLSearchParams(getParams());
      params.delete('after');
      ['south','west','north','east'].forEach(name => params.delete(name));
      if (windowBounds) Object.entries(windowBounds).forEach(([key,value]) => params.set(key,String(value)));
      if (append && cursor !== null && cursor !== undefined) params.set('after',String(cursor));
      try {
        const response = await fetch(control.dataset.mapEndpoint + '?' + params, {signal:controller.signal, credentials:'same-origin', headers:{Accept:'application/json'}});
        if (!response.ok) throw new Error('Map request failed');
        const payload = await response.json();
        if (!Array.isArray(payload.points) || !Number.isFinite(payload.count)) throw new Error('Invalid map response');
        if (current !== generation || destroyed) return;
        points = merge(append ? points : [], payload.points); count = payload.count;
        cursor = payload.next_cursor; more = !!payload.has_more; bounds = windowBounds;
        onChange(points, {count, append, bounds});
      } catch (error) {
        if (current !== generation || destroyed || error.name === 'AbortError') return;
        failed = {append, bounds:windowBounds};
      } finally {
        if (current === generation && !destroyed) { busy = false; render(); }
      }
    }
    const api = {
      get points() { return points; }, get count() { return count; },
      replace(nextBounds=null) { clearTimeout(timer); timer=null; if (!nextBounds) viewportKey=null; return request(false,nextBounds); },
      more() { if (busy) return Promise.resolve(); const retry=failed; return request(retry ? retry.append : true,retry ? retry.bounds : bounds); },
      viewport(nextBounds) { const key=JSON.stringify(Object.values(nextBounds).map(v=>Number(v).toFixed(5))); if (key===viewportKey) return; viewportKey=key; clearTimeout(timer); timer=setTimeout(() => api.replace(nextBounds),300); },
      destroy() { destroyed=true; generation++; clearTimeout(timer); controller?.abort(); button.removeEventListener('click',click); },
    };
    function click() { api.more(); }
    button.addEventListener('click',click);render();return api;
  }
  window.KidsMapPaging = {create};
})();
