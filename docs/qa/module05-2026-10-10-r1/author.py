"""Author own QA deliverables from observed facts, never application changes."""
from pathlib import Path
import json,re,hashlib
P=Path(__file__).resolve().parent;R=P.parents[2];(P/'findings').mkdir(exist_ok=True)
findings=[
('01','P2','Удалённая группа остаётся публичной после одобрения','owner → moderator → public','/ru/account/places/5/edit/; /admin/volunteer/review/5/; /ru/activities/2/',
'Открыть опубликованное занятие с двумя группами 4–6/20 AZN и 12–15/80 AZN. Раскрыть вторую группу, нажать «Удалить группу», отправить форму на проверку. В административном review одобрить. Перезагрузить публичное занятие.',
'Вторая группа перестаёт показываться в активном предложении после одобрения; история может сохраняться.',
'Группа исчезла из nested_pricing формы, POST200 и одобрение прошли, но группа #3 с тарифом80 AZN осталась в DB без archived_at и в public DOM.',
'lifecycle.result.txt; state-removed-group.json; screenshots/removed-group-still-public-390.png',
'src/catalog/services/pricing_plans.py:532 replace_nested_pricing; static/js/owner_place_offerings.js:143',
'Подтверждённая причина: JS удаляет строку из массива, replacement обрабатывает только присланные activity/groups и не архивирует отсутствующие группы. Владение ID валидируется, но отсутствие строки не применяется.',
'Ограниченный неверный публичный контент после успешного решения модерации; P2. Потеря production данных не исследована.',
'Nested replacement/publication, archive/visibility semantics, owner editor. Зависимости: PricingPlan history, candidate/live и транзакция одобрения.',
'Обеспечь предусмотренное контрактом удаление/архивирование отсутствующей группы при одобрении полного nested payload. Не интерпретируй частичный import как очистку. Проверь также пропуск занятия, удаление тарифа, foreign IDs, атомарность, историю и повторное одобрение. Воспроизведи полный UI путь и reload публичной карточки.'),
('02','P2','В редакторе групп нет обязательных полей регулярного абонемента','owner','/ru/account/places/5/edit/ → /ru/account/places/5/save-photos/',
'В тарифе группы выбрать membership, положительную точную цену, billing_mode=recurring и billing_interval=month. Нажать сохранение. Раскрыть дополнительные поля и проверить доступный ввод.',
'Владелец может задать обязательное число периодов и сохранить поддержанный регулярный тариф.',
'POST422: billing_interval_count «Укажите количество периодов больше нуля». Количество доступных controls для billing_interval_count и quantity_unit равно0. При one_time все13 product types сохранились.',
'functional4.result.txt; pricing.result.txt; screenshots/membership-missing-count-390.png',
'static/js/owner_place_offerings.js:126–138; src/catalog/models/pricing_plan.py:128–135; src/catalog/services/pricing_plans.py:normalize_pricing_plans',
'Подтверждённый разрыв UI/model: owner group advanced строит billing_mode/interval, но не count/cycles/quantity/unit. Позитивная installment запись через этот UI NOT RUN; отсутствие её controls подтверждено source.',
'Поддержанный recurring сценарий невозможно закончить через доступные controls; P2.',
'Owner group pricing editor/choices/copy; согласование с canonical PricingPlan validation. Не ослаблять DB constraints и существующие assertions.',
'Добавь согласованные с canonical pricing поля count/cycles/quantity/unit, условную видимость и сохранение значений. Обеспечь recurring и installment без фиктивных defaults. Проверь membership/month/count, installment/cycles, quantity/unit, переключение one_time, invalid0, RU/AZ/EN mobile/PC, native save и reload.'),
('03','P2','Сводка ошибки цены фокусирует выбор программы','owner','/ru/account/places/5/edit/ → save-photos/',
'Задать exact цену0, свернуть блоки занятия/группы/тарифа. Сохранить, затем нажать ссылку ошибки тарифа в сводке.',
'Нужные details раскрываются, фокус попадает в конкретное поле цены ошибочного тарифа.',
'422 и ввод0 сохранены. После перехода activeElement — SELECT с data-offering-key=program_id; price не сфокусирован.',
'functional4.result.txt; screenshots/hidden-price-error-390.png',
'static/js/owner_place_continuous.js:161 fieldTarget; src/catalog/services/pricing_plans.py:normalize_pricing_plans',
'Подтверждённое несоответствие: fieldTarget ожидает activities[i].groups[j].pricing_plans[k].price и .price, а ошибка сервера имеет «Тариф1: поле price: …». Срабатывает fallback первого control.',
'На длинной форме ошибка внутри закрытых блоков остаётся труднодоступной; P2.',
'Структурированная адресация ошибок backend→owner form, сохранение localized текста, focus/details.',
'Согласуй машинный путь ошибки и UI-target без парсинга переведённого текста. При нескольких занятиях/группах/тарифах раскрой и сфокусируй конкретный erroneous input. Проверь Tab/Shift+Tab, mobile, hidden blocks, price/age/billing ошибки и сохранность ввода. Не меняй существующие assertions для зелёного результата.'),
('04','P2','Кнопки расписания выходят за границы формы при1024px','owner','/ru/account/places/5/edit/; режим часов regular',
'Открыть заполненные часы работы в RU или AZ, viewport1024×950, с обычными буднями и несколькими интервалами понедельника. Прокрутить к расписанию.',
'«+ Интервал» и «Копировать» доступны целиком в пределах формы.',
'Ряд заканчивается x941, copy-area доx1084.83, кнопка доx1084.83 при viewport1024. В screenshot «+ Интервал» обрезана, «Копировать» скрыта справа.8 visual rows матрицы FAIL. EN1024 в прежней матрице имел иной восстановленный режим, поэтому тот case не доказывает исправность regular EN.',
'matrix.result.txt; diagnostics.result.txt; screenshots/owner-diagnostic-ru-1024.png; screenshots/owner-schedule-copy-crop-1024.png',
'static/css/components/kidsmap_schedule_editor.css:302; static/css/pages/permanent_place_wizard.css:5',
'Подтверждена геометрия и rendered clipping. Гипотеза CSS причины: четыре grid-колонки с минимальными ширинами плюс owner sidebar и nowrap copy-area превышают доступную ширину. Точный минимальный CSS patch не реализовывался.',
'Часть управления часами недоступна в обычном размере окна; P2.',
'Owner schedule responsive CSS с учётом actual content width; shared component/admin consumers.',
'Исправь responsive композицию schedule controls в continuous owner form при1024 и соседних размерах. Проверь regular, несколько интервалов, длинные AZ/RU labels, open copy popup, keyboard, sticky sidebar и widths360/390/768/1024/1280/1440. Не меняй schedule/business rules.'),
('05','P3','Мобильный статус группы требует горизонтального скролла внутри вкладки','admin-editor','/admin/catalog/offeringgroup/2/change/',
'Зайти staff с platform review permission и явным place.edit grant. Открыть вкладку «Состояние» группы при390px в RU/EN.',
'Полный статус публикации читается сразу и переносится внутри панели.',
'Badge шириной246.5px доx363.5 внутри tab-pane доx322 и шириной254px. Таб имеет overflow-x:auto и scrollWidth296. Конец статуса обрезан в начальном положении. Горизонтальная прокрутка теоретически доступна; недоступность навсегда не утверждается.',
'badge-diagnostic.result.txt; clipping.result.txt; screenshots/admin-group-badge-crop-390.png; screenshots/admin-group-en-badge-crop-390.png',
'static/admin/css/kidsmap_admin_components.css:252; src/catalog/domain_admin/business.py:118 publication_badge',
'Подтверждённая причина: nowrap badge шире ограниченной мобильной панели; scrollable tab обрезает начальное отображение. Общий document.scrollWidth при этом нормальный.',
'Полировка читаемости рабочего статуса, сохранение/права не блокируются; P3.',
'Admin status badges/BusinessEditor responsive layout; остальные entity forms.',
'Обеспечь чтение полного статуса без внутренней горизонтальной прокрутки. Сохрани статусную семантику, focus и размер контролов. Проверь Program/Activity/Group, длинные RU/AZ/EN подписи и все6 ширин, включая open tabs. Учитывай что root overflow detector не ловит этот случай.'),
('06','P3','AZ/EN административные статусы частично остаются русскими','admin-editor; LOCAL locale environment','/admin/catalog/program/1/change/; activity/2; offeringgroup/2',
'В административном language switch выбрать English или Azərbaycan. Открыть статус группы и владения.',
'Системные статусы отображаются на выбранном языке; fallback пользовательского текста отделён от перевода UI.',
'html.lang=en, но «Публикация занятия: Published», «Владелец назначен», «Условия не подтверждены». AZ аналогично. Owner add_group/add_plan и ошибки цены в свежей проверке переведены корректно; прежняя гипотеза о всех owner CTA отвергнута.',
'i18n-evidence.json; diagnostics.result.txt; screenshots/admin-group-en-badge-crop-390.png; screenshots/admin-editor-offeringgroup-tab0-az-390.png',
'src/catalog/domain_admin/business.py:118–150; locale/en/LC_MESSAGES/django.po; locale/az/LC_MESSAGES/django.po; existing .mo runtime',
'Смешанная причина подтверждена чтением gettext: перевод «Владелец назначен» есть в .po, отсутствует в .mo; для «Публикация занятия: %(status)s» и «Условия не подтверждены» нет .po записей. .mo не пересобирались в аудите.',
'Неполная локализация рабочих статусов; P3, не auth/данные. Часть ENVIRONMENT, часть source catalog gap.',
'Translations/build packaging; definitions BusinessEditor; зависит от согласованного набора переводов и выпуска compiled catalogs.',
'Отдели недостающие msgid/msgstr от устаревших .mo. Подготовь AZ/EN status translations и воспроизводимую сборку locale artifacts, затем повтори fresh browser проверку фактически поставляемых файлов. Не называй recompilation приложения исправлением безопасности и не меняй бизнес-статусы.'),
('07','P2','Обычный адрес редактора молча восстанавливает устаревшую рабочую копию','owner','/ru/account/places/6/edit/; /ru/api/drafts/',
'На чистой синтетической карточке в отдельной сессии создать unsaved Activity A и дождаться server autosave. В другой fresh сессии создать валидные Activity/Group B, явно сохранить, отправить и одобрить. В новой сессии открыть обычный /edit/ без fresh=1, сравнить с новым fresh=1 редактором.',
'Устаревшая server working copy не подменяет актуальную карточку без предупреждения о версии и явного решения пользователя.',
'Обычный URL восстановил OLD unsaved activity A с пустыми group/price и без актуальных ID. Fresh URL показывает approved B Activity4/Group5/35 AZN. UI сообщает «Текст и тарифы сохранены на сервере». Source version формы3, выбранной draft1; conflict отсутствует. Обычный reload fresh=1 ранее прошёл — разные пути не смешаны.',
'restore.result.txt; restore-read.result.txt; state-final.json; screenshots/normal-edit-old-copy-after-publish-390.png; screenshots/fresh-edit-approved-copy-after-publish-390.png',
'static/js/owner_place_continuous.js:73 restore; src/catalog/services/server_drafts.py:198 mark_explicit_save',
'Подтверждённая причина: server restore выбирает не materialized рабочую копию и применяет fields без сравнения detail.source_version с form sourceVersion. Explicit save помечает только текущую копию, старые остаются resumable. Local-cache version check есть, но не выполняет эту проверку для fetched server copy.',
'Владелец редактирует устаревшее дерево вместо сохранённого; риск повторного создания/перезаписи при последующей валидной отправке. Сам факт production потери данных NOT RUN; P2.',
'ServerDraft lifecycle/version checks, owner restoration UX, candidate/live и multiple sessions. Не очищать все черновики вслепую.',
'Устрани молчаливое применение устаревшей server copy: версия карточки/кандидата, явный выбор восстановления, scope actor+target, завершение старых copies при explicit save с сохранением нужного ввода. Проверь два разных browser contexts, обычный /edit/, fresh=1, logout/login, reload после draft/save/approval, server/local conflicts и отсутствие потери новых B данных.'),
('08','P2','Причина окончательного отказа программы не видна владельцу','moderator → owner','/admin/volunteer/moderation/content/1/ → /ru/account/organizations/1/programs/1/',
'Владелец отправляет изменение описания программы. Moderator выбирает «Отклонить» с причиной. Владелец открывает/перезагружает программу. Отдельно пройти исправление, повторную отправку и одобрение.',
'Владелец видит сохранённую причину решения и предложенный текст для осознанного исправления.',
'DB revision1 status=declined, review_note «Uydurma OFFER08 reason: clarify program text». Owner видит только чип «Отклонено», причина отсутствует; input description показывает прежнее approved «Uydurma corrected after review», а не предложенный текст. Correction/resubmit/reapproval в предыдущем native цикле прошли.',
'rejection.result.txt; rejection-repro.result.txt; state-final.json; screenshots/program-declined-reason-missing-390.png',
'src/catalog/templates/pages/program_editor.html:9; src/catalog/controllers/program_workspace.py:52 _context; src/catalog/services/publication.py:408; services/volunteer_proposals.py:37',
'Подтверждённая причина: final_reject сохраняет status=declined, template показывает review_note только для rejected; _context overlay payload тоже ограничен draft/pending/rejected.',
'Нельзя понять отказ и продолжить исходное предложение по причине решения; P2, live публикация при этом сохраняется.',
'Program owner candidate lifecycle/status rendering/forms; moderation decision contract. Зависимости: различие return/rejected и final reject/declined.',
'Согласуй отображение declined/rejected с canonical review semantics: причина, текущие и предложенные тексты, доступное дальнейшее действие. Не переименовывай бизнес-статусы только ради UI. Проверь approve/return/final reject, owner reload, correction/resubmit, AZ/RU/EN, mobile/PC и неизменность live до одобрения.'),
]
links=[]
for num,sev,title,role,url,steps,expected,actual,ev,source,cause,impact,scope,fix in findings:
 ident='OFFER-QA-'+num;filename=ident+'.md';links.append(f'| [{ident}](findings/{filename}) | {sev} | {title} |')
 evidence='\n'.join('- ['+x.split('/')[-1]+'](../'+x+')' for x in ev.split('; ') if (P/x).exists())
 missing=[x for x in ev.split('; ') if not (P/x).exists()]
 text=f'''# {ident} — {title}

OPEN · {sev} · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: {role}. Endpoint/URL: `{url}`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: {steps}

Ожидание: {expected}

Факт: {actual}

Причина / confidence: {cause} Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: {impact}

Область и зависимости: {scope} Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

{evidence}

Source references: {source}. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: {ident}, {title}. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/{filename}. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области {scope} Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
{fix}
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
'''
 (P/'findings'/filename).write_text(text,encoding='utf-8')
 if missing:print(ident,'missing optional evidence filename',missing)
(P/'FINDINGS.md').write_text('# Подтверждённые проблемы модуля05\n\nAUDIT ONLY. 8 OPEN: 6 P2, 2 P3.06 содержит environment + missing source translations; остальные — поведение приложения/визуал текущего LOCAL WORKTREE. Production/сравнение прошлых SHA NOT RUN.\n\n| ID | Приоритет | Проблема |\n|---|---|---|\n'+'\n'.join(links)+'\n',encoding='utf-8')
modules=[line[3:] for line in (P.parent/'module-acceptance-prompts.md').read_text(encoding='utf-8').splitlines() if re.match(r'^## \d\d\.',line)]
(P/'PROMPTS-INDEX.md').write_text('# Все13 промптов приёмки\n\nПолные копируемые задания: [module-acceptance-prompts.md](../module-acceptance-prompts.md).\n\n'+'\n'.join('- '+m for m in modules)+'\n\nМодуль13 выполняется после остальных. В этом запуске выполнен только05.\n',encoding='utf-8')
full=(P.parent/'module-acceptance-prompts.md').read_text(encoding='utf-8');start=full.index('## 06.');block=full[start:full.index('## 07.',start)];prompt=re.search(r'```text\n(.*?)\n```',block,re.S).group(1)
(P/'next-chat.txt').write_text('Продолжаем KidsMap на другом ПК. За этот запуск только модуль06 «Публичный каталог, поиск, фильтры и карта». Сначала найди фактический checkout; текущий на этом ПК C:\\kidsmap.\nПрочитай AGENTS.md, canonical .agents и docs/qa/module-acceptance-prompts.md. В журнале01–05 завершены;05 DONE—FAIL. Новый свежий аудит05: docs/qa/module05-2026-10-10-r1/REPORT.md, FINDINGS.md, verification.json. Историю использовать только как checklist. Не исправляй08 OPEN OFFER findings в ходе06. Модуль13 последним.\nОпредели новый HEAD/branch/dirty WORKTREE/active_run и создай новый собственный стенд; не используй PID/DB/cache/media/session/ports предыдущего ПК как доступные. Не останавливай чужие стенды и не перезаписывай чужой active_run. Режим AUDIT ONLY, без app/rules/migration/assertion fixes, commit/push/deploy/production.\nПосле полного отчёта06 обнови только его строку журнала и дай следующий prompt07.\n\n'+prompt+'\n',encoding='utf-8')
print('Own8 findings and13-prompt index + complete06 handoff written.')
