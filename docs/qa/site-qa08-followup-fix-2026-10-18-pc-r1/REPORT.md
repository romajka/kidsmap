# SITE-QA-08 — CSS followup применён и проверен, 2026-10-18

**SITE08 CLOSED LOCAL.** Согласованное дополнение в одном CSS применено без расширения scope. Уведомление после сохранения больше не расширяет мобильную страницу: native actual-source RU360 **366→360px**, тот же тест11checks:10PASS/1expectedFAIL до →11PASS после. Production UNKNOWN/не контактировали. Module10: **14OPEN (9P2/5P3)**, полная приёмка модуля остаётся pending.

User «дальше» прямо продолжает вопрос о применении конкретного followup: [authorization](authorization.json). [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) и candidate-manifest — точные исторические копии на момент одобрения, содержащие прежний NOTAPPLIED; текущее применение подтверждают [applied](applied.json), [verification](verification.json), [implemented.diff](implemented.diff). Execution /root inline, canonical frontend-admin/orchestrator scope; independent specialist review NOT RUN.

## Изменение

Только static/admin/css/pages/kidsmap_settings_forms.css: scoped `body:has(.km-settings-form-page) #content > .alert` получает normal block flow, min-width0/max-width100% и overflow-wrap:anywhere. Переносится текст со ссылкой на объект; overflow не скрывается. SHA baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83 →074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c. Exact diff SHA da5563bc9a2e2d75f6cdf8ffa2b7c1992c440ff2ccbc0d5a2eb8678cd77dde99. Остальные1032source files сохранены; template e3791aa31eba0d31ecd14ce559cfca8745185b9ba3950dcc4aa92d224e5cbe29. До/после проверялись сохранённые source bytes, без DOM/style injection.

## Свежая проверка

| Native suite | Cases | PASS |
| --- | ---: | ---: |
| Identical saved-message RU360 RED→GREEN | 5 | 11 |
| 9forms ×3languages ×6widths | 162 | 1134 |
| Readonly catalogue/mobile hidden Save | 18 | 126 |
| Place/Event no marker/CSS +exact geometry parity | 12 | 60 |
| Invalid JSON/draft/focus/viewport | 18 | 126 |
| Invalid file/visible linked summary/native anchor focus/no-write | 12 | 72 |
| ViewerPOST403/deniedGET403/no writes | 2 | 7 |
| Saved messages/short+unbroken long/both buttons +restores | 150 | 1890 |

**3426/3426checks PASS,379rows** в новом actual-source acceptance. Отдельные RED/baseline59checks:58PASS/1ожидаемый geometryFAIL; не включены в GREEN total.144native saved states: AZ/RU/EN,360/390/768/1024/1280/1440, branding/footer, short/long, `_continue`/`_save`. Exact scalar persistence и1LogEntry на операцию, видимые message/link/close, viewport bounds, отсутствие перекрытия формы, keyboard Tab/Enter dismissal и public SSR readback. Лого и галерея в этом followup не изменялись; их paths/bytes/rows сохранены.224PNG, [матрица](matrix.csv), [визуальный обзор](visual-review.json), команды/exit и scripts сохранены. В наборах с мониторингом pageerror/неожиданных localHTTP нет; permission probe проверяет expected403/no-write без pageerror listener. Внешние ресурсы блокировались, font ERR_FAILED диагностирован; console-clean не заявляется.

18permission/model branches actual template compiled;9consumers, current3root locales, CSS_HTTP200 с exactcandidateSHA и1033source guard. Backend105tests/33.566s/OK из родительского пакета — **исторический baseline, не новый запуск**. Python source unchanged; новый CSS не требовал повторения backend suite. Проверены native POST/validation/render states. Все проверки на отдельном стенде33590, DJANGO_TESTING=1, env очищен перед setup, отдельные normal/test DB/cache/media/private-media/email/locales, integrations disabled.158ожидаемых synthetic LogEntries; исходные scalar значения восстановлены native save, JSON иmedia filenames/bytes/gallery exactunchanged. No positive API business POST.

## Отдельные незакрытые пункты

**SITE22/P3 остаётся OPEN:**72native `_save` цепочки POST302→changelist302→same editor200 записаны отдельно; correct persistence не означает correct exit. CSS не меняет этот backend. SITE20/SITE11 и прочие canonical findings также OPEN. Public district filters DB-derived; controlled JSON→public dependency UNVERIFIED, не предмет этого исправления. Полный accessibility/global/module10 acceptance/модуль11 не заявляются.

## Сохранность

HEAD 852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1, dirty WORKTREE сохранён.35prior packages/7127files, sharedMO/.cbmignore/refs/index bytes/empty staging/active_runNONE и71foreign runtime IDs/states проверены. Перезапущен только собственный новый source-loaded server после проверки containerID иcmdline. CRLF сохранён; nativeGitdiff--check иreverseexactpatchcheck exit0. Guide/MASTER append-only; SITE01/15/06/19/21 иmodule09 LOCAL closures retained. Без commit/push/deploy/production/cleanup чужих стендов. [Полная проверка](verification.json), [preservation](evidence/preservation.json).
