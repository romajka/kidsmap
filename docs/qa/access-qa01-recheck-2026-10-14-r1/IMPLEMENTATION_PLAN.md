# ACCESS-QA-01 — управление фокусом окна восстановления

> Для исполнителя: выполнять последовательно в этом чате после явного одобрения этого документа. Новые агенты и Git-действия не нужны. Шаги отмечать по фактическому результату.

**Цель:** удерживать клавиатурный фокус в открытом reset modal и возвращать его на фактический opener после закрытия, включая loading и success.

**Архитектура:** сохранить существующий modal/AJAX controller в login.html. Добавить локальное управление focus и inert; не заменять диалог библиотекой или отдельным backend.

**Стек:** текущие Django 6.0.2 templates, vanilla JavaScript, существующие CSS, Chromium 153.0.8010.36, собственный PostgreSQL 17.10.

**Spec:** [guide PLAN ACCESS-QA-01](../continuation-and-repair-prompts-2026-10-11.md#repair-ACCESS-QA-01), [техническое задание](../module07-2026-10-10-r1/repair-ACCESS-QA-01.txt), [свежий REPORT](REPORT.md).

## Границы

- Единственный подтверждённый ID этого scope: **ACCESS-QA-01, P2, SOURCE**, остаётся OPEN до GREEN.
- Checkout `/home/ramin/kidsmap`; `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + чужой dirty WORKTREE; `active_run: NONE`.
- До patch перепроверить snapshot и SHA login.html `efc1949f5ed1e136bf0b22e0f56a900b852ad2afdde39c48570d44ac4b10423b`. Чужой новый diff сохранить и оценить, не откатывать.
- Никаких commit/push/deploy/production/reset/clean/stash; active_run не занимать; чужие стенды/процессы/артефакты сохранить.
- Проверки только DJANGO_TESTING=1, собственные PostgreSQL/cache/media/private-media/email и fresh sole LOCALE_PATHS. Checkout .env и production credentials не загружать.
- Сохранить href standalone reset fallback, identifier prefill/preservation, fetch URL/CSRF/JSON, empty/network errors, disabled/spinner, тексты RU/AZ/EN и CSS transitions.
- ACCESS02/04/05 требуют отдельных планов. ACCESS03=ORG02 уже принят в module02; повторный patch по старому FAIL запрещён. ACCEPT-07 после всех задач; module08 не начинать.
- После patch только targeted/affected checks. Полный module07 corpus один раз после его задач; глобальный корпус отдельно.

## Точные файлы

**Изменить в приложении только:** `/home/ramin/kidsmap/src/catalog/templates/auth/login.html` — разметка диалога около строк192–279 и controller около292–451.

**Создать/обновить только QA:** в новом уникальном `/home/ramin/kidsmap/docs/qa/access-qa01-fix-2026-10-14-r1/` файлы `runtime.py`, `settings.py`, `qa_urls.py`, `drive.py`, `focus-matrix.js`, `reset-flow.js`, `verify.py`, `REPORT.md`, `verification.json`, `commands.jsonl`, `png-manifest.json`, `screenshots/*.png`. Если путь уже существует, выбрать r2 и явно записать его. Исходный recheck и RED артефакты не перезаписывать. В guide `docs/qa/continuation-and-repair-prompts-2026-10-11.md` добавить только текущий status/link.

CSS, PO/MO, backend, schema, API, permissions, существующие test assertions — без изменений. Внешний вид уже помещается во всех18 cells. Существующие focus ring/input и close background применять как есть. Если свежий браузер докажет, что их недостаточно, отдельный точный CSS scope предъявить до расширения.

## Причина и минимальный diff

В controller нет Tab/focusin guard, сохранения opener или inert фона. Initial focus отложен на80ms и не отменяется. Loading отключает focused submit; success скрывает form controls. Opener — `<a>`: Enter работает, Space прокручивает страницу. Это один контракт управления клавиатурой, а не новые auth/data ошибки.

### Задача 1: локальный focus lifecycle

- [ ] Зафиксировать RED по старому неизменённому snapshot: `focus-matrix.js.result.json`162 observations54PASS/108FAIL; reset45 observations36PASS/9FAIL. Протокол сохранять как baseline, не переписывать ожидания.
- [ ] Добавить `tabindex="-1" inert` на `#resetPasswordModal`; дать existing success heading ID `resetModalSuccessTitle`. Существующие локализованные тексты не менять.
- [ ] Сохранить opener из `event.currentTarget` и предыдущее inert каждого body sibling. Modal уже переносится в body; сам modal, SCRIPT/STYLE/LINK исключить. Восстановить именно прежние значения, а не безусловно снимать inert со всего body.
- [ ] Открытие: прежние prefill/form/error действия → `modal.inert=false`, active/aria-hidden/body class → focus email синхронно с `preventScroll`, select только при open и заполненном identifier → inert siblings. Удалить80ms timeout; CSS transition остаётся. Не отложенный focus после закрытия.
- [ ] При закрытии: inactive → вернуть прежний inert фона → фокус actual opener, если connected и доступен → modal inert/aria-hidden. Все close controls, Escape и backdrop используют один closeModal; повторный close безопасен.
- [ ] Установить dynamic Tab/Shift+Tab handler только для активного modal. Каждый keydown пересчитывает видимые, enabled controls; disabled loading submit и скрытый form/success исключаются. Первый↔последний замыкаются, внешний focus возвращается в диалог, отсутствие controls даёт focus modal.
- [ ] Добавить focusin guard только для активного modal: попытка фокуса на фоне возвращает его к доступному control диалога. Guard не работает после close и не меняет остальные страницы.
- [ ] Добавить Space keydown на existing opener link: preventDefault и openModal; Enter остаётся native click. Сохранить реальный href для fallback без JS.

Ядро предлагаемого поведения (внутри текущего IIFE):

```javascript
var modalOpener = null;
var backgroundState = [];
function isModalOpen() { return modal && modal.classList.contains('is-active'); }
function availableControls() {
  return Array.from(modal.querySelectorAll('a[href],button,input,select,textarea,[tabindex]'))
    .filter(function (node) {
      return !node.disabled && node.tabIndex >= 0 && !node.closest('[inert]') &&
        node.getClientRects().length && getComputedStyle(node).visibility !== 'hidden';
    });
}
function focusAvailable(preferred) {
  if (!isModalOpen()) return;
  var nodes = availableControls();
  var target = nodes.includes(preferred) ? preferred : (nodes[0] || modal);
  target.focus({preventScroll: true});
}
// active keydown branch; Escape still calls closeModal.
if (e.key === 'Tab') {
  var nodes = availableControls(), first = nodes[0], last = nodes[nodes.length - 1];
  var current = document.activeElement;
  if (!nodes.length) { e.preventDefault(); modal.focus({preventScroll:true}); }
  else if (!nodes.includes(current) || (e.shiftKey && current === first) || (!e.shiftKey && current === last)) {
    e.preventDefault(); (e.shiftKey ? last : first).focus({preventScroll:true});
  }
}
```

### Задача 2: focus при AJAX states

- [ ] В setLoading сохранить факт focus submit до disabled. Если отключение убрало focus из диалога, focusAvailable(emailInput); input/select не сбрасывать. Не трогать disabled/spinner semantics.
- [ ] При actual success после скрытия формы/показа success переключить aria-labelledby на existing success heading и focus на `.km-modal-success-btn`, только если modal сейчас открыт. При новом open вернуть `resetModalTitle`.
- [ ] Error/empty/network сохраняют текущие localized сообщения и identifier; focus trap снова вычисляет доступные controls. Late response после close не вызывает focus на скрытом modal. AJAX transport и response handling не менять.
- [ ] Быстрое open→Escape→open, close во время loading, success→close→open проверять отдельно: focus не уходит на hidden controls/фон, inert не остаётся после закрытия.

### Задача 3: targeted GREEN и отчёт

- [ ] Создать собственный fix profile с новым loopback PostgreSQL/DB/cookies/cache/media/private-media/filebased email; manifest current PO до django.setup, source/loaded-template proof, transport guard. Старый стенд не переиспользовать без provenance и не перезапускать.
- [ ] Запустить unchanged nine tests: `.venv/bin/python docs/qa/<fix-run>/runtime.py test catalog.testcases.test_password_reset`. Expected9PASS, native exit0. Это impacted reset contract, не весь модуль.
- [ ] Реальный Chromium18 cells RU/AZ/EN×360/390/768/1024/1280/1440: достичь opener клавиатурой, Enter/Space, полный Tab/Shift+Tab цикл, background focus refusal, Escape/крестик/backdrop, opener restoration, input preservation, repeated/rapid opening, visible focus, geometry и PNG. Assertions проверяют actual activeElement и controls; не наличие строки кода.
- [ ] Во всех18 cells проверить empty/filled, disabled loading и динамический список focusable, success keyboard close/reopen, AJAX400 и network refusal. HTTP400 и delayed/failed transport явно SIMULATED; actual successful reset POST выполняет приложение.
- [ ] Полный user path на RU/AZ/EN390 и1440: own local mail → настоящий link → native новый пароль → старый отказ/новый login → replay denial. Ссылки/пароли/cookies только ignored scratch или in-memory, не в evidence. Confirmation/done/invalid страницы — affected shared scenarios.
- [ ] Собрать console/pageerrors/network: intentional blocked/400 отдельно, неожиданные local/static errors недопустимы. Просмотреть originals PC/mobile/errors/loading/success; сохранить PNG manifest с SHA/dimensions.
- [ ] Новые целевые native regression scripts оставить воспроизводимыми; GREEN сравнить с неизменённым RED. Full module/global tests здесь не запускать.
- [ ] Проверить приложение diff только login.html, чужие hashes/HEAD/branch/active_run/process/container preservation, source runtime и свежесть sole locale manifest; сохранить REPORT/verification/commands/exits/counts/NOT RUN. Закрыть только ACCESS-QA-01 при всех целевых acceptance; иначе OPEN/NOT RUN.

## Риски и зависимости

- Existing body sibling inert необходимо восстановить после всех способов close; body целиком inert делать нельзя — он содержит modal.
- Hiding/disabling focused element требует явного выбора нового видимого control. Не фокусировать закрытый dialog из pending promise.
- Не сохранять статичный список кнопок: form и success/loading различаются.
- Opener link сохраняет no-JS navigation; Space handling ограничен этим opener.
- Не менять shared CSS ради данной страницы без нового browser evidence/scope. Реальные screen readers/Firefox/Safari/physical devices остаются NOT RUN, Chromium ограничен указанной matrix.
- ACCESS-QA-03: template/JS/API/service byte-identical принятому module02; CSS после той приёмки отличается. Нового network defect этим recheck не обнаружено, сетевой lifecycle заново не запускался; полнота этой части проверяется ACCEPT-07, отдельный patch сейчас не нужен.

**Одобрение:** «Одобряю IMPLEMENTATION_PLAN.md из docs/qa/access-qa01-recheck-2026-10-14-r1, только ACCESS-QA-01 и перечисленные файлы, без commit/push/deploy/production». Согласование нужно по прямому ограничению пользователя и guide IMPLEMENT-APPROVAL; текущий запуск разрешает только recheck/план.
