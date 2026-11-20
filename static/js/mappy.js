/* KidsMap Mascot Companion · Dynamic tips, playful reactions, accessible guidance */
(function () {
  const key = 'kidsmap:mappy:hidden';

  const TIPS = {
    ru: [
      "Выберите район и возраст — покажу занятия на карте!",
      "Ищете спорт, творчество или шахматы? Помогу найти рядом!",
      "Кружки, парки и развлечения — найдите место для ребёнка!",
      "Перед посещением уточните цену и расписание у организатора.",
      "Нажмите на любое место или метку — всё подробно покажу!"
    ],
    az: [
      "Rayon və yaşı seçin — xəritədə uyğun məşğələləri göstərim!",
      "İdman, yaradıcılıq, yoxsa şahmat? Yaxınlıqdakı dərnəkləri tapmağa kömək edərəm!",
      "Dərnəklər, parklar və əyləncə — uşağınız üçün məkan tapın!",
      "Getməzdən əvvəl qiyməti və cədvəli təşkilatçı ilə dəqiqləşdirin.",
      "Xəritədə istənilən məkana toxunun — dərhal ətraflı göstərim!"
    ],
    en: [
      "Choose an area and age — I’ll show you great activities on the map!",
      "Looking for sports, arts, or chess? I’ll help you find them nearby!",
      "Clubs, parks and entertainment — find a place for your child!",
      "Confirm prices and schedules with the organizer before visiting.",
      "Tap any pin on the map — I’ll show you all the details!"
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
        const tips = (TIPS[docLang] || TIPS.ru).slice();
        if (document.querySelector('[data-mappy-specialists]')) {
          tips.splice(1, 0, ({
            ru: "Ищете логопеда, репетитора или психолога? Теперь они тоже есть на KidsMap!",
            az: "Loqoped, repetitor və ya psixoloq axtarırsınız? Onlar artıq KidsMap-dədir!",
            en: "Looking for a speech therapist, tutor or psychologist? They're on KidsMap now!"
          })[docLang] || "");
          if (!tips[1]) tips.splice(1, 1);
        }
        let tipIndex = 0;
        let rotationTimer = null;
        let switchTimer = null;
        let sleeping = false;

        function cancelSwitch() {
          clearTimeout(switchTimer);
          textEl.classList.remove('is-switching');
        }

        function cycleTip() {
          if (sleeping || document.hidden || content.hidden) return;
          cancelSwitch();
          tipIndex = (tipIndex + 1) % tips.length;
          if (reduced.matches) {
            textEl.textContent = tips[tipIndex];
            return;
          }
          textEl.classList.add('is-switching');
          switchTimer = setTimeout(function () {
            textEl.textContent = tips[tipIndex];
            textEl.classList.remove('is-switching');
            content.classList.remove('mappy-react');
            if (typeof content.offsetWidth === 'number') void content.offsetWidth;
            content.classList.add('mappy-react');
          }, 220);
        }

        function startRotation() {
          stopRotation();
          if (sleeping || reduced.matches || document.hidden) return;
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
        // A reaction from the 3D bear owns the cloud until the next full tip interval.
        helper.addEventListener('mappy:say', function () {
          cancelSwitch();
          startRotation();
        });
        helper.addEventListener('mappy:sleep', function () {
          sleeping = true;
          cancelSwitch();
          stopRotation();
          content.classList.remove('mappy-react');
        });
        helper.addEventListener('mappy:wake', function () {
          sleeping = false;
          startRotation();
        });
        reduced.addEventListener('change', function () {
          cancelSwitch();
          startRotation();
        });
        document.addEventListener('visibilitychange', function () {
          if (document.hidden) stopRotation();
          else startRotation();
        });

        function nextTip() {
          cycleTip();
          startRotation();
        }
        helper.querySelector('.mappy-bubble')?.addEventListener('click', nextTip);
        const portrait = helper.querySelector('[data-mappy3d]');
        let pressedOnPicture = false;
        portrait?.addEventListener('pointerdown', function (event) {
          if (event.isPrimary !== false && event.button === 0) pressedOnPicture = !portrait.mappy?.ready;
        });
        portrait?.addEventListener('click', function (event) {
          if (!portrait.mappy?.ready || (pressedOnPicture && event.detail > 0)) nextTip();
          pressedOnPicture = false;
        });
      }
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, {once: true});
  else start();
})();
