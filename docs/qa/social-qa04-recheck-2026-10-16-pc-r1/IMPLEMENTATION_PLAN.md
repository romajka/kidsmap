# SOCIAL-QA-04 Implementation Plan

> Для исполнителя: выполнять checkbox tasks последовательно после одобрения конкретного scope ниже. Канонический lead frontend-reviewer; browser-qa и Django/security проверки последовательно. Этот план и candidate diff ещё не разрешают application patch.

**Goal:** вернуть странице уведомлений существующее оформление кабинета и читабельные responsive строки/действия без изменения прав, данных и workflow.

**Architecture:** общий `account_profile.css` подключается только на inbox через `extra_head`. Небольшой новый page stylesheet оформляет строки/кнопки/empty/error/read-unread внутри `.account-notifications`; shared navigation template и global/account/org CSS не меняются. Все POST/CSRF/currentness/ACL остаются серверными.

**Tech Stack:** SSR Django6.0.2, Python3.12.15, PostgreSQL17.11, vanilla CSS, native Chromium155. Новых зависимостей нет.

**Spec:** [guide PLAN04](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-04), [finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-04.md), [repair prompt](../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-04.txt), [свежий REPORT](REPORT.md). Датированный прежний FAIL — checklist; текущее доказательство находится в этом run.

## Global constraints

- Только SOCIAL-QA-04, P2, scope approval PENDING. Сохранить уже одобренные SOCIAL01–03 и прочие местные изменения. Module09 OPEN;05–09/full ACCEPT09/global отдельно.
- Checkout `C:\kidsmap`, branch `codex/module09-transfer-2026-10-16-r1`, HEAD `852938d96764ae315b92859e3651e5ea62054a36` + dirty SOCIAL03; index tree `881e0c48c7d557c46221beb3b2410a157982f861`; `active_run: NONE` не назначать автоматически.
- Без commit/push/deploy/production/reset/clean/stash, переключения грязного checkout, чужих restart/cleanup. Существующие assertions не менять ради PASS.
- Application scope ровно2файла ниже. Controllers/services/models/routes/schema/PO/global JS/CSS/shared account/navigation/org styles и другие findings не входят.
- Собственный DJANGO_TESTING=1 PostgreSQL/DB/cache/media/private-media/email; fictional fixtures; очищенный env, без `.env`/production credentials. Browser localhost allowlist и internal Docker network; реальный внешний delivery NOT RUN.
- Fresh RU/AZ/EN через штатный isolated locale builder; verify/sole LOCALE_PATHS до django.setup; sharedMO не менять. Existing profile использовать только после ownership/isolation/current-source проверки. Порты/PID/сессии не наследовать как действующие без проверки.
- Targeted RED до patch, GREEN после; не повторять неизменившиеся успешные полные наборы. Full ACCEPT09 один раз после всех SOCIAL tasks, global corpus отдельно в конце.

## Точные файлы и минимальный diff

| Операция | Файл | Ответственность |
|---|---|---|
| Modify | `src/catalog/templates/pages/account_notifications.html` | static/extra_head2links, page scope и классы строк/действий/empty/error, текстовый unread badge AZ/RU/EN |
| Create | `static/css/pages/account_notifications.css` | Только inbox presentation: row/list reset, responsive actions, focus-visible, контрастные кнопки, unread/empty/error |

Полное точное содержимое: [template candidate](candidate/account_notifications.html), [CSS candidate](candidate/account_notifications.css), [proposed.diff](proposed.diff), [candidate hashes](candidate-manifest.json). Кандидаты лежат только в QA package; исходники приложения ещё не изменены. Отдельного нового application Python test нет: CSS/import assertions дублировали бы реализацию; meaningful regression выполняет настоящий browser по результату DOM/layout/action/readback и4существующих affected backend methods.

Подключение существующего account stylesheet восстанавливает layout/sidebar/active nav и базовый button language. Вместо подключения всего `organization_workspace.css` новый scoped CSS оформляет лишь реально используемые inbox `.org-list/.org-row`; это исключает ненужные org rules на странице. Их shared definitions не меняются. Existing local bundled Material Symbols остаются через base icons.css; внешние font links не добавляются.

## Task1 — snapshot, authorization и сохранение RED

- [ ] Получить одобрение двухфайлового scope. Сверить [source-entry.json](source-entry.json), HEAD/branch/index/dirty/active_run, source1020 и текущий inbox template SHA. Не трогать dirty SOCIAL03, `.cbmignore` и старые QA packages.
- [ ] Проверить ownership/isolation runtime `m09s04-plan-r1-app`/`m09s04-plan-r1-pg`, internal network и собственные media/cache/email. Если runtime исчез/перезапущен/source изменён — создать новый уникальный profile с актуальными source/PO; не запускать старые prepare scripts вслепую.
- [ ] При неизменном source использовать уже записанный targeted browser RED и4backend baseline; не повторять весь старый корпус. При drift воспроизвести только затронутый trigger до patch. Browser RED отличается от backend PASS: серверные workflow checks не проверяют оформление.
- [ ] Сохранить entry/current manifest и конкретный будущий approved patch SHA отдельно. Выполнить apply-check:

```powershell
git apply --check --ignore-space-change docs/qa/social-qa04-recheck-2026-10-16-pc-r1/proposed.diff
```

## Task2 — применить page-only presentation

- [ ] Применить ровно два файла [diff](proposed.diff); CSS path до добавления отсутствует. Существующий template сохраняет event-kind labels, `can_accept/can_reject/join_action_url`, read_at guard, URL actions, form methods и csrf_token.

```powershell
git apply --ignore-space-change docs/qa/social-qa04-recheck-2026-10-16-pc-r1/proposed.diff
```

- [ ] `extra_head` загружает `{% static 'css/pages/account_profile.css' %}?v=2` и `{% static 'css/pages/account_notifications.css' %}?v=1`; wrapper получает `.account-notifications`.
- [ ] Новые классы соответствуют полному candidate. В unread строках добавляется visible text badge: AZ `Oxunmayıb`, RU `Не прочитано`, EN `Unread`. На серверную eligibility/action logic это не влияет; read строки отличаются отсутствием badge/mark-read, а не только цветом.
- [ ] Scoped CSS сбрасывает маркеры/отступы UL, задаёт row layout с переносом и `min-width:0`, спокойный фон/border и44px actions. Mobile≤600 actions/form могут переноситься; длинные переводы остаются читаемыми без overflow clipping. Font-size не уменьшается ради вмещения.
- [ ] Кнопки используют brand tokens `--brand-turf/--brand-spruce`, вторичные — `--surface`; scope overrides общего `account-btn-action` сохраняют контраст. Focus-visible outline3px/offset3px, native buttons/links и POST form semantics сохранены. Пустое состояние/role=alert имеют тот же page layout.

## Task3 — targeted GREEN и native acceptance

- [ ] Новый approved-source manifest после patch; running template/static origins и hashes соответствуют WORKTREE. Проверить sole свежие MO и отсутствие local static404. Никакой подмены результата только HTTP200 или source grep.
- [ ] Один affected backend GREEN с неизменёнными4методами:

```text
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_join_confirmation_form_is_current_owner_post_only
catalog.testcases.test_access_qa02_invitation_decline.InvitationDeclineTests.test_inbox_exposes_decline_for_both_current_invitation_kinds_in_all_locales
```

Текущий профиль запускает `runtime.py test` с этими labels через docker exec; точная команда в [commands.md](commands.md). Ранее успешный baseline не является post-patch GREEN.

- [ ] Native six states (`empty/unread/read/invitation/revoked/expired`) × RU/AZ/EN ×360/390/768/1024/1280/1440. Шаблон [matrix-cell.js](matrix-cell.js) уже фиксирует loaded CSS/computed layout/nav/row/buttons и отдельно source failures. Future GREEN расширяет outcome checks для новых scoped классов, contrast/focus и44px actions; пустые множества controls отмечать N/A, а не PASS. Сохранять raw RED history.
- [ ] Во всех cells: real canonical URL/locale, existing shared active nav, CSS loaded200, layout flex и mobile column≤860, навигация доступна горизонтальным scroll/keyboard, text/content/actions без page overflow, empty/read/unread/current invitation и недоступные revoked/expired действия согласованы с backend.
- [ ] На390/1440 каждого языка: Tab/Shift+Tab до каждого action, видимый focus и scroll reachability под header; action names/CSRF формы; контраст обычного текста≥4.5, UI focus≥3. Новых анимаций нет, hover не единственный способ действия. Реальный screenreader/physical/cross-browser отдельно NOT RUN без фактического запуска.
- [ ] На отдельных новых fictional data actual native `Mark read`→redirect→reload/read_at, `Accept`→membership/readback, `Decline`→REJECTED/no new grant/readback, pending join confirmation→confirmation/readback. По одной независимой fixture на язык/действие; остальные successful cells не повторять. Получатель/чужой/гость, CSRF/POST-only и stale/revoked guard — по actual HTTP плюс явно выделенные browser flows.
- [ ] Error400/409 возвращаются тем же inbox renderer: native malformed decline/revoked-after-open сценарии на независимых owned invitations; GET reload и безопасное сохранение текущего state. Loading finite delay/transport abort только как SIMULATED, без автоматических повторных POST.
- [ ] Три representative account роли дополнительно: обычный recipient, owner и staff; display changes не выдавать за permissions change. Соседние Favorites, account profile и organization workspace — небольшой affected smoke390/1440 AZ/RU/EN на собственных fixtures. Новые CSS должны загружаться только на inbox; shared styles не менять ради green.
- [ ] Console/pageerrors/network/static/font facts и native PNG SHA/dimensions. Scope04 не объявляет полный WCAG/global UI PASS. Новый существенный общий дефект, требующий третьего application файла, сначала отдельный plan/approval; обычные итерации внутри этих двух файлов входят в согласованный scope.

## Task4 — evidence, guide и остановка

- [ ] Новый уникальный fix-run REPORT/verification, RED→GREEN, source/commands/exits/counts, PNG manifest, failed attempts и NOT RUN/SIMULATED. Проверить index/refs/active_run/sharedMO, текущие source и foreign containers/artifacts. Не утверждать whole-machine continuity по одной docker проверке.
- [ ] Закрыть только фактически принятую SOCIAL04; добавить новый статус guide с сохранением всей истории. SOCIAL01–03 остаются их scoped LOCAL решениями, module09 OPEN до ACCEPT09. SOCIAL05 не реализовывать автоматически.

## Self-review

Plan покрывает missing local stylesheet cause, responsive rows/actions, read/unread/empty/error, current and unavailable invitation display, keyboard/focus/contrast и сохранение backend guard contracts. Shared account/org/navigation source остаётся прежним. Full candidates даны без placeholders, app diff apply-check доступен; post-patch GREEN и UI acceptance пока NOT RUN. Production applicability UNKNOWN. Для исполнения требуется одобрение этого конкретного двухфайлового scope, прежнее одобрение SOCIAL03 его не включает.
