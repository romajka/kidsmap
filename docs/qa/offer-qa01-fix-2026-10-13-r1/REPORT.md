# OFFER-QA-01 — удаление группы после одобрения

2026-10-13. Root, последовательное выполнение, lead kidsmap-orchestrator. **OFFER-QA-01 CLOSED LOCAL в проверенном scope. Модуль05 IN PROGRESS.** Независимые исполнители не заявляются. Отдельный OFFER-QA-09 остаётся OPEN; частичная модерация не объявлена исправной.

## 1. Срез и разрешение

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE с предыдущими работами сохранён; active_run NONE. Пользователь одобрил [конкретный план](../../superpowers/plans/2026-10-13-offer-qa01-approved-group-removal.md) ответом «да». Только OFFER-QA-01, два существующих серверных файла и один новый тестовый файл. [Entry](entry.json), [final verification](verification.json), [runtime](runtime-version-final.json), [diff](application.diff), [hashes](source-change-manifest.json).

Собственный профиль `offer-qa01-fix-2026-10-13-r1`: свежие DB/container/volume/порты, loopback PostgreSQL, отдельные cache/media/private-media/email/cookies. Точные актуальные значения — server.json/verification.json, не portable параметры другого ПК. `.env` не загружается; inherited env удаляется, DJANGO_TESTING=1 до setup, socket egress только к собственному PG. Браузер блокирует внешние fonts/CDN/maps. Секреты только в ignored `.tmp`0600. Общие MO не заменены. Собственные RU/AZ/EN собраны из текущих PO, manifest проверяется до setup, единственный LOCALE_PATHS. [Manifest](locale-manifest.json), [commands](COMMANDS.md).

## 2. Причина и результат

Редактор корректно убирал группу из полного nested payload, но серверный writer обновлял только присланные строки. Оmitted группы оставались активными; после одобрения их тариф80 продолжал показываться посетителям.

`replace_nested_pricing(..., complete_tree=False)` теперь имеет явный безопасный partial default. Только `_apply` approved nested snapshot вызывает `complete_tree=True`. В этом режиме writer после валидации полного payload архивирует пропущенные группы/занятия через canonical archive(), сохраняет их строки и тарифы, повышает версии, обновляет итоговую проекцию цены. Existing target locking/atomic review/ACL/CAS сохраняются. До одобрения live не меняется, при отказе/ошибке rollback сохраняет исходные данные. Отдельное удаление тарифа следует прежнему контракту; direct Place tariffs не очищаются из-за пустого nested tree.

Приложение: `services/pricing_plans.py`, один call site в `services/publication.py`, новый `testcases/test_offer_qa01_group_removal.py`. Никаких schema/CI/dependency/UI/PO patches.

## 3. Backend evidence

[Native RED](../offer-qa01-recheck-2026-10-13-r1/approved-repair-regression-red.txt):1 executed/1 behavioral failure, native1, omitted group not archived. [Targeted GREEN](targeted-green.txt):38 executed/38 PASS, native0; новые10 regression cases плюс affected GroupPricing/CompletionTaxonomy/ProgramWorkspace. [Discovery](test-discovery.json):38 unique method IDs. После изменения только импорта fixture helper отдельно повторены [новые10](new-tests-final.txt), native0, без повторения28 старых. Django runner уже deduplicates initial labels; первый набор38 был уникальным, не48 accepted tests.

Новые проверки: ожидание одобрения, сохранение истории/ID/проекции, omitted activity/empty tree, direct tariff сохранность, rejection, partial default, complete mode, foreign IDs до mutation, реальный archive→injected failure→transaction rollback, прежнее удаление отдельного тарифа, повторное одобрение/stale source/candidate rejection. Existing assertions не менялись.

## 4. Native browser и READ ONLY

RU/AZ/EN×360/390/768/1024/1280/1440,18 fictional Place/Activity pairs: реальный keyboard Enter удаления группы, отправка формы, public reload до одобрения, candidate reopening, native reviewer approve, public и owner reload.199 PASS evidence rows, не199 независимых tests. До approval видны2 группы; после — одна KEEP и цена20.18 READ ONLY DB rows: removed archived/version2, history tariff retained, kept IDs stable, public removed tariff отсутствует, scalar min/max20.

Дополнительно: native stale session сохранение отвергнуто422 существующей validation архивированного ID, введённое имя сохранено, removed group не воскрешена (5 PASS rows). Это не заявляется как typed409 UI CAS; service CAS отдельно проверен backend. Native admin полный nested JSON import→save→approve удаляет группу; частичный name import оставляет hidden tree и public remaining group, но последующая approval блокируется отдельным baseline OFFER-QA-09. После native return live unchanged. Admin current tree readback с настоящим language switch RU/AZ/EN×6widths.30 accepted admin evidence rows; один row, подтверждающий baseline defect, отделён в baseline_rows и не считается здоровым workflow. Public Place detail по native ссылке из Activity проверен18 cells: headline20, archived tariff80 отсутствует (19 rows включая pageerrors check).

Итого253 scoped accepted assertion rows; отдельно OPEN baseline evidence. [Main native result](browser.result.attempt1791889890.json), [stale](stale-browser.result.json), [admin effective](admin-browser-effective.json), [Place detail](place-detail.result.json), [READ ONLY](readback.json), [extra readback](extra-readback.json), [PNG manifest](png-manifest.json).118 native PNG originals, derived [overview](public-overview.jpg). Native originals текущего собственного run обновлялись при повторных попытках той же cell; raw attempt results сохранены. Исторические evidence runs не перезаписаны. Визуально просмотрены native AZ1024 и overview18 public screens; автоматическая geometry/DOM проверка ограничена указанными сценариями. App pageerrors0 в accepted scripts; внешний транспорт явно blocked, негативный stale422 ожидаем.

## 5. Сохранность

Final verifier сверяет все прежние nonignored hashes, отдельно ignored common MO, HEAD/branch/active_run; разрешает только указанные source3, guides2, approved plan, собственные QA artifacts и добавленную RED запись собственного audit command log. Не трогает чужие процессы/container/DB. Собственный server перезапущен один раз после изменения импорта тестового helper; actual source receipt совпадает с current disk/startup. Последний verification проверяет собственный process argv, PostgreSQL loopback mapping и артефакты на actual own secret values. Это не универсальная гарантия отсутствия любых секретов.

## 6. Baseline/tool/fixture failures

Raw attempts сохранены. Сценарий сначала считал группу также в preview; native key/click probe подтвердил правильное удаление, locator сужен к редактору. Fixture mistakenly used invalid price_mode=paid;422, corrected только18 own prerequisite records to canonical tariffs before acceptance. Stale scenario ждал409/conflict UI, фактически422 relation validation; assertions приведены к фактическому безопасному отказу, input/live readback проверены, исходные reports retained. JSON export является download: protocol body ошибка устранена чтением native Download stream. Import требует настоящего подтверждения «Продолжить импорт»; оно выполнено. Timeout при approval partial name выявил настоящее baseline finding09; raw failure не удалён и не объявлен PASS.

## 7. Новая открытая проблема

[OFFER-QA-09](FINDINGS.md): trusted review_form для partial name revision не подставляет existing grouped pricing; readiness ошибочно требует цену. Native UI подтверждает отсутствие approve; exact pre-patch pricing/publication source probe reproduces defect in isolated test DB, corrected diagnostic native0/1 case. Scope09 не одобрен, application fix не выполнялся. Это не regression двух patched services и не дубликат01. Пределы dedup отмечены в FINDINGS.

## 8. NOT RUN и пределы

Полная ACCEPT-05, весь проектный корпус/no-label wrapper, остальные OFFER-QA-02–08, исправление/приёмка09, реальные внешние интеграции, physical devices/Firefox/WebKit/screenreader, production/commit/push/deploy NOT RUN. Проверки относятся к dirty LOCAL срезу, не HEAD-only или production. Полная приёмка module05 один раз после его задач; общий проектный прогон после всех модулей, по договорённости.

## 9. Handoff / приоритет

OFFER-QA-01 CLOSED LOCAL,P2 repaired. OFFER-QA-02–08 —7 исторических OPEN для свежего recheck. OFFER-QA-09 OPEN,P2 baseline blocked partial moderation. Нет заявлений P0/P1/общего module PASS. Следующий по порядку [PLAN OFFER-QA-02](next-prompt.txt). Реализация следующих findings автоматически не начинается; требуется конкретный план/scope approval. [Статусы](../module-acceptance-prompts.md).
