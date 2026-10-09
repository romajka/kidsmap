# Профиль специалиста: внедрение и локальная приёмка — 2026-10-07

Согласованный scope A–D реализован: предложение профиля, собственный кабинет подтверждённого специалиста и административный редактор. Новые проверки выполнялись на текущем WORKTREE; старый аудит использован для гипотез, а не как доказательство исправления. Другие сущности в этом запуске не переделывались. Работу выполнял один агент последовательно.

## Версия и изоляция

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`; `active_run=NONE` при начале.
- Начальное WORKTREE: 144 строки status, 5078 файлов в манифесте. Рабочее дерево включало чужие изменения постоянных мест, организаций и других задач. Они сохранены; проверка SHA256 стартовых файлов не обнаружила изменений вне согласованных файлов и пометки плана.
- Финальный исходный runtime digest: `33bd6c325700ce553d9108f2c140163c248af6730f4bf087ca91914bc0f921ed`. `/qa/acceptance-version/` подтверждает HEAD/digest, `DJANGO_TESTING=true`, отсутствие внешних credentials, локальные cache/email.
- Стенд: [localhost:8786/qa/](http://localhost:8786/qa/). Локальные синтетические роли: `demo_owner` — автор/организация, `demo_person` — подтверждённый специалист, `demo_moderator` — проверяющий, `demo_outsider` — посторонний. Вход кнопками QA; реальные пользовательские данные не использованы.
- Отдельные PostgreSQL container/volume/socket, DB `qa_stage04`, тестовая DB `test_qa_stage04`, раздельные media/private-media/cache. Контейнер `kidsmap-specialist-implementation-20261007`, network none; серверные guards не допускают внешний DB/network. Другие локальные стенды не перезапускались. Внешняя браузерная интеграция не принималась.
- Миграция `0140_specialist_proposal_draft` применена только на этом стенде и свежей тестовой БД. Production не проверялся и не менялся. Commit/push/deploy не выполнялись.

## Что исправлено и почему

| Причина | Изменение |
|---|---|
| Admin template определял группы по русским подстрокам переведённых заголовков: в AZ/EN исчезали поля | Стабильные идентификаторы 12 разделов; сохранён configured editable/readonly inventory. Исходные и новые AZ/EN снимки приведены ниже |
| Очная готовность могла выводиться из raw checkbox presence вместо валидированных строк | Проверка active/not DELETE/Place либо адрес по cleaned formset; текущие model clean/region rules сохранены. Для новой формы inline получает настоящий parent object |
| Общая цена/телефон при обычном сохранении перезаписывали данные основного места | Отдельный ограниченный formset мест; локальные контакты/цены и ID сохраняются независимо. Новое место не наследует их молча |
| Длинная admin-форма и маленький поиск направлений | 12 anchors, mobile выбор раздела, 29 native searchable checkboxes, live counts, фокус; сводка ошибок ведёт в конкретное поле. Кабинет сохраняет существующие 5 этапов |
| Автор канонического предложения не имел права повторно открыть Specialist editor | Отдельная приватная рабочая копия предложения до отправки: version, allowlisted public payload, приватное временное фото. Отправка создаёт один Specialist с created_by, без person/owner authority; повтор возвращает существующий результат |
| Общий legacy browser key мог подставлять чужой или устаревший ввод | Recovery ключ actor/entity/schema/base revision, явное восстановление. Файлы/документы/tokens не записываются. После успешного ответа очищается соответствующая копия; конфликт не перезаписывает сервер |
| Сохранение и готовность не объясняли реальное состояние | Раздельные dirty/saving/saved/error/conflict, серверная дата, требования текущего действия. Показано действующее снятие опубликованного профиля после owner-save; нет обещания серверного автосохранения |
| Не все публичные сведения были доступны, цена 0 исчезала | Необязательные alternate name/education/experience texts, языковые поля без генерации переводов; NULL стаж отличён от 0. Цена 0 выводится в профиле и месте |
| Неясные связи автора, личности и сотрудничества | Точные scoped labels; место приёма не подтверждает employment. Identity остаётся private, reviewer не ставит публичное согласие от имени человека |

Сохранены дедупликация 29 направлений и черновик первого шага. Admin и owner требования не унифицированы. Общий контакт по-прежнему обязателен при отправке; филиальный телефон его не заменяет. Owner address change/deactivation сохраняет историю; online отключает места, возврат требует явного выбора. Legacy admin delete/address semantics не заменялись новым owner history workflow. Права автора/организации/проверяющего и согласия на документы не расширены. Организационные приглашения не превращаются автоматически в место приёма.

Основные изменения: `domain_admin/specialist.py`, owner/admin templates и JS/CSS, `forms_specialist_locations.py`, owner use case/controller, приватные model/service/routes рабочей копии, migration0140, public specialist template, scoped labels и RU/AZ/EN. Новые регрессии находятся в трёх `test_specialist_entry_* / test_specialist_proposal_drafts` модулях. `views.py` и общий admin submit template не менялись в этом запуске.

## Свежие результаты

PASS означает выполненную проверку в указанном слое; NOT RUN — сценарий целиком в этом слое не выполнялся. Наличие UI не считается доказательством успешного сохранения.

| Сценарий | Сервер | Браузер | Доказательство |
|---|---|---|---|
| Пустое/частичное предложение, черновик с каждого из 5 этапов, reload, выход/вход, продолжение | PASS | PASS | proposal tests, functional16, recovery4 |
| Невалидная отправка, сохранение введённого текста, переход к ошибке | PASS | PASS | functional16; focus/step phone |
| Отправка предложения, повторное нажатие: один Specialist, author editor/documents404 | PASS | PASS | proposal tests, functional16 |
| Три места с ценами35/60/0 и независимыми телефонами; общий contact edit не затирает их | PASS | PASS | locations tests, functional16, public card |
| Online save отключает места; both не включает историю; одна явная реактивация сохраняется | PASS | PASS | browser-formats3, неизменные ID/price/phone |
| Отправка, проверка/публикация, публичная карточка, изменение published→draft с предупреждением | PASS | PASS | moderation8; публичная draft-карточка404 |
| Отказ профиля с причиной и все состояния claim/employment | PASS | NOT RUN целиком | existing domain/security/transfer suites; browser подтвердил approve/confirm |
| Пустой стаж и 0 лет; общая и локальная цена0 | PASS | PASS частично | NULL draft reload и public price0; 0 лет renderer серверно |
| Две вкладки owner и admin: stale action отклонён, версия не подменена | PASS | PASS | functional16, moderation8, conflict screenshots |
| Подтверждение личности по отдельному запросу; приглашение сети требует подтверждения человека | PASS | PASS | privacy9; права появились после review |
| Identity private; certificate consent+review+publish; отзыв закрывает anonymous download | PASS | PASS | privacy9: certificate200/identity404, после отзыва404, no-store |
| Автор/посторонний/org owner/обычный admin/dedicated reviewers, tampered IDs, текущие epochs | PASS | PASS частично | 113 tests; browser author/outsider/org owner/moderator. Обычный restricted admin не проверялся визуально |
| Фото: keyboard file chooser, серверный черновик/reload, ошибка файла400 с сохранённым текстом | PASS | PASS | photo-native1, functional16, final-shots2 |
| RU/AZ/EN ×360/390/768/1440, proposal/person/admin add/change/docs/invites | PASS inventory | PASS 72/72 | final browser matrix, scrollWidth≤viewport, 5 stages/29 directions |
| Клавиатура: steps/search/checkbox/bio tabs/photo/jump/Escape; admin без JS | — | PASS 11/11 | keyboard log, native controls и фокус |
| Format keyboard RU/AZ/EN ×4 ширины; extra320/1024/1280 owner/admin | — | PASS 30/30 | extra log; keyboard12 + responsive18 |
| System check / specialist migration graph | PASS | — | 0 issues, единственный catalog leaf0140, applied true |
| Полная репозиторная migration-drift проверка | FAIL baseline | — | dry-run обнаруживает прежние Meta options Activity/OfferingGroup/Organization/Program; не включены в0140 |
| Новые whitespace ошибки согласованного diff | PASS | — | before→current scoped diff check: 0 diagnostics |

Итого: **113 targeted server tests, 0 failures/errors**; **156 браузерных assertions, 0 FAIL** в сохранённых журналах. Это не 156 независимых end-to-end сценариев: часть — повторные responsive/keyboard проверки. Финальная 72-case матрица и снимки сняты после последних CSS изменений. После серверных тестов изменились только два specialist templates и два CSS файла; SHA256 всех Python файлов совпадают с проверенной версией.

Точная серверная команда (очищенный env/guards задаёт wrapper):

```bash
.venv/bin/python .tmp/specialist-implementation-20261007/run.py \
  catalog.testcases.test_task33_specialist_domain \
  catalog.testcases.test_task33_specialist_privacy \
  catalog.testcases.test_task33_specialist_workspace \
  catalog.testcases.test_task33_specialist_screens \
  catalog.testcases.test_task33_specialist_screens_security \
  catalog.testcases.test_task33_specialist_security_review \
  catalog.testcases.test_task33_specialist_transfer \
  catalog.testcases.test_task33_specialist_retention \
  catalog.testcases.test_specialist_entry_admin \
  catalog.testcases.test_specialist_entry_locations \
  catalog.testcases.test_specialist_proposal_drafts
.venv/bin/python .tmp/specialist-implementation-20261007/run.py --script local_checks.py
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session spec-final-20261007 run-code --filename .tmp/specialist-implementation-20261007/browser_matrix.js
```

[Полный server log](/home/ramin/.local/share/kidsmap-qa/specialist-profile-2026-10-07/targeted-final.log), [browser summary](/home/ramin/.local/share/kidsmap-qa/specialist-profile-2026-10-07/browser-summary.json), [72-case matrix](/home/ramin/.local/share/kidsmap-qa/specialist-profile-2026-10-07/browser-matrix-final.json), [runtime metadata](/home/ramin/.local/share/kidsmap-qa/specialist-profile-2026-10-07/stand-version.json), [preservation](/home/ramin/.local/share/kidsmap-qa/specialist-profile-2026-10-07/preservation.json). Там же fresh functional/moderation/privacy/keyboard/format/recovery logs, source manifests и исходные RED-regressions. Журналы содержат только синтетический QA namespace; credentials, production records и graph caches не сохранялись.

## Скриншоты

Финальный admin PC:

![Admin PC](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/final-admin-pc.png)

Финальное место приёма на телефоне:

![Person mobile](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/final-owner-mobile.png)

[Кабинет PC](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/final-owner-pc.png), [admin mobile](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/final-admin-mobile.png), [ошибка фото](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/photo-error-mobile.png), [публичная карточка](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/public-card-390.png), [owner conflict](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/owner-conflict-390.png), [admin conflict](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/admin-conflict-390.png).

[До: admin AZ PC](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/before-admin-az-1440.png), [до: admin EN mobile](/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/acceptance-2026-10-07/before-admin-en-390.png). Остальные выбранные снимки proposal/person/docs/invitations/add/change и before RU/AZ/EN — в этой же папке. Финальные screenshots — synthetic runtime этого отчёта, не исторический prototype.

## Что не проверено

- Полный project suite, production, применение миграции на production/реальных данных.
- Реальные телефоны, виртуальная клавиатура ОС, VoiceOver/NVDA, каждый control клавиатурой на всех языках/ширинах. Проверка браузером выполнялась в desktop engine с указанными viewport.
- Реальные доставка email/внешние интеграции, внешнее media storage, полный HEIC pipeline.
- Storage quota/disabled storage в браузере, все варианты simultaneous browser recovery; fallback проверен исходным кодом, не свежим браузерным сценарием.
- Каждый reject/stale claim/changed organisation owner/inactive-person сценарий через UI; эти границы покрыты серверными suites, но не считаются browser PASS.
- Порядок галереи: у специалиста здесь одно основное фото. Галереи мест/мероприятий, их занятия/группы/тарифы и общая приёмка четырёх сущностей не входят в этот scope.

Открытое ограничение вне specialist scope — старый Meta-options migration drift из таблицы. Его исправление не включено. Плановые checkbox ниже в исходном плане не превращены автоматически в полное browser approval: точная граница выполненных проверок указана здесь.

## Повторный запуск собственного стенда

```bash
.venv/bin/python .tmp/specialist-implementation-20261007/capture_runtime.py
.venv/bin/python .tmp/specialist-implementation-20261007/launch.py
```

Launch управляет только собственным8786 PID/контейнером, не другими стендами; manifest сверяется до запуска. Переход в QA → вход нужной synthetic ролью → кабинет/админка. После acceptance format-проверки профиль1 — draft/both с одним явно включённым местом; proposal6 отправлен, proposal4 был опубликован. Это состояние тестовых данных, а не regression.
