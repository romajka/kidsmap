# Yandex Metrica Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Подключить Яндекс Метрику к публичному KidsMap и измерять попытки связаться с организациями, сохранив существующую GA4.

**Architecture:** Независимый выключенный по умолчанию счётчик, серверный gate публичных страниц и один JS-мост от существующего `kidsMapEmitAnalyticsEvent`. Вебвизор включается только после проверки маскирования в кабинете и локальных privacy-проверок. Частные разделы и авторизованные сеансы в первую версию не входят.

**Tech Stack:** Существующий Django, vanilla JavaScript, Yandex Metrica tag, Django tests, Node `node:test`.

**Spec:** `docs/superpowers/plans/2026-10-20-yandex-metrica.md#request-and-acceptance` — запрос пользователя и acceptance ниже.

**Execution:** Inline, без запуска субагентов. Наличие рекомендации в заголовке не даёт разрешения менять приложение или развёртывать его.

## Request and acceptance

Пользователь попросил настроить Яндекс Метрику для KidsMap. Предложен счётчик, цели телефона/WhatsApp, карты кликов и Вебвизор со скрытием ввода.

Первоначально в аккаунте было три счётчика других сайтов. После явного подтверждения пользователя «да делай» соглашение принято и создан отдельный счётчик KidsMap.az: **113691893**. Сохранены домен kidsmap.az, только указанные адреса без поддоменов, Баку UTC+04:00 и AZN. Цели: phone_click (672705940), whatsapp_click (672706031). «Записывать все поля» выключено; автоцели, ecommerce и тег-менеджер выключены.

Acceptance: счётчик для `kidsmap.az`, без поддоменов; часовой пояс Баку UTC+04:00; валюта AZN; две JS-цели `phone_click`, `whatsapp_click`; не дублировать их автоматическими целями. Рабочая установка подтверждается отдельно от сохранения настроек кабинета.

## Snapshot and global constraints

- LOCAL HEAD: `e4e05cc213b34e2d771ecb854901bfd016d1db51`, ветка `task33-progress`, 20.10.2026.
- WORKTREE: существующие чужие изменения, в том числе `context_processors.py` и `base.html`. Не reset/clean/stash и не заменять их версиями HEAD.
- PRODUCTION revision/config: UNKNOWN в этой задаче. Доступ к приложению только read-only. Подготовка кода и активация на сервере — разные границы.
- До первой правки приложения требуется согласовать этот план и точные файлы по `AGENTS.md`.
- До принятия соглашения Яндекса требуется отдельное подтверждение пользователя непосредственно перед действием. Вход в аккаунт этого не заменяет.
- Первый запрос счётчика должен уходить после маскирования. Не передавать имя, email, телефон посетителя, введённый поисковый текст, user/session ID, полный referrer или произвольные event params.
- Тесты: `DJANGO_TESTING=1`, одноразовая локальная DB/cache/media/email, без production credentials и реальной отправки событий.
- Не менять GA4, схему БД, права доступа, опубликованные карточки, active_run, CI, nginx, production env. Не commit/push/deploy.

## Confirmed IDs and source

| ID | Подтверждённое основание | Результат |
|---|---|---|
| METRIKA-01 | Нет интеграции в просмотренных source paths; нет счётчика KidsMap в кабинете | Новый независимый счётчик, fail-closed при пустом/невалидном ID |
| METRIKA-02 | `base.html`: `send()` нормализует `cta_call` → `phone_click`, `cta_whatsapp` → `whatsapp_click` | Повторно использовать нормализованные имена, не создавать второй click-listener |
| METRIKA-03 | `legal_content.py`: политика AZ/RU/EN описывает Google Analytics, но не Метрику | Согласованно описать активируемую интеграцию и ограничения записи |

Основные source anchors: `src/catalog/context_processors.py:_google_analytics_context/site_settings`, `src/catalog/templates/base.html:send/emitAnalyticsEvent`, `src/catalog/services/tracking.py:PUBLIC_ANALYTICS_PAGE_TYPES`, `src/catalog/legal_content.py:get_legal_page_content`.

Graph: индекс ready, root `/home/ramin/kidsmap`; `base.html` разобран частично, использовано прямое чтение нужных диапазонов. Полнота графа не заявляется.

## Exact application scope

Modify:
1. `src/config/settings.py` — ID счётчика и флаг Вебвизора с выключенными defaults.
2. `src/catalog/context_processors.py` — отдельный gate и контекст в обеих ветках `site_settings`.
3. `src/catalog/templates/base.html` — условный include и вызов независимого моста Метрики из существующего `emitAnalyticsEvent`.
4. `src/catalog/legal_content.py` — техническое описание Метрики в privacy AZ/RU/EN, динамически по настройке, дата обновления privacy-документа.
5. `src/catalog/testcases/public.py` — проверки текстов privacy при включённой/выключенной Метрике.
6. `.env.example` — имена новых переменных с пустым ID и выключенным Вебвизором, без реальных env values.

Create:
7. `src/catalog/templates/includes/yandex_metrica.html` — конфигурация загрузчика через безопасные data-атрибуты.
8. `static/js/yandex_metrica.js` — privacy-маски, загрузка tag.js, единственный page hit и allowlist целей.
9. `src/catalog/testcases/test_yandex_metrica.py` — gate, render, privacy integration.
10. `static/js/tests/yandex_metrica.test.js` — регрессии отправки, блокировок и маскирования.

## Task 1: кабинет счётчика

- [x] В форме оставить `KidsMap.az`, домен `kidsmap.az`, «только с указанных адресов» включено, поддомены выключены.
- [x] Выбрать Баку UTC+04:00 и AZN, проверить сохранённые выбранные значения после потери фокуса. В текущей форме списки не раскрылись при проверке; введённое слово «Баку» само по себе НЕ подтверждает выбор.
- [x] Получить подтверждение перед принятием соглашения https://yandex.ru/legal/metrica_termsofuse.
- [x] Создать счётчик, записать публичный числовой ID и домен, сохранить screenshot. Повторно открыть настройки и проверить время/валюту/ограничения домена.
- [x] Создать две цели типа JavaScript-событие с точными идентификаторами `phone_click`, `whatsapp_click`. Не назначать им денежную стоимость и не считать их подтверждёнными звонками.
- [x] В Вебвизоре выключить «Записывать все поля», не создавать `ym-record-keys`. Дополнительные сервисы/реклама/ecommerce/user parameters не подключать.

## Task 2: server gate and render, RED → GREEN

- [x] В новом Django test module воспроизвести отсутствие метрики: пустой ID, нечисловой ID, DEBUG, TESTING, preview, admin host, localhost/testserver, private route, authenticated user.
- [x] Отдельный разрешённый request fixture: host `kidsmap.az`, URL name `place_detail`, `AnonymousUser`, DEBUG/TESTING/preview false, тестовый ID `12345678`. Проверить разрешение и ровно один include.
- [x] Реализовать `_yandex_metrica_context(request)` с фиксированным public allowlist `home/place_list/place_new/seo_landing/place_detail`. Это явный scope первой версии, не копия всей GA taxonomy.

```python
YANDEX_METRICA_COUNTER_ID = (os.getenv("YANDEX_METRICA_COUNTER_ID", "") or "").strip()
YANDEX_METRICA_WEBVISOR_ENABLED = _env_bool("YANDEX_METRICA_WEBVISOR_ENABLED", False)
```

Возвращаемый контракт:

```python
{
    "yandex_metrica_enabled": enabled,
    "yandex_metrica_counter_id": counter_id if enabled else "",
    "yandex_metrica_webvisor_enabled": enabled and webvisor_enabled,
}
```

Host сверяется с `PUBLIC_BASE_URL` и публичным `kidsmap.az`, не с суффиксом домена. ID допускает только положительное целое. Применить контекст в обеих ветках `site_settings`, существующие Google flags не менять.

- [x] В `base.html` подключить include только при enabled и отсутствии preview. Include содержит deferred static script с `data-counter-id`, `data-webvisor`; не содержит счётчик для private/test страниц и не имеет noscript fallback, который обойдёт JS privacy-gate.

## Task 3: клиент, privacy and goals, RED → GREEN

- [x] Сначала Node-проверки: один init/hit, allowlist двух целей, игнор неизвестных событий, совместимость при отсутствии ym/gtag, отсутствие утечки arbitrary params, защита от двойной загрузки.
- [x] После DOM ready пометить `form` и `#reviews` классом `ym-hide-content`; поля `input/textarea/select/[contenteditable]` — `ym-disable-keys`. Динамические формы маркировать до попадания в запись через существующий DOM lifecycle или компактный observer; маскирование не меняет содержимое/работу формы.
- [x] До загрузки `https://mc.yandex.ru/metrika/tag.js` подготовить очередь ym и маски. Не копировать сторонний inline snippet без host/gate.

```javascript
ym(counterId, 'init', {
  defer: true,
  clickmap: true,
  trackLinks: false,
  accurateTrackBounce: true,
  webvisor: webvisorEnabled
});
```

`trackLinks:false` выбран для ограничения автоматической передачи внешних URL; контактные цели считаются существующим мостом. Отправить один `hit` на очищенный URL: origin + pathname и только allowlist маркетинговых меток `utm_source/utm_medium/utm_campaign`; удалить `q`, fragment, `next`, tokens и другие произвольные query values. Для referrer оставить origin + pathname, исключив private/auth пути и query. Не передавать title, содержащий свободный поисковый текст. Проверить `hit` options по актуальной справке перед кодом и network acceptance.

- [x] Добавить независимый `window.kidsMapTrackYandexMetricaEvent(name)`; принимает только `phone_click/whatsapp_click` и вызывает `ym(counterId, 'reachGoal', name)` без visitor params.
- [x] В существующем `emitAnalyticsEvent` вызвать этот мост отдельно от GA. Не добавлять обработчик клика в `place_phone_reveal.js` и не повторять listener `[data-track-event]`.
- [x] Не добавлять Метрику в сервисную `dataLayer` и не включать автосбор ecommerce/пользовательских параметров.

## Task 4: privacy content and shared verification

- [x] Сначала тесты privacy AZ/RU/EN при включённом счётчике и без него.
- [x] В трёх языковых секциях указать Яндекс Метрику как отдельный сервис, публичные анонимные страницы, cookies/технические данные и записи действий при включённом Вебвизоре; явно описать скрытие форм и исключение личного кабинета. Не называть все идентификаторы гарантированно анонимными.
- [x] Не представлять обновление текста как правовое заключение о требованиях любых стран; сторонние пользовательские соглашения не менять.
- [x] Запустить новый Django module + существующие tracking и public privacy tests; Node new tests + `ai_referral_tracking.test.js`. Базовые команды в изолированной копии без унаследованных DB/Redis/Google credentials:

```bash
DJANGO_TESTING=1 DATABASE_URL= DJANGO_DEBUG=1 .venv/bin/python manage.py test src.catalog.testcases.test_yandex_metrica src.catalog.testcases.tracking src.catalog.testcases.public.TestPublicPagesSmoke.test_privacy_policy_is_full_document_in_all_languages
node --test static/js/tests/yandex_metrica.test.js
node static/js/tests/ai_referral_tracking.test.js
```

Для gate-тестов с DEBUG=False использовать RequestFactory и settings override; запуск isolated DB оставлять DEBUG=True, не обращаться к production DB. Cache LocMem, email LocMem, media — уникальная временная директория в test settings.

- [ ] Browser: с заблокированной внешней отправкой проверить AZ/RU/EN home/catalog/detail и private/preview/authenticated negatives. Маски должны существовать до первой попытки загрузки tag.js. Для privacy-текста проверить 390/768/1024/1280/1440; layout компонентов не перерабатывать.
- [x] Отдельно записать проверенные и не выполненные transport/browser/account checks. Не утверждать получение событий Метрикой по одним mock-тестам.

## Activation boundary and rollback

После code scope approval подготовить локальный diff и evidence. Production активация требует отдельного согласованного release scope с текущей версией сервера; этот план её не разрешает. В release env установить ID созданного счётчика; Вебвизор включать только после проверки маскирования полей в его настройках. Реальный page hit и запись визита проверять отдельно от установки кода. Цели проверять без искусственного открытия звонка/WhatsApp или отдельно согласованной тестовой сессией.

Rollback: выключить внешний счётчик через пустой `YANDEX_METRICA_COUNTER_ID`, Вебвизор через false; восстановить только собственный scoped diff в подготовленном checkout. Чужие изменения и существующую GA4 сохранять. Сам счётчик не удалять.

## State at handoff

20.10.2026: пользователь одобрил соглашение и локальный scope. Счётчик 113691893 создан, кабинет настроен, обе JS-цели сохранены, запись всех полей отключена. Согласованные 10 файлов реализованы в dirty WORKTREE с сохранением исходных чужих изменений. Defaults по-прежнему выключены; ID не записывался в рабочие env.

Проверки: RED до реализации; targeted Django и Node; реальные Django render fixtures в изолированной копии без унаследованных credentials. Browser: 9 публичных home/catalog/detail AZ/RU/EN с локальной заменой ym и блокировкой внешних запросов через CSP; один init/hit, одна контактная цель, динамические маски. Privacy: AZ/RU/EN × 390/768/1024/1280/1440, без горизонтального переполнения, без загрузчика Метрики. Authenticated/preview/private/host negatives проверены Django gate и rendered integration tests; полный браузерный login/preview runtime не запускался.

Фактические дополнительные ограничения: sendTitle:false; no-referrer для загрузки tag.js; Вебвизор отключается при немаркетинговых query-параметрах и fragment. Для метода hit используется options.referer по актуальной официальной справке.

Доказательства: /home/ramin/.codex/visualizations/2026/10/20/01a158f9-7892-7eb1-b19a-51dc8b944ec0/metrica-setup-result.html. Отдельный metrica-only-changes.patch содержит только эту задачу относительно исходного dirty состояния.

NOT RUN: production deploy/env/static collection, реальная доставка hit/reachGoal в Яндекс, реальные записи Вебвизора и аудит сетевого payload внешней библиотеки. Синтетические production контакты не отправлялись. Схема БД не менялась; SQLite не проверяет PostgreSQL constraints. Release требует отдельного согласованного scope с актуальной ревизией production.
