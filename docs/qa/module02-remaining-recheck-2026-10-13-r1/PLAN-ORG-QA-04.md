# ORG-QA-04 — конкретный план переводов

Статус PLAN READY / IMPLEMENTATION NOT RUN. Scope только остаточные подписи административного редактора организации ORG-QA-04. Snapshot соответствует entry.json.

## Причина и точные файлы

Свежий isolated gettext и реальные PNG подтверждают:14 exact msgid отсутствуют, один (`Одобрить заявку`) имеет fuzzy и исключается компилятором. Lazy section/model/readonly labels следуют текущему override в том же процессе, frozen import-time причина не подтверждена.

Изменить только `locale/az/LC_MESSAGES/django.po` и `locale/en/LC_MESSAGES/django.po`: добавить отсутствующие14 entries с source references, обновить fuzzy entry `Одобрить заявку` проверенным переводом и снять fuzzy только с него. Не запускать массовый makemessages/rewrite, не менять другие fuzzy/headers/PO entries, RU/общие MO/backend/templates. Полный список и согласуемые тексты в proposed-copy.json и таблице ниже.

| RU msgid | AZ | EN |
|---|---|---|
| Названия | Adlar | Names |
| Организации | Təşkilatlar | Organizations |
| Владение | Sahiblik | Ownership |
| Проверка данных | Məlumatların yoxlanılması | Data verification |
| Владелец не назначен | Sahib təyin edilməyib | No owner assigned |
| Владение проверено | Sahiblik yoxlanılıb | Ownership verified |
| Владение не проверено | Sahiblik yoxlanılmayıb | Ownership not verified |
| Связанные разделы | Əlaqəli bölmələr | Related sections |
| Текущие и предложенные данные | Cari və təklif olunan məlumatlar | Current and proposed data |
| Программы | Proqramlar | Programs |
| Черновик и проверка не меняют публичные данные до одобрения. | Qaralama və yoxlama təsdiqdən əvvəl açıq məlumatları dəyişmir. | Drafts and review do not change public data before approval. |
| Приглашённый редактор сможет менять организацию и общие программы после принятия приглашения. | Dəvət olunan redaktor dəvəti qəbul etdikdən sonra təşkilatı və ümumi proqramları dəyişə biləcək. | The invited editor can edit the organization and shared programs after accepting the invitation. |
| Email сотрудника | Əməkdaşın email ünvanı | Employee email |
| Пригласить сотрудника | Əməkdaş dəvət et | Invite employee |
| Одобрить заявку | Müraciəti təsdiqlə | Approve submission |

Общие msgid (Организации, Программы, Одобрить заявку) имеют shared consumers; их затронутые admin headings/buttons включить в точечную проверку. Другие русские sidebar labels или новые переводы не входят автоматически.

## Выполнение и acceptance

1. Snapshot/hashes/active_run/сохранность чужих changes. Новый unique `docs/qa/org-qa04-fix-2026-10-13-r1/` (или следующий rN), собственный LOCAL QA профиль, без .env/production credentials.
2. RED — текущие15 runtime fallback entries и видимые AZ/EN редакторы. Для translations не добавлять тест, просто повторяющий msgstr: gate проверяет реальные lazy labels/template output и сменуRU→AZ→EN→RU в одном Django процессе. Existing assertions не менять.
3. Внести только таблицу выше. Native msgfmt --check-format через existing isolated helper, новый уникальный каталог, manifest/verify и sole LOCALE_PATHS до setup; старые MO не трогать.
4. Native browser language switch в той же сессии, add/edit/draft/pending/published; создать/save/reload/candidate review/approve UI на fictional данных, сверить live/candidate. RU/AZ/EN ×6 widths, keyboard/focus, screenshots и error/conflict состояния в применимом scope. Runtime GET/readback с READ ONLY/timeout. Внешние обращения blocked/SIMULATED.
5. Shared labels в organization/program/review headings проверять на новом profile, targeted tests: `catalog.testcases.test_organization_admin_labels`, `catalog.testcases.test_task33_admin_editors.AdminEditorTests.test_organization_admin_draft_and_submit_use_candidate`, `...test_pending_editor_shows_current_and_candidate_separately`; не повторять весь корпус.
6. REPORT exact commands/exits/counts/PNG/hash/preservation/NOT RUN; закрыть только ORG-QA-04 при acceptance и обновить current guide status. Затем полная ACCEPT-02 строго audit-only по guide. Дополнительные findings оставить OPEN и согласовать отдельный scope.

Разрешённые files: два указанных PO, новые QA evidence в собственном run и current guide status. Backend/services/schema/ownership/connections и предыдущие fixes не менять. Без commit/push/deploy/production.
