from pathlib import Path
import json
H=Path(__file__).resolve().parent;v=json.loads((H/'verification.json').read_text());b=v['browser'];p=v['preservation'];phases='\n'.join(f'| {name} | {count} |'for name,count in b['phase_counts'].items())
text=f'''# SOCIAL-QA-01 — CLOSED LOCAL

2026-10-16, Asia/Baku. Реализован одобренный [план](../social-qa01-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md). Исполнитель `/root`, kidsmap-orchestrator; frontend-reviewer, django-reviewer и browser-qa выполнены последовательно одним исполнителем по действующим definitions. Независимая делегация не заявляется.

**Сохранённая оценка снова выбрана в редакторе после reload.** Проверены Place, Specialist, Activity и Event. Закрыт только SOCIAL-QA-01; модуль09 целиком ещё не принят.

## 1. Срез и границы

`/home/ramin/kidsmap`, branch `task33-progress`, HEAD `{v['snapshot']['head']}` + dirty WORKTREE, active_run NONE. Checkout не переключался. Production и записанный deployed release cfef63e3 не проверялись. Старые module01–08 отчёты и границы принятия сохранены.

Новый собственный PostgreSQL17.10, контейнер `social-qa01-fix-2026-10-16-r1-pg`, loopback44905, database/role `social01_fix_r1`; HTTP `127.0.0.1:33741`, текущий PID {v['source']['pid']}. Python3.12.3, Django6.0.2, Chromium153.0.8010.36. Первоначальный seed создал20fictional accounts/24typed targets, reviews0. Все проверяемые review submit/approve/reject переходы выполнены через native UI, без ORM-подмены.

DJANGO_TESTING=1; inherited credentials очищены до settings; .env/manage.py не загружались. Отдельные LocMem cache, media/private-media/staticfiles/email и cookies. File-based email только локально. Socket guard разрешает лишь собственный PG. Browser contexts блокируют внешний transport. Новая RU/AZ/EN сборка из текущих PO проверена штатным builder до django.setup; единственный LOCALE_PATHS — собственный `.tmp/social-qa01-fix-2026-10-16-r1/locales/locale`. Shared MO не переписаны.

[Entry](entry.json), [isolation/runtime](runtime-info.json), [locale manifest](locale-manifest.json), [source/PID/template/MO gate](runtime-source-final.json), [verification](verification.json).

## 2. Что исправлено

В `src/catalog/templates/catalog/typed_reviews.html` существующий select получает selected из candidate.rating, иначе из сохранённого head.rating. Пустая новая форма остаётся пустой и required. Head уже содержит current projection либо оценку первого отклонённого отзыва; новая бизнес-логика не вводилась.

Новый `src/catalog/testcases/test_social_qa01_rating_readback.py` содержит7meaningful regression methods. Это ровно два согласованных application/test файла, оба побайтно совпадают с approved candidate. [Reviewable diff](application.diff), [source match](approved-source-match.json). Controller, services, ACL, CAS, cooldown, schema, JS, CSS, PO и существующие tests/assertions не менялись.

## 3. Причина и RED → GREEN

До patch select не выбирал ни одну сохранённую option. В предыдущем [свежем recheck](../social-qa01-recheck-2026-10-16-r1/REPORT.md)8nativeFAIL подтверждали pending/approved для4типов.

Новый целевой RED:7methods выполнены,1PASS/6failing methods,61assertion failures,0errors; все по пустому rating вместо сохранённого. После patch — **11/11unique methods PASS**:7новых +4затронутых shared; exit0. Существующие assertions не ослаблялись. [Counts/source](test-results.json), [RED](regression-red-ready.txt), [GREEN](regression-green.txt).

Тесты проверяют пустой/чужой редактор, pending4, approved5, candidate2 поверх live5, первый отказ3, отказ edit1 поверх live4, reload→resubmit неизменного rating и escaping. Shared subset проверяет язык, candidate/live projection, ACL/stale moderation и сохранность revision reactions. Полный module/global корпус не запускался.

## 4. Native browser

**{b['pass']}PASS /0FAIL accepted observations**, {b['matrix_states']} rendered state cells, {b['png']}nativePNG. Counts — assertions, а не число независимых дефектов.

Основная матрица: четыре типа × empty/pending/approved/pending-edit/rejected-edit/rejected-first × RU/AZ/EN ×360/390/768/1024/1280/1440. Это {b['matrix_observations']} наблюдений: фактическое значение select, текст/CAS, readonly public count/average, Tab/ShiftTab/focus-visible, safe HTML и document overflow. Состояния создавались нативно и затем читались на18cells; одинаковые mutation suites во всех18cells не дублировались.

Native key flows прошли отдельно RU/AZ/EN390/1440: create4→reload→approve→reload; edit2 при live4; resubmit4 без повторного выбора; reject edit→current4; первый reject3 без current. Реальный cooldown120s сохранён: новые POST делались после его истечения, часы/policy не менялись. Unit-only cooldown0 явно SIMULATED.

Дополнительно ArrowDown/Up/Space/Escape и достижение submit с клавиатуры; outsider/guest не видят приватные candidates/rejected texts. Реальный stale second-tab POST получает409 и не перезаписывает новуюcandidate5; Back/reload восстанавливает5. Сам raw409 editor-less экран — известный SOCIAL03, здесь не исправлялся и не принят как полноценный conflict UX. Два явных SIMULATED delayed/aborted transport checks сохраняют прежнюю DB candidate и восстанавливают выбранный rating на свежем native GET; UI во время полной document navigation не объявляется сохраняющим старый DOM.

[Все observations](matrix.json), [CSV](matrix.csv), [PNG SHA/dimensions](png-manifest.json), [representative visual review](manual-png-review.json), [readonly final state](state-final.json). PNG — нативные captures; вручную просмотрена representative selection, остальные проверены автоматизацией по DOM/geometry/value и PNG integrity. Непрерывный ручной просмотр каждого PNG не заявляется.

| Фаза | Accepted assertions |
|---|---:|
{phases}

## 5. Data/security и пределы

В финальной БД по каждому case/type публичная current contribution одна: average4/count1. Rejected edit2 остаётся историей; первый rejected3 не имеет current/candidate. Повторный отзыв не создаёт второй current head. Readbacks — READ ONLY transactions с5s statement/2s lock timeout. Author-only head selection и существующие ACL/CAS не менялись.

В основных матрицах неожиданных local HTTP/JS/console ошибок0. В смешанном history/transport сценарии отдельно наблюдался1global view-transition pageerror и aborted navigation; JS/CSS не менялись, этот общий сбой не исправлен и его introduction UNKNOWN. Три завершённые CAS/Back проверки сохранены; два transport checks выполнены отдельно в свежем контексте и прошли. Реальный409/simulated failed request отделены от blocked external font diagnostics. Внешние fonts/offline transport явно SIMULATED/offline; успешность Google/SMTP/SDK не заявляется. Geometry evidence относится к этим локальным условиям.

## 6. Сохранность

Входные {p['entry_files']}files проверены по hash; изменились только согласованный template и текущий статус в guide. Новый regression — отдельно разрешённое добавление. Missing/unexpected changes0, sharedMO/index/HEAD/branch/active_run MATCH. {p['foreign_containers']}входных containers: те же identities/names/ports/state. Foreign restarts0. [Фактические процессы](verification.json) содержат PID/argv comparison; на входе этого fix-run был один QA HTTP.

Пять более ранних QA HTTP исчезли при явном user interruption до этого fix-run; их историческая continuity остаётся NOT VERIFIED и не превращается в PASS. В текущем run перезапускался только собственный HTTP из-за изменения служебного QA URL, приложение после GREEN не менялось. Исторические отчёты/данные не очищались.

## 7. QA/environment incidents

Первый RED был запущен до PG readiness:7bodies NOT RUN, environment failure. После pg_isready выполнен настоящий RED.

Первый create-case1 helper readback использовал ?case=1; canonical301 удалил служебный query и вернул case0. Исправлен только QA helper на `/qa/state/<case>/`; один уже сохранённый Place отзыв прочитан и продолжен без второго POST/cleanup. Оригинальный incomplete script/result сохранён и исключён из accepted observations; успешные case0/empty suites не повторялись. [Harness notes](harness-notes.md), [exclusions](excluded-observations.json). Последняя mixed-history попытка имела3PASS и незавершённое transport continuation после global view-transition error; повторены только2transport checks в свежем контексте. В итоговых2235observations три PASS сохранены явно из partial result, complete всей partial попытке не приписан. CLI exit0 сам по себе не считался PASS.

## 8. Команды и NOT RUN

Точные argv/exits/durations — [commands.jsonl](commands.jsonl), [контейнер](create-container.json). Основные команды:

```bash
.venv/bin/python docs/qa/social-qa01-fix-2026-10-16-r1/runtime.py test catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests
# RED ready: exit1; после patch тот же7 +4точных shared labels: exit0,11PASS
python3 docs/qa/social-qa01-fix-2026-10-16-r1/start_green.py
python3 docs/qa/social-qa01-fix-2026-10-16-r1/batch_browser.py <phase:case:language...>
# Каждая actual generated script и argv записаны в ledger; semantic complete/status проверяются отдельно
.venv/bin/python docs/qa/social-qa01-fix-2026-10-16-r1/verify.py
```

NOT RUN: полный ACCEPT09 (один раз после всех задач), global corpus, полноценная приёмка других SOCIAL ID, production/commit/push/deploy, physical devices/screenreader/другие браузеры, реальные SMTP/Google/SDK и прочие внешние integrations. Ничего из этого не объявляется PASS.

## 9. Итог и следующий шаг

**SOCIAL-QA-01 CLOSED LOCAL** в описанном scope; новых findings внутри выбранного восстановления rating не установлено. Сохраняются известные соседние SOCIAL02/03 и очередь остальных ID. Следующий шаг — отдельный свежий PLAN SOCIAL-QA-02 о причине отказа. Его реализация требует нового конкретного scope approval. Модуль09 ещё не закрыт; module10 автоматически не начинается.
'''
(H/'REPORT.md').write_text(text)
