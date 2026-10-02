# Этап 08 — независимый backend review

Canonical role `.agents/agents/django-reviewer/agent.md`; reviewer `/root/stage07_review`, 2026-09-30. Bounded AUDIT по поручению primary: source/publication ingress, личный isolated QA, legacy retention. Application не редактировалась. Production UNKNOWN: не подключались. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE; HEAD не содержит текущую реализацию. Личный финальный срез: 50 source SHA совпали до и после свежих запусков (digest `83ae7b97a3963fed61b4a410de626a7f200e8fbe059e056fc61f551e87bbf5c0`). От первого `08-handoff-manifest.json` изменены только `domain_admin/place.py`, `services/publication.py`, `services/publication_forms.py`; это проверенные исправления после первого review.

**PASS bounded independent review 08.** Подтверждённых незакрытых backend blocker findings в проверенном scope нет. После первого review primary исправил `PlaceAdmin.mark_pending`/formset metadata, ошибку фото storage boundary, сохранение volunteer rejection note при draft и attribution `moderated_by`; reviewer сверил actual source и лично повторил проверки. Это не вердикт по full canonical suite или production.

Source: `services/publication.py:propose/review/publish`, `publication_forms.py:source_version/save_form`, `volunteer_places.py:revision_base_matches/adopt_legacy_revision/review_proposal`, `organization_ownership.py:moderate_place_request`, `domain_admin/place.py:changeform_view/save_model/save_related`, `domain_admin/volunteer.py:edit/review`, models/migrations 0120–0121, owner/CSV adapters и public queryset. Typed revision использует существующий VolunteerPlaceRevision как один candidate pipeline. Pending/rejected оставляет approved live; цена и расписание применяются при explicit save, зависимые условия суммы проходят единым пакетом; approval патчит только согласованные поля и проверяет dependencies/source. Новая закрытая published карточка остаётся в detail queryset и исключается из обычного каталога. Category.code — PK; прежнее предположение reviewer о mismatch category_id было ошибочным и отозвано.

Личный запуск:

```text
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_publication --output /tmp/task33-08-independent-final-20260930-052128Z
```

Результат: **37 tests, 0 failures, 0 errors, 0 skipped, exit 0, 6.553s**; `django check`, `makemigrations --check --dry-run` PASS; catalog migration leaf 0121, unapplied 0. Disposable PostgreSQL17 через Unix socket, network none/no published ports/tmpfs; `DJANGO_TESTING=1`, isolated cache/email/media, network+libpq guards, no production credentials; cleanup PASS.

Отдельный /tmp-only QA04 extension запускался командами:

```text
python3 /tmp/task33-08-review-tools/run.py --mode probe --output /tmp/task33-08-independent-extras-final-20260930-052128Z
```

Свежий extension exit 0, cleanup PASS. На синтетических данных подтверждены: pending legacy PUBLICATION request со старой candidate version отказывает approval без live/status write; populated 0119→0121 сохраняет все прежние значения одного VolunteerPlaceRevision и новые typed defaults; adoption нормализует старый full payload в один реально изменённый `description_az`, сохраняя author/place/version. Staff review GET и admin candidate GET, volunteer edit GET имеют `conflict=False`; resave через volunteer POST сохраняет исходного author и approved live. Admin `PlaceAdminForm` отвергает invalid signed publication token, а `PlaceAdmin.save_model` отказывает при изменении content_version между validation и save; candidate не создан. Скрипты/сырые данные только в /tmp, в evidence сохранены агрегаты/booleans.

Исторический первый admin probe `/tmp/task33-08-independent-admin-20260930-052128Z` остановился на неверном ожидании scratch harness: invalid signed token отклоняется уже `PlaceAdminForm.is_valid`, раньше `save_model`. После исправления только /tmp probe повторён, затем снова пройден на финальном source SHA; это не application failure. Старые volunteer test ожидания full `revision.payload` не подходят к принятому sparse patch контракту; current editor читает live+patch. Parent отдельно классифицирует full suite и legacy baselines, assertions не менялись.

Independent full canonical suite, rendered browser, production, external integrations и этап 09 **NOT RUN** этим reviewer. Codebase Memory прошлый граф имел best-effort coverage; текущие новые source changes сверены с actual files, не выводились из graph absence. Named handoff: **primary django-reviewer `/root`** — совместить этот report с собственным full suite/baseline и browser evidence, записать основной `reports/08.md`/журнал и снять active_run только после criteria. Evidence: [08-review-evidence.json](08-review-evidence.json).
