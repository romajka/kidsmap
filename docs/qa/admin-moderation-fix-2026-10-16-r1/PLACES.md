# Места и заявки: AM-02 / AM-06 / AM-07 / AM-08

16.10.2026. Режим APPROVED IMPLEMENT по прямому запросу пользователя «все исправь окончательно и дай мне отчет». LOCAL HEAD: `e4e05cc213b34e2d771ecb854901bfd016d1db51`; работа выполнена в уже dirty WORKTREE. Чужие изменения сохранены. Production не изменялся, commit/push/deploy не выполнялись.

## Что исправлено

- **AM-02:** у неопубликованного места ссылка из раздела «Фото» открывает защищённый `/admin/catalog/place/<id>/site-preview/`. Наличие заявки не требуется. Используется полная карточка сайта; видимая гостевая шапка не уничтожает настоящую административную сессию. Публичный URL pending-карточки по-прежнему закрыт. Для опубликованной карточки остаётся рабочая публичная ссылка.
- **AM-06:** действующие RU-переводы «Открыть», «Низкая оценка» и «Риски» теперь совпадают со смыслом действий. Исправлены также неправильные AZ/EN-переводы оценки, превью и успешной публикации; снят fuzzy именно с проверенных строк.
- **AM-08:** после публикации из proxy-очереди переход идёт в конкретную карточку `admin:catalog_place_change`, которая продолжает существовать после выхода места из pending-выборки. Успешное сообщение появляется после успешной публикации.
- **AM-07:** один `request_is_stale()` используется просмотром заявки, списочными действиями, меню строки и формой подтверждения. Устаревшая заявка показывает причину и не предлагает одобрение ни в строке, ни в карточке, ни на странице подтверждения. Прямой POST по-прежнему отклоняется серверной бизнес-логикой; состояние заявки и публичность места не меняются. Возможность отклонения заявки сохранена.

Основные файлы: `src/catalog/domain_admin/place.py`, `src/catalog/domain_admin/owner.py`, `src/catalog/services/admin_place_preview.py`, `src/catalog/services/admin_site_preview.py`, `src/catalog/templates/admin/catalog/place/form/section_media.html`, `src/catalog/templates/admin/catalog/placeownershiprequest/change_form.html`, `templates/admin/catalog/place_ownership_request_moderate_confirm.html`, новый `src/catalog/testcases/test_admin_place_moderation_fix.py`.

## Проверки

Финальная команда из `/home/ramin/kidsmap`:

```bash
.venv/bin/python .tmp/admin-moderation-places-fix-r1/run.py catalog.testcases.test_admin_place_moderation_fix catalog.testcases.test_ownership_admin_preview catalog.testcases.test_ownership_site_preview catalog.testcases.test_task33_ownership > .tmp/admin-moderation-places-fix-r1/green-r3.log 2>&1
```

**Exit 0; 80 tests / 94.319s / OK.** Новые регрессии 10/10; inspection 20/20; site-preview 11/11; ownership и concurrency 39/39. Копия полного финального лога — [places-green.log](places-green.log).

Runner очищает окружение, устанавливает `DJANGO_TESTING=1`, использует отдельную тестовую PostgreSQL-БД `test_admin_moderation_places_fix` в принадлежащем аудиту локальном контейнере, locmem cache/email, отдельные media/private-media, изолированные MO-каталоги. Исходящий socket connect разрешён только к этой локальной БД. Никаких production credentials.

Новые регрессии проверяют 200 закрытого preview без заявки, READ ONLY SQL transaction, 403/302 для недопущенных посетителей, 405 для POST preview, no-store/noindex, AZ/RU/EN, безопасный возврат при подставном `next`, сохранение административной сессии, публикацию/публичное чтение после перехода из proxy, stale UI и фактическое отклонение stale POST. Существующие suites дополнительно проверяют отправленные snapshots, цены/расписания/группы/фото, отсутствие записи при просмотре и гонки ownership.

До реализации сохранены RED: `.tmp/admin-moderation-places-fix-r1/red.log` — 8 tests / 7 failures; `red-locales.log` — 1/1 failure; `red-sidebar.log` — 1/1 failure. На промежуточных запусках исправлены активация проверенных PO-строк без fuzzy и область проверки отсутствующей формы одобрения: глобальный запрет любого `type=submit` ошибочно захватывал формы языка/выхода в общей шапке. Финальная проверка ищет конкретную `km-inspection-confirm-actions`, а также выполняет запрещённый POST и проверяет сохранность данных. Проверка сути блокировки не ослаблена.

Дополнительная точная команда — exit 0:

```bash
git diff --check -- src/catalog/domain_admin/place.py src/catalog/domain_admin/owner.py src/catalog/services/admin_place_preview.py src/catalog/services/admin_site_preview.py templates/admin/catalog/place_ownership_request_moderate_confirm.html src/catalog/templates/admin/catalog/placeownershiprequest/change_form.html src/catalog/templates/admin/catalog/place/form/section_media.html src/catalog/testcases/test_admin_place_moderation_fix.py locale/ru/LC_MESSAGES/django.po locale/az/LC_MESSAGES/django.po locale/en/LC_MESSAGES/django.po
```
 Изолированная сборка MO трёх языков завершена: `.tmp/admin-moderation-places-fix-r1/locales-build-r3.log`; результат `catalogues: 3`.

Один warning окружения в финальном test log: каталог изолированных `staticfiles/` не собран. Это не ошибка тестов; наличие и визуальное отображение static-файлов этим backend-прогоном не подтверждаются.

## Переводы

Проверенные активные PO-записи, без fuzzy; полная машинная фиксация — [places-locales.json](places-locales.json).

| Исходная строка | RU | AZ | EN |
|---|---|---|---|
| Открыть | Открыть | Aç | Open |
| Низкая оценка | Низкая оценка | Aşağı qiymət | Low rating |
| Риски | Риски | Risklər | Risks |
| Предпросмотр | Предпросмотр | Ön baxış | Preview |
| Карточка опубликована — уже видна на сайте | Карточка опубликована — уже видна на сайте | Kart dərc olunub — artıq saytda görünür | Listing published — now visible on the site |

Пояснение stale-блока имеет активные RU/AZ/EN-переводы; они также записаны в JSON. Редакции других строк PO, существовавшие до этой работы или появившиеся в соседних задачах, не присваиваются этому исправлению.

## Границы и передача

Миграций и изменения схемы БД нет. Просмотр только GET с административной авторизацией и concrete Place permissions; не расширялись cookie domain или публичный доступ к pending. Для preview выставляются `X-Robots-Tag: noindex, nofollow, noarchive`, приватный ответ `no-store` и отключено отслеживание.

Codebase Memory доступен; проект/root проверены. Индекс поколения `2026-10-16T11:58:41Z` отстал от изменённых файлов: exact coverage показал `metadata_changed`, новый test `not_tracked`, PO частично разобраны. Новый helper отсутствовал в graph; отрицательный результат не использован как вывод. Решения проверены непосредственно по source и свежему runtime.

**NOT RUN этим исполнителем:** rendered-browser acceptance, вся библиотека тестов проекта, Google indexing, real-device/iOS, production post-deploy проверка. Backend HTML-response tests не выдаются за браузерную приёмку.

**Handoff → kidsmap-orchestrator / browser-qa:** принять локальные backend-результаты 80/80, выполнить браузерный сценарий закрытого preview места без заявки, stale карточки/подтверждения и публикации из proxy на общей финальной копии. Проверить AZ/RU/EN, рабочую сессию, отсутствие 404, предупреждение stale, статические ресурсы и responsive widths. SHA-256 затронутых source на момент проверки — [places-source-sha256.json](places-source-sha256.json). Выпуск на production — отдельная операция; локальный PASS не означает, что действующий сайт уже обновлён.
