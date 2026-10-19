# SITE-QA-22: выход из раздела настроек — Implementation Plan

> **For agentic workers:** выполнять inline по шагам RED → согласованный exact diff → GREEN. Этот пакет — PLAN, кандидат НЕ ПРИМЕНЁН. Использовать существующее одобрение после его получения; повторно разрешение на этот scope не запрашивать.

**Goal:** после успешного обычного сохранения шести разделов вернуться к «Настройкам сайта», сохранить поведение продолжения редактирования, ошибок и конфликтов вкладок, корректно показать уведомление на странице назначения.

**Architecture:** переопределить штатный Django `response_post_save_change(request, obj)` только в `_BaseSiteSettingsSectionAdmin`. Django сохраняет объект, журнал и success message своим обычным путём; меняется конечный адрес обычного Save. На hub добавить одно локальное CSS-правило переноса сообщений; его необходимость показана отдельным labelled transport/CSS prototype. Analytics, catalogue и gallery не наследуют этот base.

**Tech Stack:** существующие Python3.12/Django6.0.2/PostgreSQL/Jazzmin/CSS/Chromium. Без новых зависимостей.

**Spec:** [исходный finding](../site-qa08-fix-2026-10-18-pc-r1/findings/SITE-QA-22.md), [72 прежних native случая на том же source snapshot](../site-qa08-followup-fix-2026-10-18-pc-r1/evidence/SITE22-observed-navigation.json), [свежий backend RED](evidence/red-backend.json), [реальный installed Django contract](evidence/runtime-contract.json), [destination prototype](evidence/browser-destination-prototype-v2.json), [квалификация симуляции](evidence/prototype-qualification.json), [exact diff](proposed.diff), [SHA](candidate-manifest.json).

## Global Constraints

- Только три application files: `src/catalog/domain_admin/site.py`, `static/admin/css/pages/kidsmap_site_settings.css`, новый `src/catalog/testcases/test_site_qa22_save_exit.py`. Точное содержимое — в `candidate/`; не добавлять другие исправления.
- Действующая авторизация «давльше» разрешает подготовку следующего плана. Предыдущий approved scope относился к CSS SITE08. На данный новый diff нужно решение пользователя согласно AGENTS.md: «Future implementation requires a concrete plan and user approval for its scope».
- Source1033 неизменён в этом PLAN. HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE/индекс/refs сохранять. Production UNKNOWN, без контакта.
- Не менять `_SiteSettingsConcurrencyAdminMixin`, `changelist_view`, save/validation/ACL/revision logic, модели/схему/PO, галерею, catalogue/analytics destinations или общий shell. Existing SITE08 CSS SHA074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c сохранить.
- Сохранить `active_run: NONE`, shared MO, `.cbmignore`, все36предыдущих sealed packages/7436files и чужие runtimes. Текущий PLAN33600 и прежние33590/33580 — чужие для следующего run; не использовать их fixtures для нового GREEN и не перезапускать/очищать.
- DJANGO_TESTING=1, env очищен до setup, собственные fresh normal/test DB/cache/media/private-media/email/current3locale, внешние интеграции отключены. Никаких production credentials, commit/push/deploy/reset/clean/stash/index/branch mutations.

## Task 1: exact fix и доказательство конечного перехода

**Files:**
- Modify: `src/catalog/domain_admin/site.py`, `_BaseSiteSettingsSectionAdmin`, сразу после `changelist_view`.
- Modify: `static/admin/css/pages/kidsmap_site_settings.css`, только append scoped alert rule.
- Create/Test: `src/catalog/testcases/test_site_qa22_save_exit.py`, exact [готовый тест](candidate/src/catalog/testcases/test_site_qa22_save_exit.py).
- Evidence: новый `docs/qa/site-qa22-fix-2026-10-18-pc-r1/`; ignored scratch `.tmp/site22-pc-fix-r1/`.

**Interfaces:** existing `admin:catalog_sitesettings_changelist` — hub уже используется ссылкой «Назад»; `response_post_save_change(self, request, obj)` возвращает redirect после обычного успешного Save. Six runtime consumers: branding/about/contacts/footer/empty/visibility. `_continue` и popup завершаются в Django до этого hook; errors/stale409 до `response_change` вообще не доходят. Default POST без submit-button использует обычный Save; backend test с именем `default_enter` проверяет именно отсутствие submit-button, а не реальное поведение клавиши Enter в браузере.

- [ ] **Step 1: fresh guard и собственный стенд.** Сверить source1033/HEAD/branch/task33/index с этим source-final.json; проверить36prior manifests и этот новый manifest. Проверить отсутствие новых runtime/DB имён перед созданием. Использовать `m10s22-fix-r1-app`, `m10s22_fix_r1`, `test_m10s22_fix_r1`, loopback33610; при занятом имени выбрать новый уникальный owned namespace и записать его. Скопировать из этого пакета runtime/config/fixture scripts, заменить только QA namespace и заново собрать current3root locales через scripts/build_isolated_locales.py. Repo mount RO, только свой scratch RW. Нормальный и тестовый storage/cache отделены. Сверить installed Django contract с evidence/runtime-contract.json, если runtime изменился.

- [ ] **Step 2: повторить RED из exact candidate tests.** Скопировать candidate test в собственный QA import path и выполнить тот же runner против НЕИЗМЕНЁННОГО приложения:

```text
docker exec m10s22-fix-r1-app python /mnt/c/kidsmap/.tmp/site22-pc-fix-r1/runtime.py test test_site22_candidate
```

Текущий свежий результат —9методов:3failed/6PASS,20expectedfailure observations,0errors,5.836s,exit1.18language×section cases сохраняют значение/1LogEntry, но приходят в редактор вместо hub; ещё2fail — proxy-only editor и normal no-button POST. Controls: continue/invalid200/stale409/denied403/analytics/catalogue PASS. Сохранить actual output; при других причинах сначала диагностировать, не ослаблять destination assertions. Подробный executable test полностью дан в candidate file; не заменять его source-string или mock assertions.

- [ ] **Step 3: применить exact three-file diff после одобрения.** Перед записью проверить base SHA из candidate-manifest и отсутствие нового test path:

```text
git -C /mnt/c/kidsmap apply --check /mnt/c/kidsmap/docs/qa/site-qa22-recheck-2026-10-18-pc-r1/proposed.diff
```

Скопировать exact candidate bytes только в три перечисленных path. Сохранить CRLF двух existing files и исходные unrelated whitespace. Hook:

```python
    def response_post_save_change(self, request, obj):
        """Exit a saved subsection to the existing settings hub."""
        return redirect(reverse("admin:catalog_sitesettings_changelist"))
```

Hub CSS append:

```css
/* Saved subsection messages are shown on the settings hub. */
body:has(.km-site-settings-page) #content > .alert {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}
```

Не использовать overflow:hidden или смену текста уведомления/переводов. Source станет1034:2existing changed+1new test,1031existing unchanged. Сверить все candidate SHA, остальные source SHA, diff exactness. Новый тест должен оставаться логически/побайтно тем же кодом, который исполнялся в RED. У owned source-loaded server проверить containerID и `/proc/PID/cmdline`, остановить только его, обновить expected-source guard и запустить заново; старые серверы не трогать.

- [ ] **Step 4: actual-source backend GREEN.** Запустить9методов из нового `catalog.testcases.test_site_qa22_save_exit` и существующие105методов следующим списком в новом isolated testDB; при taxonomy/keepdb environment проблеме сохранить ошибку и создать fresh owned testDB, не переписывать assertions:

```text
runtime.py test catalog.testcases.test_site_qa22_save_exit catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches
```

Ожидаются114unique methods,0failures/0errors; фактические count/time/exit записать. Текущие105/33.566sOK — исторический baseline SITE08, не GREEN этого кандидата. Проверки must catch: неверный hub адрес; hook на общем mixin с ошибочным redirect analytics; обход continue; потеря сообщения или лишняя запись; конфликт409 и validation200 без ухода; proxy-only editor без permission на SiteSettings достигает существующего hub без расширения ACL.

- [ ] **Step 5: unmodified native browser acceptance.** Новый Chromium profile/current locales. Никакого route.fetch/Location rewrite, transport mock или addStyleTag для actual-source GREEN. Две destination ветки: `_save` POST302→hubGET200, ровно1redirect/1LogEntry/точное значение; `_continue` POST302→тот же changeGET200. Error200/stale409 остаются в editor, записи/файлы/log не меняются. Шесть секций ×AZ/RU/EN ×360/390/768/1024/1280/1440 ×оба действия =216valid save states. Branding/footer дополнительно: длинное unbroken имя бренда105chars и валидный длинный email,3langs ×360/1440 ×оба действия =24states. Конкретные значения — существующий prototype (`Q`+`UnbrokenBrand`×8; email mailpart×6 + @ + domainpart×5 + .invalid (localpart54chars)), поля для шести секций — SECTIONS в new test.

Для каждого save: native submit/reload/revision обновляется штатно, exact value/1log, ожидаемый target/template/lang, success text/link/close видимы, message внутри viewport и выше формы/карточек, document≤viewport, keyboard Tab/Enter close. На hub без сообщения и с сообщением исключить новый overflow; screenshot baseline/prototype из PLAN не подменяет sourceGREEN. Проверить fresh CSS_HTTP200/exact SHA обеих stylesheets. Повторить mobile invalid email/file/JSON и focus field-linked summary; stale409 draft/old token/file reselection на уже защищённых формах; proxy-only editor/viewer/denied/CSRF. Analytics/catalogue/gallery должны сохранять собственные destinations; Place/Event marker/assets/geometry и readonly mobile controls сохраняются. SITE20/SITE11 и другие findings не расширять этим diff.

Публичные brand/footer scalar values после соответствующих native saves читать реальным SSR GET; logo/gallery files в этом scope не менять. Тексты и flags других секций после проверки восстановить native saves; изменения checkbox затрагивают только own fixture. Учитывать все ожидаемые LogEntry/времена; сравнить JSON/media hashes/gallery rows. Public district options DB-derived, JSON→public dependency этим не доказывать.

- [ ] **Step 6: audit outcome и seal.** Сверить app exact SHA/source1034/1031unchanged/ref/index/empty staging/sharedMO/.cbmignore/activeNONE/все prior manifests/foreign runtime identities. Сохранить native commands/exits/matrix/PNG/fixture restores/failures без переписывания старых прогонов. Append-only guide/MASTER. Закрыть SITE22 LOCAL только после actual-source GREEN и native transitions. До этого module10 остаётся14OPEN(9P2/5P3); после отдельного scoped closure ожидается13OPEN(9P2/4P3), full acceptance всё ещё pending. Сохранить SITE01/15/06/19/21/08/module09 closures. Без автоматического следующего fix, commit/push/deploy/production.

## Self-review

Root cause проверен в actual source и installed Django: normal Save делегирует response_post_save_change, default destination — subsection changelist с немедленным возвратом в editor. Six consumers подтверждены registry runtime, graph используется только как навигация (stale/coverage_unavailable). Destination template реально грузит только hub CSS, поэтому одного SITE08 form stylesheet недостаточно. Labelled prototype показывает long mobile message1020/1028/1039→360→exactrollback,12cases/162controls; native direct candidate redirects ещё НЕ ПРОВЕРЕНЫ. CSS необходим для корректного результата нового перехода; копирайт, permissions, модели и прочие consumers остаются отдельными scope.

Initial backend helper ошибочно использовал SiteSettings pk для отдельной CatalogContentSettings table: v1 evidence сохранён, исправлен только fixture ID, destination assertions сохранены. Prototypev1 не перехватил redirect GET,12`actual_hub_render`FAIL сохранены. Prototypev2 форвардит footer POST через route.fetch;13rewrite включая восстановление footer/26success writes, не unmodified native acceptance. Initial candidate two-file diff и helper diagnostics сохранены; финальный concrete scope — этот three-file diff. Existing whitespace в site.py сохранён, checks относятся к добавленным строкам.

**Approval scope:** exact [proposed.diff](proposed.diff), SHA `e60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97`,3files. Исполнение inline после решения пользователя.
