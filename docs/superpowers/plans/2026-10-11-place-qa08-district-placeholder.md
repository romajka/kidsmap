# PLACE-QA-08 District Placeholder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Канонические `.agents` и прямые ограничения пользователя имеют приоритет. Этот документ — предложение scope, не разрешение на реализацию или запуск дополнительных агентов.

**Goal:** Закрыть одну причину PLACE-QA-08 / CROSS-QA-03: пустая option района в RU должна показывать «Выберите район».

**Architecture:** Сохранить gettext-вызов и политику языка в `configure_location_choices`. Восстановить активный RU перевод существующего ключа. Проверять результат на новой изолированной сборке RU/AZ/EN через существующий locale helper.

**Tech Stack:** Django, gettext PO/MO, существующий Python helper, PostgreSQL на отдельном loopback-порту, реальный браузер.

**Spec:** `docs/qa/module01-recheck-2026-10-11-r1/PLACE-QA-08-repair.txt`, `PLACE-QA-08.md`, `REPORT.md`; `docs/qa/module-acceptance-prompts.md`, раздел 01.

## Global Constraints

- Статус на 2026-10-11: PLAN ONLY, implementation NOT RUN; выбор следующего scope ожидается от пользователя.
- Без commit/push/deploy/production. Не переписывать PLACE-QA-01–07, существующие assertions, общие MO, чужие runtime и отчёты.
- Только DJANGO_TESTING=1, новая изолированная DB/cache/media/private-media/email, вымышленные данные; без production credentials и внешних интеграций.
- Сохранить district codes, geographic validation, request-language/fallback policy, ACL, candidate/live и публичный адрес.
- RU/AZ/EN × 360/390/768/1024/1280/1440; реальные browser evidence и native save/reload.
- Закрытие этого finding не означает полной приёмки module01. Её пропущенные сценарии остаются NOT RUN до отдельного выполнения.

## Проверенный исходный контекст

- Фактический checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; 18 изменённых tracked-файлов и чужие untracked artifacts.
- `docs/task33/implementation-status.md:7`: `active_run: NONE`.
- Read-only OS inspection: localhost:8841 слушает PID 16156; loopback:55446 слушает PID 17536. Проверка HTTP/DB и browser в этом планировании не выполнялась.
- `src/catalog/services/locations.py:552–566`: `configure_location_choices(form)` использует `_('Выберите район')`; callers в `src/catalog/forms.py:1493,2056`.
- `locale/ru/LC_MESSAGES/django.po:18354–18355`: запись только `#~ msgid` / `#~ msgstr`. AZ: активный `Rayon seçin`; EN: активный `Select district`.
- Codebase Memory project `C-kidsmap`, root `C:/kidsmap`, index ready; generation `2026-10-11T14:26:04Z`. Для locations.py и RU PO coverage_unavailable / metadata_changed; вывод о причине проверен непосредственно по source.
- Свежий recheck из REPORT — предыдущий запуск: 38 Django + 34 Node + 9 helper PASS; browser 252 PASS / 6 FAIL одной причины / 12 scope NOT RUN; 164 native PNG. Эти числа не являются результатами исполнения этого плана.
- PLACE-QA-06 имеет PASS только для описанного fresh compiled profile; состояние общих MO и других runtime этим не подтверждается.

## Task 1: Восстановить перевод и проверить контракт

**Files:**
- Modify: `locale/ru/LC_MESSAGES/django.po`, только entry «Выберите район».
- Create: `src/catalog/testcases/test_place_qa08_district_localization.py`.
- Create after approval: `docs/qa/place-qa08-fix-2026-10-11-r1/` — собственный launcher/settings, evidence и отчёт; если путь уже занят, выбрать следующий rN без перезаписи.
- Modify after verification: только строка 01 `docs/qa/module-acceptance-prompts.md`.
- Reuse read-only: `scripts/build_isolated_locales.py`, `docs/qa/isolated-locale-build.md`, recheck `run.py` / `qa_settings.py` как образцы.

**Interfaces:**
- Consumes: `catalog.services.locations.configure_location_choices(form)`; form с полями `region` и `district`.
- Produces: активный RU gettext mapping, прежние AZ/EN labels и стабильные значения choices.

- [ ] Перед выполнением повторно проверить разрешение на этот scope, HEAD/WORKTREE/active_run, занятые порты и сохранность чужих файлов. Зафиксировать entry hashes. Не подключать новый тест к чужому launcher.
- [ ] Подготовить собственный launcher: новые DB/container/порты/cache/media/private-media/email и ignored scratch, отключённые integrations. Выбирать свободные порты после проверки; не переиспользовать 8841/55446, чужую DB или browser session. Применять migrations только в собственной DB. Startup gate должен проверить manifest до django.setup, задать единственный LOCALE_PATHS и подтвердить ожидаемые RU/AZ/EN. Сохранять только безопасные доказательства изоляции.
- [ ] Добавить следующий отдельный regression test; существующие тесты не менять:

```python
from django import forms
from django.test import SimpleTestCase
from django.utils.translation import gettext, override

from catalog.services.locations import configure_location_choices


class LocationProbeForm(forms.Form):
    region = forms.ChoiceField(required=False)
    district = forms.ChoiceField(required=False)


class DistrictLocalizationTests(SimpleTestCase):
    def test_empty_option_matches_request_language(self):
        expected = {
            "ru": "Выберите район",
            "az": "Rayon seçin",
            "en": "Select district",
        }
        for language, label in expected.items():
            with self.subTest(language=language), override(language):
                form = LocationProbeForm()
                configure_location_choices(form)
                choices = list(form.fields["district"].choices)
                self.assertEqual(gettext("Выберите район"), label)
                self.assertEqual((choices[0][0], str(choices[0][1])), ("", label))
                self.assertInHTML(
                    f'<option value="" selected>{label}</option>',
                    str(form["district"]),
                )

    def test_language_switch_keeps_district_values(self):
        all_values = []
        for language in ("ru", "az", "en"):
            with override(language):
                form = LocationProbeForm()
                configure_location_choices(form)
                values = [value for value, _ in form.fields["district"].choices]
                self.assertEqual(values[0], "")
                self.assertIn("baku_yasamal", values)
                self.assertEqual(form.fields["district"].clean("baku_yasamal"), "baku_yasamal")
                all_values.append(values)
        self.assertEqual(all_values[0], all_values[1])
        self.assertEqual(all_values[1], all_values[2])
```

- [ ] Собрать baseline locales в новом ignored output существующим helper и запустить новый тест только через собственный проверенный launcher. Ожидается RU FAIL с `Rayon seçin`, а не environment failure. Если воспроизведения нет, выяснить фактический runtime/catalogue до изменения PO.

```powershell
.venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/place-qa08-fix-20261011-r1/baseline-locales --locales ru az en --compiler wsl
.venv\Scripts\python.exe scripts/build_isolated_locales.py verify --manifest .tmp/place-qa08-fix-20261011-r1/baseline-locales/manifest.json
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py test catalog.testcases.test_place_qa08_district_localization
```

Команды являются запланированными, сейчас не исполнялись. Собственный launcher сначала должен пройти проверку изоляции; имена r1 применять только если свободны. Если GNU msgfmt недоступен в WSL, проверить native msgfmt; не заменять compilation старым MO.

- [ ] Реактивировать только найденную obsolete пару, без массового обновления каталога:

```diff
-#~ msgid "Выберите район"
-#~ msgstr "Выберите район"
+msgid "Выберите район"
+msgstr "Выберите район"
```

- [ ] Собрать исправленные locales в другом новом output и переключить только собственный launcher на verified manifest. Запустить в свежем процессе, чтобы не использовать gettext cache предыдущей сборки.

```powershell
.venv\Scripts\python.exe scripts/build_isolated_locales.py build --output .tmp/place-qa08-fix-20261011-r1/fixed-locales --locales ru az en --compiler wsl
.venv\Scripts\python.exe scripts/build_isolated_locales.py verify --manifest .tmp/place-qa08-fix-20261011-r1/fixed-locales/manifest.json
.venv\Scripts\python.exe docs/qa/place-qa08-fix-2026-10-11-r1/run.py test catalog.testcases.test_place_qa08_district_localization catalog.testcases.test_place_qa04_manual_location catalog.testcases.test_task33_place_nature_localization
```

- [ ] Сохранить реальные commands/counts/exit codes, baseline/fixed PO/MO SHA и startup source attestation; результат ожидания не выдавать за PASS.

## Task 2: Browser acceptance и ограниченное закрытие

**Files:** только собственная `docs/qa/place-qa08-fix-2026-10-11-r1/` и строка 01 журнала после проверки.

**Interfaces:** native owner editor → `select#id_district option[value=""]`; собственные synthetic candidate/live objects и публичная карточка для readback.

- [ ] Пройти RU/AZ/EN × 360/390/768/1024/1280/1440: реальное открытие dropdown, чтение первой option, native выбор пустого пункта, видимый label/focus, клавиатура и геометрия, console/network. Ожидания: RU «Выберите район», AZ «Rayon seçin», EN «Select district». Сохранить native PNG PC/mobile и матрицу по языку/ширине.
- [ ] Для screenshots пустого пункта использовать отдельный unsaved browser context с блокировкой non-GET после login; обозначить это SIMULATED. Readback должен подтвердить, что пустой выбор не изменил server/candidate/live.
- [ ] В отдельном обычном контексте выполнить native save/reload корректно выбранного `baku_yasamal` на трёх языках. Сверить сохранённый code, candidate/live и публичный адрес; проверяемые переходы не выполнять ORM-сохранением. DB readback только read-only, без вывода private records.
- [ ] Сверить source/PO/MO SHA запуска и конечных файлов, entry hashes чужого WORKTREE, active_run, общие MO и чужие listeners. Не останавливать/перезапускать чужие процессы.
- [ ] Записать новый REPORT, matrix, screenshot manifest и команды; квалифицировать FAIL/NOT RUN/SIMULATED и scope. При успехе закрыть только PLACE-QA-08 / CROSS-QA-03 в собственном отчёте и строке 01, сохранив ссылки на историю и остальные байты журнала. Не переписывать module13 и canonical MASTER_AUDIT без отдельного scope.

## Альтернативный scope для решения пользователя

AUDIT ONLY недостающей полной приёмки module01: отдельный новый изолированный стенд со свежими locales; перечень непокрытых требований из REPORT §7 и исходного module01 prompt; функциональные, ACL/concurrency/recovery и browser проверки; новые evidence/repair prompts, без исправления приложения. PLACE-QA-08 остаётся открытым. Выбор этой альтернативы не разрешает выполнять Task 1 данного плана.

## Проверка плана

Покрыты: один root cause/alias, минимальный PO diff, воспроизводимый RED/GREEN контракт, fresh isolated locales и startup gate, 18 browser клеток, native round-trip, сохранность data/source/runtime, scoped report/журнал. Implementation, новые tests/browser и полный module01 в этом планировании NOT RUN. Поддержка отдельными агентами не запускалась.
