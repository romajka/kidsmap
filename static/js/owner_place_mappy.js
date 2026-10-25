/* Desktop-only form companion. Readiness comes from the existing server check. */
(() => {
  'use strict';
  const mounted = new WeakMap();
  const language = (document.documentElement.lang || 'az').slice(0, 2);
  const copy = ({
    ru: {start:'Давайте добавим ваше место',hint:'Начните с названия. Остальное заполним по шагам.',writing:'Хорошо получается!',remaining:n=>`Осталось ${n} обязательных пунктов. Можно сохранить и продолжить позже.`,ready:'Готово к отправке!',review:'Посмотрите предпросмотр — и можно отправлять на проверку.',check:'Проверим пару деталей',error:'Исправьте отмеченные поля. Всё введённое останется в форме.'},
    az: {start:'Məkanınızı əlavə edək',hint:'Addan başlayın. Qalanını addım-addım doldurarıq.',writing:'Əla gedir!',remaining:n=>`${n} məcburi bənd qalıb. Saxlayıb sonra davam edə bilərsiniz.`,ready:'Göndərməyə hazırdır!',review:'Ön baxışı yoxlayın, sonra yoxlamaya göndərin.',check:'Bir neçə detalı yoxlayaq',error:'İşarələnmiş sahələri düzəldin. Yazdıqlarınız formada qalacaq.'},
    en: {start:'Let’s add your place',hint:'Start with its name. We’ll take the rest step by step.',writing:'Looking good!',remaining:n=>`${n} required items left. You can save and continue later.`,ready:'Ready to send!',review:'Take a look at the preview, then send it for review.',check:'Let’s check a few details',error:'Check the highlighted fields. Your entries stay in the form.'}
  })[language] || null;
  function mount(root) {
    if (!root) return null;
    if (mounted.has(root)) return mounted.get(root);
    const image = root.querySelector('[data-mappy-sprite]'), button = root.querySelector('[data-pc-mappy-wave]');
    const title = root.querySelector('[data-pc-mappy-title]'), caption = root.querySelector('[data-pc-mappy-caption]');
    if (!image || !copy) return null;
    const desktop = matchMedia('(min-width: 961px)'), reduced = matchMedia('(prefers-reduced-motion: reduce)');
    let waveTimer = null, hasGreeted = false, loaded = false, state = null;
    const setText = (node, value) => { if (node && node.textContent !== value) node.textContent = value; };
    function stop() { clearTimeout(waveTimer); waveTimer = null; root.classList.remove('is-waving'); }
    function wave() {
      if (!desktop.matches || reduced.matches || document.hidden || !loaded || root.hasAttribute('data-fallback')) return;
      stop(); root.classList.add('is-waving'); waveTimer = setTimeout(stop, 1950);
    }
    function syncMedia() {
      if (!desktop.matches || reduced.matches || document.hidden) stop();
      if (desktop.matches && !image.hasAttribute('src')) image.src = root.dataset.sprite;
    }
    function onLoad() {
      loaded = true;
      if (!hasGreeted && desktop.matches) { hasGreeted = true; if (state === 'welcome') wave(); }
    }
    function onError() {
      stop();
      if (root.hasAttribute('data-fallback')) return;
      root.setAttribute('data-fallback', ''); image.src = root.dataset.welcome;
    }
    function update(readiness, pending) {
      if (pending) return; // Keep the confirmed pose while the person is typing.
      const total = Number(readiness.required_count) || 0, done = Number(readiness.completed_count) || 0;
      const next = readiness.is_ready ? 'ready' : readiness.error_count ? 'check' : done ? 'writing' : 'welcome';
      if (state !== next) { stop(); state = next; root.dataset.pose = next; }
      setText(title, next === 'ready' ? copy.ready : next === 'check' ? copy.check : next === 'writing' ? copy.writing : copy.start);
      setText(caption, next === 'ready' ? copy.review : next === 'check' ? copy.error : next === 'writing' ? copy.remaining(Math.max(0,total-done)) : copy.hint);
    }
    const listeners = [[desktop,'change',syncMedia],[reduced,'change',syncMedia],[document,'visibilitychange',syncMedia],[image,'load',onLoad],[image,'error',onError],[button,'click',wave]];
    listeners.forEach(([target,event,handler]) => target?.addEventListener?.(event,handler));
    const controller = {update,destroy(){stop();listeners.forEach(([target,event,handler])=>target?.removeEventListener?.(event,handler));mounted.delete(root);}};
    mounted.set(root,controller); update({required_count:0,completed_count:0,is_ready:false},false);syncMedia();
    return controller;
  }
  window.KidsMapOwnerMappy = {mount};
})();
