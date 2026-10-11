# Fresh AZ analytics localization handoff

Role `analytics-reviewer`, `/root/analytics_source`; AUDIT ONLY; source-review ownership. Parent native browser confirmed AZ analytics labels remain Russian with AZ cookie and heading `Statistika`; evidence attributed to parent: [admin-filled-az-390.png](../screenshots/admin-filled-az-390.png). No independent rendered-browser execution here.

## Verified cause

`admin_analytics.py:74/81/88` wraps KPI labels with Django gettext; `:119` wraps chart subtitle. `templates/admin/catalog/site_analytics.html:18/26/57/82/113` wraps period label, updated status, chart title and table subtitles with `{% trans %}`. These are intended localized UI keys, unlike raw GA event names/paths which remain provider identifiers.

Current AZ PO contains the labels, but they are **fuzzy drafts**, several semantically wrong or with incompatible interpolation. Their current compiled MO has no matching keys and consequently returns the Russian source msgid. Normal AZ keys in the same MO resolve correctly: `Статистика` → `Statistika`, `Обзор Google Analytics 4` → `Google Analytics 4 icmalı`, `Уникальные` → `Unikal`, `Просмотры` → `Baxışlar`. This corroborates the parent's active-AZ page and establishes a bounded translation-content failure, not merely an unresolved language-cookie/runtime assumption.

| Key | Current AZ PO line | PO draft | Compiled MO |
|---|---:|---|---|
| Активные пользователи |11260|fuzzy; `Adi istifadəçi` (ordinary user)|key absent; Russian fallback|
| Сессии |11266|fuzzy; `Sessiya`|key absent; Russian fallback|
| Просмотры страниц |11272|fuzzy; contact-page text|key absent; Russian fallback|
| GA4, последние 30 дней |11278|fuzzy; `Son %(days)s gündə nə yenidir`|key absent; Russian fallback|
| Выбор периода |18483|fuzzy; quick links text|key absent; Russian fallback|
| Обновлено сегодня |18498|fuzzy|key absent; Russian fallback|
| Посещаемость |18504|fuzzy; site setting text|key absent; Russian fallback|
| События GA4 |18520|fuzzy|key absent; Russian fallback|
| Топ событий за последние 30 дней |18526|fuzzy|key absent; Russian fallback|
| Популярные страницы GA4 |18538|fuzzy; popular regions text|key absent; Russian fallback|
| Топ страниц за последние 30 дней |18544|fuzzy; unresolved `%(days)s`|key absent; Russian fallback|

Installed Django `compilemessages.py:54–58` exposes `--use-fuzzy`; `:76–77` adds msgfmt `-f` only when requested, while default options at35 are `--check-format`. **No compilation was performed.** Compiling alone is not a justified repair of these keys; approving corrected AZ translations and checking format/placeholders precedes reproducible locale compilation. Turning on fuzzy compilation would publish incorrect drafts and is not recommended.

Fresh command: `.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/source-review/locale_checks.py` — exit0, 15 selected keys inspected;11 fuzzy and11 absent from MO; all15 selected PO contents (msgid/msgstr/fuzzy) match current HEAD. PO/MO hashes recorded in [locale-checks.json](locale-checks.json); MO before/after bytes unchanged. An initial output-only Windows encoding error exit1 was corrected in the **own QA script**; no app/locale change or compilation. Source reads with a nonnumeric Select-Object argument were corrected without mutation.

## Deduplication and scope

Historical module10 [SITE-QA-07](../../module10-2026-10-10-r1/findings/SITE-QA-07.md) concerns three public-section switch labels where valid translated PO content is missing from the existing MO. It is a shared locale-pipeline dependency/checklist, **not fresh evidence here**. Current analytics labels are distinct keys with unapproved/incorrect **fuzzy PO** matching HEAD, not demonstrated stale MO omission of valid translations. If parent assigns an analytics finding, cross-link SITE-QA-07 as dependency and avoid counting the generic build pipeline twice.

Owner AZ delta uses a separate direct-template cause: `src/catalog/templates/pages/owner_analytics.html:32/44` uses EN `vs previous period`, else Russian `к прошлому периоду`, so AZ never reaches gettext for this phrase. Locale compilation cannot fix that owner phrase; retain it as separate bounded finding if parent native evidence confirms.

Classification: pre-existing selected HEAD localization-content failure; likely P2 for multilingual administrative metrics. Production locale state NOT RUN/UNKNOWN. Parent assigns final `ANALYTICS-QA-xx` and severity based on its fresh native evidence. Native GA fixture may be SIMULATED data, while these real template/compiled translation effects are observed under that fixture; do not claim real Google Analytics access.

Named handoff: `/root` consolidates fresh native AZ matrix and final defect; future `frontend-admin` / locale pipeline owner translates these exact keys, validates approved format-safe PO entries, builds MO reproducibly and reruns rendered AZ acceptance in separately authorized repair scope. No repair authorization inferred from this audit.
