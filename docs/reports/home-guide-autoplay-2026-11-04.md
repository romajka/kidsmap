# Гиды: автопрокрутка по умолчанию

LOCAL / APPROVED IMPLEMENT, 2026-11-04. Пользователь явно запросил автоматическое движение ленты и более заметную анимацию. Предыдущее решение без горизонтальной автопрокрутки заменено.

Первый плавный переход через1.8s после появления блока; следующий через3.6s после завершения прокрутки. На конце плавное возвращение к началу. Без DOM-клонов и новых зависимостей. Кнопка паузы останавливает таймер и движение; ручные стрелки/свайп/клавиатура сохранены. Hover над лентой, касание, keyboard focus-visible, скрытая страница, уход блока за экран и reduced-motion блокируют автоматическое перелистывание. Наведение больше не замораживает парение всех карточек: только выбранную. Парение усилено с3до5px, цикл4.8s. Ничего не движется автоматически при reduced-motion.

18Node tests PASS: новый RED→GREEN default-autoplay regression, pause/reduced, прежние navigation/focus/guide-anchor тесты. Diff-check с cr-at-eol PASS. Independent browser-qa guide_motion_review подтвердил ПК1440 autoplay0→402, Resume402→753, конец→начало; mobile390 touch-context0→268 и свайп268→501. Пауза/hover/keyboard/touch/reduce/offscreen стабильны4.2–4.3s, нет overflow/pageerror; evidence `.tmp/home-guide-autoplay-20261104/agent-review.md`. В пользовательской существующей IAB вкладке после reload подтверждены JSauto_v1, reducedMotion=false, motionstate=running.

Локальные изменения: home_guide_slider.js, стили анимации секции home_layout.css, версии ассетов home.html, targeted JS tests. Параллельные изменения hero/home и другие грязные файлы сохранены. Прежний cache URL home_layout от другого изменения обновлён уникальным guide_auto_v2, чтобы пользователь получил свежие стили. Production/commit/push/deploy не выполнялись. Физические телефоны/Safari/Firefox NOT RUN.

Browser hidden-tab state отдельно не проверен (обработчик реализован). Видео недоступно из-за отсутствующего bundledffmpeg; ничего не устанавливалось. Локальный preview8896 оставлен работающим.
