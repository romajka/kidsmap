import json,hashlib,shutil,re
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module12-repair-2026-10-18-pc-r1';Q=R/'.tmp/m12-full-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backend=read(O/'evidence/final-backend.json');assert backend['exit']==0 and not backend['failures'] and not backend['errors'] and len(backend['test_ids'])==len(set(backend['test_ids']))==586 and backend['fresh_own_test_db']=='test_m12full_r2'
current=read(Q/'expected-source.json')['sources'];assert current==read(O/'evidence/final-backend-source.json')['sources']==read(O/'source-current.json')['sources'];assert all(sha(R/p)==h for p,h in current.items())
names=['browser-report-disabled-r2','browser-report-filled-r1','browser-report-empty-r1','browser-report-error-r1','browser-report-partial-r1','browser-controls-final','browser-counters','browser-phone-isolated','browser-outbound-isolated','browser-read-fault','browser-beacon-fallback','browser-storage-failure','browser-storage-disabled','browser-retry','browser-lifecycle','browser-recovery'];native=[]
for name in names:
 data=read(O/'evidence'/(name+'.json'));values=[v for row in data['rows'] for v in row['checks'].values()];assert values and all(v is True for v in values) and not data.get('errors') and not data.get('pageerrors'),name;native.append({'artifact':'evidence/'+name+'.json','rows':len(data['rows']),'checks':len(values),'PASS':len(values),'FAIL':0})
rows=sum(s['rows'] for s in native);checks=sum(s['checks'] for s in native);assert (rows,checks)==(447,2322),(rows,checks)
js=read(O/'evidence/javascript.json');assert all(x['exit']==0 for x in js) and all(x['PASS'] for x in js[0]['result']['results']);phone=(Q/'phone-dom-node24.log').read_text();assert re.search(r'ℹ tests 4',phone) and re.search(r'ℹ pass 4',phone) and re.search(r'ℹ fail 0',phone);js[2]['summary']=['tests4','pass4','fail0','skipped0'];(O/'evidence/javascript.json').write_text(json.dumps(js,indent=2))
check=read(Q/'checks-result.json');assert check['exit']==0;shutil.copyfile(Q/'checks-result.json',O/'evidence/django-checks.json');preserve=read(O/'evidence/preservation.json');assert preserve['sources_checked']==1066 and preserve['changed_or_added']==24 and preserve['prior_packages']==43 and preserve['prior_files']==9517 and preserve['all_original_test_sources_unchanged'] and preserve['documented_86400s_expirations']==4
items={
'01':('P2','Доступ к административной статистике','SiteAnalyticsAdmin проверяет view/change permission до построения отчёта. Superuser и законные читатели сохраняют доступ.','ingress'),
'02':('P2','События приватных карточек','Репозиторий требует published/active/nondeleted, как state-контракт Place.is_public. Каталожная quality-видимость остаётся отдельным контрактом.','ingress'),
'03':('P2','Допустимый Origin с портом','Сохраняется полная authority запроса и явно доверенных origins. Чужие host/port и HTTPS downgrade отклоняются.','ingress'),
'04':('P2','Правильные KPI за 90 дней','Отдельный quarter использует89daysAgo→today;7/30/365 сохранены. График и таблицы по-прежнему явно подписаны как30-дневные.','reporting'),
'05':('P2','Честные состояния GA4','Disabled/error/partial/missing-window дают недоступность и прочерк; успешный пустой ответ даёт0. Время обновления только после успешной загрузки, безопасный статус и клавиатурный retry.','reporting'),
'06':('P3','Азербайджанское сравнение с прошлым периодом','Оба сравнения owner UI имеют AZ-ветку; реальная дельта100% проверена по сохранённым событиям.','reporting'),
'07':('P2','Изоляция отказов записи аналитики','Optional writes имеют отдельный atomic/savepoint; DatabaseError перехватывается снаружи с безопасным предупреждением. Публичные карточки и бизнес-действия продолжают работать; ошибки каталога/ACL/программирования не скрываются.','ingress'),
'08':('P3','Локализация административной аналитики','Исправлены14 конкретных ошибочных AZ сообщений,15-е уже было корректно. Сохранены остальные PO-правки; новые статусы переведены AZ/RU/EN, MO собраны отдельно.','reporting'),
'09':('P2','API при отказе записи — дополнительный случай07','API возвращает503 analytics_unavailable без фиктивной записи вместо500/неверной классификации. Общая первопричина и helper учитываются вместе с07.','ingress'),
'10':('P2','Отказ служебного ingress-счётчика — дополнительный случай07','Ошибка вспомогательного счётчика не ломает уже сохранённое событие. Общая граница persistence учитывается вместе с07.','ingress'),
'11':('P2','Контраст и компоновка статистики','Устранены низкий контраст, обрезка KPI label/icon и неверная высота нового уведомления. Использован существующий компактный компонент;3колонки по числу KPI,1колонка на узком экране.','visual'),
'12':('P2','Нечисловой и слишком длинный numeric ID','Неконвертируемый Unicode и5000-значный ID дают400 без записи вместо500. Чужие размеры/идентичности из payload не принимаются.','payload'),
'13':('P2','Некорректный необязательный Referer','Ошибка разбора optional referrer даёт пустой domain без отказа допустимого события; нормальный referrer хранится только как hostname.','payload'),
'14':('P2','Изоляция отказов чтения агрегатов','Owner получает unavailable200; независимый GA продолжает работать. Atomic/savepoint восстанавливает транзакцию после реальной SQL ошибки.','readfailure'),
'15':('P2','Резервная отправка при отказе Beacon','Если sendBeacon возвращаетfalse, выполняется существующий keepalive fetch. Принятый Beacon не дублируется; missing/throw ветки сохранены. Условие отказа в браузере явно SIMULATED.','beacon'),
}
(O/'findings').mkdir(exist_ok=True)
for number,(priority,title,description,stage) in items.items():
 merged=number in ['09','10'];status='MERGED → ANALYTICS-QA-07; CLOSED LOCAL' if merged else 'CLOSED LOCAL';(O/'findings'/('ANALYTICS-QA-'+number+'.md')).write_text('# ANALYTICS-QA-'+number+' — '+title+'\n\n'+priority+'; '+status+'; LOCAL WORKTREE, production NOT RUN.\n\n'+description+'\n\nПервопричина, точные файлы, свежий RED и принятые границы: [план](../stages/'+stage+'/IMPLEMENTATION_PLAN.md), [diff](../stages/'+stage+'/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.\n')
verification={'status':'PASS LOCAL Module12','historical_checked':8,'historical_closed':8,'additional_canonical_causes':['11','12','13','14','15'],'merged_subcases':{'09':'07','10':'07'},'checked_rows':15,'canonical_causes':13,'confirmed_OPEN':0,'backend_methods':586,'backend_unique_methods':586,'backend_exit':0,'javascript':{'sender_cases':4,'phone_dom_cases':4,'ai_referral_script_exit':0,'runtime':'Node24; Node18/jsdom environment failure retained'},'native':native,'native_rows':rows,'native_checks':checks,'native_PASS':checks,'native_FAIL':0,'source_files':1066,'changed_added':24,'prior_packages':43,'prior_files':9517,'foreign_runtime_expirations':4,'production':'NOT TOUCHED','execution':'root inline, no independent-agent claim'};(O/'verification.json').write_text(json.dumps(verification,indent=2));(O/'progress.json').write_text(json.dumps({'phase':'COMPLETE LOCAL','confirmed_OPEN':0,'historical_closed':list(items)[:8],'additional_closed':['11','12','13','14','15'],'merged_subcases':['09','10'],'backend_methods':586,'native_checks':checks,'production':'NOT TOUCHED'},indent=2))
table='\n'.join('| [ANALYTICS-QA-'+n+'](findings/ANALYTICS-QA-'+n+'.md) | '+item[1]+' | '+('Случай07 закрыт' if n in ['09','10'] else 'Закрыт локально')+' |' for n,item in items.items())
report=f'''# Модуль 12 — завершён локально

Проверены и закрыты все **8 исходных пунктов**. Дополнительно исправлены **5 самостоятельных связанных причин**; ещё2случая отказа записи объединены с07. Всего15проверенных пунктов /13причин, подтверждённых открытых проблем в проверенном объёме: **0**.

Итоговая регрессия: **586 уникальных backend-методов, без ошибок и падений**. Принятые браузерные наборы: **{rows} строк / {checks} проверок**, все прошли; это не число уникальных пользовательских сценариев. Node24:4проверки отправителя и4phone DOM, отдельный AI-referral script PASS. Django check и makemigrations --check --dry-run прошли.

## 1. Состояние области

Основной агент выполнял роли analytics-reviewer/django/UI/QA последовательно; независимая проверка другим агентом не заявляется. Пользователь разрешил весь модуль и связанные новые исправления. Production не проверялся и не изменялся.

HEAD `852938d96764ae315b92859e3651e5ea62054a36`, ветка `codex/module09-transfer-2026-10-16-r1`; результат находится в грязном рабочем дереве. Начальный снимок1058файлов, текущий1066;24изменённых/добавленных файла, исходные тесты сохранены. Codebase Memory C-kidsmap:51523узла/280457связей, индекс2026-10-16, metadata_changed/coverage_unavailable. Критичные связи и динамические Django пути проверены непосредственно по source.

Собственные app `m12full-r1-app`, порт33780, loopback PostgreSQL `m12-full-r1-pg`; основной fixture DB `m12full_r1`, итоговая свежая test DB `test_m12full_r2`. Окружение очищено, DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email и текущие изолированные AZ/RU/EN MO. Внешние интеграции отключены; GA snapshots и ошибки явно SIMULATED. Синтетические retention90/collection-start2026-08-20 заданы только в QA-профиле; реальные env/credentials не использовались.

## 2. Что подтверждено

View — успешный серверный GET карточки; повторы добавляют просмотры. Идентичность привязана к сущности/пользователю/сессии, адрес не является ключом агрегации. Один пользователь в двух сессиях остаётся одним посетителем; bot/staff/активные исключения фильтруются, owner учитывается. HEAD не создаёт просмотров. Действующие v1/v2 и contact/directions правила сохранены; локальные агрегаты не подменяют GA.

Проверены равные предыдущие окна и полуоткрытые границы времени в Baku; реальные contact aliases, приватность и отсутствие доверия к client dimensions. Через UI выполнены редактирование→кандидат→одобрение, старые URL/redirect, телефон/WhatsApp/website/social/directions, избранное, длинные имена, снятие с публикации→отказ ingress→повторная публикация. Названия/контакты восстановлены через UI с обычной нормализацией пробелов, адреса/медиа сохранены; история и audit timestamps закономерно выросли.

## 3. Проверенные проблемы

| ID | Результат | Статус |
|---|---|---|
{table}

09/10 не считаются отдельными первопричинами поверх07. Неправильная высота уведомления была замечена после первого исправления состояний и устранена до приёмки; исходный неудачный вариант сохранён.

## 4. Технические границы

Не менялись поля/схема моделей, роли, история и методика метрик. Новое persistence/read isolation перехватывает только DatabaseError в собственной транзакционной границе. Ошибки основного каталога/ACL и программирования не скрываются. Успешный пустой GA ответ остаётся0; недоступный/частичный ответ не выдаётся за нулевую аудиторию. Числа за90дней не подменяются годом; графики/таблицы явно остаются30-дневными.

SiteVisit по-прежнему не подключён к основному публичному пути; его сервисные тесты не объявляются доказательством новых пользовательских просмотров. У Organization/Activity есть сырые subject views, но эквивалентный owner-report не добавлялся. Новые Event/Specialist analytics surfaces не выдумывались.

## 5. Риски и ограничения

Реальные GA ingestion/Realtime/property timezone/consent/квоты/latency NOT RUN. Отправитель Beacon проверен по [первичному контракту W3C](https://www.w3.org/TR/beacon/#sendbeacon-method): true означает принятие в очередь, а не подтверждение доставки. Реальный overflow не вызывался; false-return явно симулировался, последующий локальный POST/delta проверен. Синхронная внешняя задержка GA не измерялась.

Chromium с эмуляцией desktop/mobile UA и viewport; физические устройства, Safari/Firefox, физический звонок и внешние переходы не проверялись. В headless после неподдержанного tel последующая операция иногда не доставляла DOM click: диагностика и неудачные монолитные попытки сохранены. Канонические outbound-сценарии выполнены в независимых свежих контекстах, каждый с подтверждённым локальным событием. Неудачная последовательность не использована для вывода об ошибке обработчика аналитики; поведение физического dialer не подтверждено.

## 6. Сохранность и legacy

Проверены43предыдущих пакета /9517файлов, прежние тесты, refs/index/staging, общие MO/.cbmignore/active_run NONE. Двоичный index отличался от предыдущего модуля при начальной проверке; refs/исходники/staging совпадали, причина обновления metadata не доказана. Текущий начальный index сохранён.

Четыре прежних m09 standby-контейнера естественно завершили свой `sleep(86400)` во время долгой работы: те же IDs, exit0/OOMfalse, срок≥86400s. Они не перезапускались/не останавливались этой задачей, данные/volumes не удалялись; см.[наблюдения](evidence/foreign-runtime-transitions.json). Нельзя утверждать, что все runtime states остались прежними. Production/commit/push/deploy не выполнялись. Dead-code/DB cleanup не проводился.

## 7. Проверки и доказательства

[Итоговый backend](evidence/final-backend.json), [его source snapshot](evidence/final-backend-source.json), [native summary](verification.json), [JavaScript](evidence/javascript.json), [Django checks](evidence/django-checks.json), [сохранность](evidence/preservation.json), [команды и воспроизведение](EXECUTION.md).

Первый широкий583-method PASS относится к снимку до расширения read/Beacon fault coverage и сохранён отдельно. Последний586-method PASS относится к текущим исходникам. RED/ошибки своих fixtures/наблюдателей/окружения сохранены, не переименованы в GREEN; см.[заметки](evidence/adapter-notes.md). Старые assertions не менялись. Node18/jsdom ESM mismatch устранён запуском на уже используемом Node24, без изменения тестов/зависимостей. Windows mapped-file resize остановил один patch после записи prefix; точное исходное состояние восстановлено по байтам до применения окончательного кандидата; source guard заблокировал промежуточный запуск.

Пять GA-state матриц проверяют disabled/filled/empty/error/partial,3языка/6ширин; последующие изменения read isolation/Beacon не меняли их UI. На окончательных исходниках дополнительно проверены все роли/периоды/owner layouts, отказ чтения и записи, recovery, sender fallback, native counters и lifecycle. Полные реальные внешние интеграции и межмодульная приёмка всего проекта остаются отдельными задачами.

## 8. Дальнейший шаг

Следующий по плану — этап13: сверка актуальных результатов модулей1–12, сквозные сценарии, покрытие и обнаружение тестов CI. Автоматически он не начинался. Release/production и реальное подключение GA требуют отдельной задачи.

## 9. Решение

**PASS LOCAL** для документированного и фактически проверенного объёма модуля12. Все8исходных пунктов,5новых причин и2объединённых подслучая закрыты локально. P0/P1/подтверждённых OPEN в этом объёме нет. Это не общий production PASS проекта.
'''
report=re.sub(r'(?<=[0-9])(?=[А-Яа-яЁё])|(?<=[А-Яа-яЁё])(?=[0-9])',' ',report);(O/'REPORT.md').write_text(report)
for stage in ['ingress','reporting','visual','payload','acceptance','readfailure','beacon']:
 S=O/'stages'/stage;(S/'REPORT.md').write_text('# '+stage+' — CLOSED LOCAL\n\nПлан, исходные/итоговые кандидаты и RED/GREEN сохранены. Текущая общая проверка586уникальных методов0F0E и итоговая native summary относятся к указанным границам; отдельные неудачные попытки не объявлены успешными. Для acceptance-only test addition RED не выдумывался. No production/commit/push/deploy.\n');(S/'verification.json').write_text(json.dumps({'status':'CLOSED LOCAL','backend_methods':586,'native_summary':'../../verification.json'},indent=2))
docs=read(O/'document-current.json')
for relative,h in docs.items():
 path=R/relative;assert sha(path)==h;prefix='' if relative.startswith('docs/qa/') else '../qa/';path.write_bytes(path.read_bytes()+('\n\n## Module12 repaired and accepted LOCAL — 2026-10-19 pc-r1\n\n[Отчёт]('+prefix+O.name+'/REPORT.md). Все8исходных пунктов CLOSED LOCAL;5дополнительных причин11–15 исправлены,09/10 объединены с07. Права/приватные субъекты/Origin-порты,90-day KPI, unavailable≠zero/partial/retry, AZ labels/delta, write/read isolation и Beacon false fallback проверены. Fresh586unique backend0F0E, '+str(checks)+'/'+str(checks)+'accepted native checks/'+str(rows)+'rows, Node sender4+phone DOM4+AI scriptPASS; Django checks/driftPASS. Старые тесты и43sealed prior packages/9517files/refs/index/sharedMO/activeNONE сохранены.4старых m09standby естественно завершили86400sPID1, identities/data сохранены, no task restart/cleanup; отчёт не заявляет unchanged runtime states. Historical583PASS/failed harness/environment attempts retained; exact current-source final evidence. No commit/push/deploy/production/realGA. Следующий отдельный этап13, не начат автоматически.\n').encode());docs[relative]=sha(path)
(O/'document-current.json').write_text(json.dumps(docs,indent=2));p=O/'PLAN.md';p.write_text(p.read_text().replace('- [ ]','- [x]')+'\nВыполнены также отдельные планы readfailure и beacon. Отмеченные пункты относятся к локальному документированному объёму; ограничения внешних интеграций/physical dialer/других браузеров сохранены в REPORT.\n')
for p in (R/'.tmp').glob('m12-*.py'):shutil.copyfile(p,O/'execution-scripts'/p.name)
for name in ['runtime.py','runtime_full2.py','qa_settings.py','qa_full2_settings.py','qa_urls.py','qa_simulation.py','stage_apply.py','apply-native.ps1','seed.py','seed-extra.py','proxy.py','checks.py']:
 shutil.copyfile(Q/name,O/'execution-scripts'/name)
for name in ['m12-recover-mapped-base.ps1']:shutil.copyfile(R/'.tmp'/name,O/'execution-scripts'/name)
print(json.dumps({'status':'PASS LOCAL','backend_methods':586,'native_rows':rows,'native_checks':checks,'historical_closed':8,'additional_canonical_closed':5,'merged_subcases':2,'OPEN':0}))
