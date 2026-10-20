/* KidsMap Mascot Companion · Dynamic tips, playful reactions, accessible guidance */
(function () {
  const key = 'kidsmap:mappy:hidden';

  const TIPS = {
    ru: [
      "Выберите район и возраст — покажу занятия на карте! 🗺️",
      "Ищете спорт, творчество или шахматы? Помогу найти рядом! 🎨",
      "Более 70 проверенных секций и кружков для детей в Баку! 🧸",
      "Точное расписание и цены в одном месте — без лишних звонков! ⏱️",
      "Нажмите на любое место или метку — всё подробно покажу! ✨"
    ],
    az: [
      "Rayon və yaşı seçin — xəritədə uyğun məşğələləri göstərim! 🗺️",
      "İdman, yaradıcılıq, yoxsa şahmat? Yaxınlıqdakı dərnəkləri tapmağa kömək edərəm! 🎨",
      "Bakıda uşaqlar üçün 70-dən çox yoxlanılmış məkan! 🧸",
      "Dəqiq cədvəl və qiymətlər — artıq zənglərə ehtiyac yoxdur! ⏱️",
      "Xəritədə istənilən məkana toxunun — dərhal ətraflı göstərim! ✨"
    ],
    en: [
      "Choose an area and age — I’ll show you great activities on the map! 🗺️",
      "Looking for sports, arts, or chess? I’ll help you find them nearby! 🎨",
      "Over 70 verified kids’ places and clubs across Baku! 🧸",
      "Schedules, age groups, and prices all in one place! ⏱️",
      "Tap any pin on the map — I’ll show you all the details! ✨"
    ]
  };

  function start() {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    document.querySelectorAll('[data-mappy-helper]').forEach(function (helper) {
      if (helper.dataset.ready) return;
      const content = helper.querySelector('[data-mappy-content]');
      const dismiss = helper.querySelector('[data-mappy-dismiss]');
      const restore = helper.querySelector('[data-mappy-restore]');
      if (!content || !dismiss || !restore) return;
      helper.dataset.ready = 'true';

      let timer;
      function stop() { clearTimeout(timer); content.classList.remove('mappy-enter'); }
      function enter() {
        stop();
        if (reduced.matches || document.hidden || content.hidden) return;
        content.classList.add('mappy-enter');
        timer = setTimeout(stop, 850);
      }
      function setHidden(hidden, moveFocus) {
        stop(); content.hidden = hidden; restore.hidden = !hidden;
        if (moveFocus) (hidden ? restore : dismiss).focus({preventScroll: true});
      }

      let hidden = false;
      try { hidden = sessionStorage.getItem(key) === '1'; } catch (_) { /* storage is optional */ }
      setHidden(hidden, false);

      dismiss.addEventListener('click', function () {
        try { sessionStorage.setItem(key, '1'); } catch (_) {}
        setHidden(true, true);
      });
      restore.addEventListener('click', function () {
        try { sessionStorage.removeItem(key); } catch (_) {}
        setHidden(false, true); enter();
      });

      document.addEventListener('visibilitychange', stop);
      reduced.addEventListener('change', stop);
      enter();

      // Dynamic rotating tips & cheerful cartoon reaction
      const textEl = helper.querySelector('[data-mappy-text]') || content.querySelector('p');
      if (textEl) {
        const docLang = (document.documentElement.lang || 'ru').toLowerCase().slice(0, 2);
        const tips = TIPS[docLang] || TIPS.ru;
        let tipIndex = 0;
        let rotationTimer = null;

        function cycleTip() {
          if (document.hidden || reduced.matches || content.hidden) return;
          tipIndex = (tipIndex + 1) % tips.length;
          textEl.classList.add('is-switching');
          setTimeout(function () {
            textEl.textContent = tips[tipIndex];
            textEl.classList.remove('is-switching');
            content.classList.remove('mappy-react');
            if (typeof content.offsetWidth === 'number') void content.offsetWidth;
            content.classList.add('mappy-react');
          }, 220);
        }

        function startRotation() {
          stopRotation();
          rotationTimer = setInterval(cycleTip, 6500);
          if (rotationTimer && typeof rotationTimer.unref === 'function') {
            rotationTimer.unref();
          }
        }

        function stopRotation() {
          if (rotationTimer) {
            clearInterval(rotationTimer);
            rotationTimer = null;
          }
        }

        startRotation();
        document.addEventListener('visibilitychange', function () {
          if (document.hidden) stopRotation();
          else startRotation();
        });

        // Click bubble or mascot to playfully cycle tips
        const bubble = helper.querySelector('.mappy-bubble');
        if (bubble) {
          bubble.addEventListener('click', function () {
            cycleTip();
            startRotation();
          });
        }
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
