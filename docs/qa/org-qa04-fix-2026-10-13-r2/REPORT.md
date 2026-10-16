# ORG-QA-04 — LOCAL SCOPED ACCEPTED, включая RU fallback

2026-10-13 Asia/Baku. Root/kidsmap-orchestrator `.agents/agents/kidsmap-orchestrator/agent.md`, sequential execution. Изначальные AZ/EN планы одобрены «одобряю», отдельное [RU дополнение](../org-qa04-fix-2026-10-13-r1/PLAN-RU-FALLBACK.md) одобрено «да делай». [Authorization](authorization.json). Historical r1 OPEN/raw failures сохранены.

## 1. Состояние области

**ORG-QA-04 P3 LOCAL SCOPED ACCEPTED.** 15 согласованных AZ/EN translations уже внесены; новым diff добавлены только14 exact missing entries в `locale/ru/LC_MESSAGES/django.po`, msgstr=исходная русская подпись. «Одобрить заявку» RU уже был переведён. Без этого default LANGUAGE_CODE=az вызывал RU fallback к AZ. Backend/settings/templates/LANGUAGE_CODE не менялись; другие fuzzy/header/PO entries и shared MO не переписаны.

Checkout `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +approved dirty WORKTREE, active_run NONE. [entry](entry.json), [current source](entry-final.json), одновременно отдельно approved ORG-QA-05 CSS.

## 2. Сильные стороны / RED→GREEN

RED сохранён в [r1 copy proof](../org-qa04-fix-2026-10-13-r1/copy-proof.json) и browser: htmlLang=ru, но Adlar/Təşkilatlar/Sahiblik. GREEN [same-process proof](copy-proof.json): все15 согласованных strings и lazy section/model/badge следуют RU/AZ/EN/RU/EN; RU fallback regression отсутствует.

Fresh real browser [browser.result.json](browser.result.json): **72PASS,0FAIL,0pageerrors,0localnetwork errors**. Native language dropdown RU→AZ→EN→RU;54 add/draft/published-candidate renders RU/AZ/EN×6widths; native submit→visible pending→approve→visible published→reload; invalid URL/error/input preservation→correction→draft/reload;9shared admin heading checks. Здесь wait for actual visible published control затем строгий count=1; earlyCount1. Historical EN count FAIL не переписан.

72 rows не равны72PNG: [PNG manifest](png-manifest.json) содержит56 оригинальных screenshots (54 matrix+pending/error). Русские заголовки и длинные AZ/EN labels просмотрены в оригинальных screenshots; overall module288 states review отдельно.

## 3. Реальные проблемы

Две причины одного scope (missing AZ/EN entries и необходимый RU identity fallback) устранены. Не объявлялось исправление всех sidebar/global translations. Общие msgid reviewed в organization/program/ownership request consumers.

## 4. Tech debt

При переводе source msgid в default AZ catalogue нужны RU identity entries, если RU должен сохранять исходный текст. Глобальная locale унификация вне scope.

## 5. Risks / isolation

Свой runtime/URL/PID [server.json](server.json), DB orgqa04_20261013_r2; PG17.10 explicit loopback127.0.0.1:35715. DJANGO_TESTING=1, own caches/media/private-media/email/cookies/browser, .env/production credentials не использовались. Fresh helper build/verify [RU/AZ/EN manifest](locale-manifest.json), sole LOCALE_PATHS before setup. Source match [runtime-version-final.json](runtime-version-final.json). Старые локальные MO/stand profiles сохранены, новые unique outputs; old processes не перезапускались.

## 6. Dead/legacy

Не исследовались/не удалялись.

## 7. Tests gaps / NOT RUN

4 обязательных existing locale/admin tests вошли в один финальный248 unique-test module run, exit0, без assertion changes. Прогон не повторялся. Global corpus/external SMTP/fonts SDK/production/commit/push/deploy NOT RUN.

## 8. Handoff

ORG-QA-04 закрыт в LOCAL scope. Полная приёмка организаций [module02-full-r2/REPORT.md](../module02-full-2026-10-13-r2/REPORT.md), hashes/provenance/commands сохранены. Historical r1 regression superseded only by this fresh proof.

## 9. Приоритеты

P3 ORG-QA-04 LOCAL SCOPED ACCEPTED, новых подтверждённых P0/P1/P2 в этом translation scope нет. Общий production PASS не заявлен.
