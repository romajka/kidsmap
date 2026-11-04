# Лента гидов: компактность и спокойное движение

LOCAL / APPROVED IMPLEMENT, 2026-11-04. По запросу пользователя подключён независимый browser-qa (`guide_motion_review`), lead выполнял изменения. Применены KidsMap UI/frontend-design/fixing-accessibility и Playwright.

Удалены непонятный диапазон карточек, custom progress и видимая нативная полоса. Native scroll сохранён: свайп/трекпад, стрелки, Home/End и Tab. Стрелки и кнопка паузы компактно находятся под карточками. Уменьшены padding/gap и высота иллюстраций, сохранены реальные пять направлений и все ссылки. На≤360px CTA краткий «Гид / Guide / Bələdçi», полный accessible name сохранён; минимальная зона44×44px.

Карточки мягко парят вертикально на3px с разными фазами, цикл5.6s. Горизонтальная автопрокрутка отсутствует. Есть явная постоянная пауза; движение также останавливается при hover, keyboard focus, touch/pointer, прокрутке ленты, уходе секции за экран, скрытом документе и reduced-motion. БезJS анимации выключены, native scroll/links работают. Pause/Resume после клика не застревает из-за обычного pointer focus: остановка по CSS применяется к :focus-visible.

Lead:16Node tests PASS (slider motion/navigation +existing guide anchors); diff-check с cr-at-eol PASS. Скриншоты desktop1440/mobile390/320 просмотрены. ВысотаRU блока1440:556px вместо669;390:646 вместо789;320:700. Функциональный JS без backend/schema изменений.

Независимая проверка:21 сочетание AZ/RU/EN ×320/360/390/768/1024/1280/1440 без overflow/pageerror/local400, старых индикаторов нет, native scrollbar hidden. Normal/reduced motion, pause/resume/hover/keyboard/pointer/offscreen, Home/End,1и15карточек. После финальной правки повторены6узких состояний и pointerResume+keyboardFocus. Агент выявил и lead исправил retained focus после Resume и слишком узкуюRUCTA. Подробные evidence/точная граница проверки: `.tmp/home-guide-refine-20261104/agent-review.md`.

Evidence root: `.tmp/home-guide-refine-20261104/`; screenshots `output/playwright/home-guide-refined-{1440,390,320}.png`. Пользовательская существующая IAB вкладка обновлена, новая не создавалась. Прежний/параллельный dirty work сохранён. Production/commit/push/deploy, реальные телефоны/Safari/Firefox NOT RUN. Standalone localhost8896 продолжает работать.
