"""Assemble the human report from completed, preserved audit evidence."""
import collections,json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
input_hashes={}
def read(name):
    content=(ROOT/name).read_bytes();input_hashes[name]=hashlib.sha256(content).hexdigest()
    return json.loads(content)
def suite(d):return d['suite-results.json']
def label(d):
    s=suite(d);return f"{s['tests_run']} выполнено; {s['failures']} failures, {s['errors']} errors, {s['skipped']} skipped"
def words(value):
    if isinstance(value,list):return '; '.join(words(x)for x in value)
    if isinstance(value,dict):return '; '.join(f'{k}: {words(v)}'for k,v in value.items())
    return str(value)
status_labels={'HISTORICAL_ACCEPTANCE':'Исторически принято; свежая проверка отдельно','PARTIAL':'Частично подтверждено; см. ограничения','NOT_INDIVIDUALLY_VERIFIED':'Нет отдельного доказательства для всего пункта','PARTIAL_CURRENT_LOCAL_EVIDENCE':'Есть локальные доказательства части пункта','HISTORICAL_SCOPE_NOT_CURRENT_PASS':'Историческое согласование / границы этапа','PARTIAL_CONFIRMED_PRODUCT_GAP':'Частично: подтверждён пробел продукта','PARTIAL_CRASH_WINDOW_NOT_TESTED':'Частично: окно аварии не проверено','PARTIAL_FULL_SUITE_FAILURES_AND_PRODUCT_GAP':'Частично: красная регрессия и пробел продукта'}
image_file='image-full-r2-results.json'if(ROOT/'image-full-r2-results.json').exists()else'image-full-results.json'
full=read('full-results.json');image=read(image_file);security=read('security-results.json')
stages=read('stage-map.json')['stages'];requirements=read('requirements-review.json')['requirements']
browser=read('browser-results.json');screens=read('screenshots/index.json')
recovery=read('recovery-results.json')['r2-rehearsal.json'];javascript=read('javascript-results.json')
entry=read('entry.json');perf=full['stage19-query-comparison.json']
assert len(stages)==28 and len(requirements)==306
task33=full['task33'];passed=task33['executed']-len(task33['failed_ids'])
image_task=image['task33'];image_passed=image_task['executed']-len(image_task['failed_ids'])
# Browser collector schema is deliberately explicit: no expected count replaces actual execution.
contexts=browser['contexts'];checks=browser['checks'];passed_checks=browser['passed_checks']
assert browser['status']not in {'RUNNING','IN_PROGRESS','PENDING'} and contexts>=798
gallery=screens if isinstance(screens,list)else screens.get('screenshots',screens.get('items',[]))
assert gallery
gallery_rows=[]
for item in gallery:
    path=item.get('path',item.get('file',item.get('filename')))
    assert path
    if not path.startswith('screenshots/'):path='screenshots/'+path
    assert(ROOT/path).is_file(),path
    caption=item.get('title','')+'. '+item.get('caption','')
    caption+=' · '+str(item.get('language',item.get('lang','')))+' · '+str(item.get('width',''))+'px'
    gallery_rows.append({'path':path,'caption':caption})
stage_rows=[]
for item in stages:
    stage_rows.append([f"{item['stage']:02}",item['title'],words(item.get('promise',item.get('user_value',''))),words(item['implementation']),status_labels.get(item['status'],words(item['status'])),words(item.get('dependencies',[])),words(item.get('gaps',[]))or'См. границы evidence в подробной матрице.'])
requirement_counts=collections.Counter(r['status']for r in requirements)
def requirement_group(status):
    if status.startswith('HISTORICAL'):return'Исторические согласования и границы этапов'
    if status.startswith('FAILED'):return'Есть упавшая проверка части требования'
    if 'CONFIRMED_PRODUCT_GAP'in status:return'Подтверждён функциональный пробел'
    if status.startswith(('NOT_','PENDING_','DOCUMENTED_EXTERNAL')):return'Отдельная проверка не выполнена или не установлена'
    if status.startswith('PROVED_'):return'Конкретный локальный сценарий подтверждён полностью'
    if status.startswith('WORKFLOW_'):return'Соблюдение процедуры подтверждено'
    return'Есть частичные доказательства; границы указаны отдельно'
requirement_groups=collections.Counter()
for k,v in requirement_counts.items():requirement_groups[requirement_group(k)]+=v
sections=[]
def section(title,**content):sections.append({'title':title,**content})
def table(title,headers,rows):return{'title':title,'headers':headers,'rows':rows}
section('1. Главный вывод простым языком',paragraphs=[
 '**Основная система реализована и её ключевые части связаны друг с другом. Окончательно считать всю задумку завершённой пока нельзя.** В этом аудите проверялось реальное поведение текущего приложения, а не только наличие отметок DONE.',
 'Есть организация с филиалами и сотрудниками, занятия с группами и тарифами, проверка публикаций, каталог и карта, отдельные отзывы, специалисты с личными документами, события с календарём и историей. Семья получает публичные карточки и поиск; бизнес — кабинет управления; KidsMap — модерацию и контроль доступа.',
 'Подтверждено функциональное ограничение: самостоятельному занятию нельзя задать собственную категорию через текущую форму. Оно может находиться по возрасту и исчезать при добавлении категории. У общей программы есть категория, но нет полноценного пути задания подкатегории. Следовательно, точный поиск по всем сочетаниям исходной задумки работает не для всех новых предложений.',
 f'Новый полный прогон выполнил1817 тестов. Из{task33["executed"]} тестов Task33 прошли{passed}; конкурентный сценарий передачи владения остаётся нестабильным по ожидаемому результату. Прежние580/580 относятся к предыдущему запуску и не подменяют этот результат.',
 'Технический долг тестов также значителен: полный suite остаётся NOT_GREEN. Часть старых проверок требует поведения, которое было осознанно изменено; их нельзя ни игнорировать, ни делать зелёными ослаблением важных проверок. Полноценная эксплуатация на production в этот аудит не входила и не доказана.'
],tables=[table('Ответы на основные вопросы',['Вопрос','Ответ'],[
 ['Все28 этапов рассмотрены?','Да. Составлены28 строк дорожной карты и отдельная сверка306 требований.'],
 ['Работают ли части вместе?','Основные проверенные связки работают. Ниже указаны фактические сценарии, ограничения поиска и непроверенные внешние связи.'],
 ['Есть ли реальные скриншоты?','Да. Новые снимки отрендеренного приложения на синтетических локальных данных, с языком/шириной/источником и хешем.'],
 ['Можно считать всё окончательно готовым?','Нет: остаются функциональная неполнота поиска, регрессионный долг, мелкие UI-дефекты и внешние эксплуатационные проверки.'],
 ['Можно запускать production прямо сейчас?','Этот отчёт не даёт такого заключения. Нужны отдельные действия из раздела дорожной карты запуска.']])])
section('2. Что получилось: понятная модель продукта',paragraphs=[
 'Организация — необязательная общая оболочка бизнеса. Место может существовать самостоятельно. Программа описывает общую часть занятия, а конкретное предложение, группы и условия привязаны к месту. Такое разделение позволяет менять общую программу и сохранять местные отличия.',
 'Новая правка опубликованной информации хранится отдельно до проверки. Посетитель продолжает видеть последнюю одобренную версию. Владение бизнесом, право редактирования и разрешение на публикацию — отдельные вещи.'
],tables=[table('Сущности и их смысл',['Термин','На простом языке','Главная связь'],[
 ['Organization','Организация или сеть, даже без филиалов.','Сотрудники, общие контакты и программы.'],['Place','Отдельное место или филиал.','Может быть самостоятельным; связь с сетью не передаёт владение.'],
 ['Program','Общая программа сети.','Применяется к выбранным филиалам с контролем влияния.'],['Activity / занятие','Конкретное предложение в конкретном месте.','Может основываться на программе; имеет группы и свои условия.'],
 ['Group','Группа по возрасту, уровню, языку и расписанию.','Поиск должен сопоставлять условия внутри одной реальной группы.'],['Tariff','Цена и понятные условия оплаты.','Одна группа, набор групп или общий вход в место. Несопоставимые цены не сводятся в ложный бюджетный фильтр.'],
 ['Specialist','Профиль отдельного человека.','Claim подтверждает KidsMap; организация не становится владельцем личности.'],['Event','Одно конкретное проведение события.','Один организатор, отдельная площадка, точное время Баку, отмена/перенос с историей.'],
 ['Review / revision','Отзыв и его редакции.','Публична одобренная версия; бизнес отвечает или жалуется, а не модерирует чужой отзыв.'],['Outbox','Надёжная очередь служебных сообщений.','Изменение сохраняется даже при сбое отправки письма; повтор не должен дублировать сообщение.']])],flows=[
 {'title':'Путь бизнеса к публичному каталогу','steps':['Создать место / организацию','Настроить сотрудников и программу','Добавить занятие, группы и тарифы','Отправить изменения на проверку','KidsMap одобряет актуальную версию','Семья видит карточку, поиск и карту']},
 {'title':'Путь специалиста и события','steps':['Подтвердить профиль человека','Подтвердить связи с организациями отдельно','Выбрать и проверить публичные сертификаты','Назначить организатора события','Опубликовать проведение в афише','Сохранить историю отмены или переноса']}
])
section('3. Как проводилась проверка и что означает evidence',paragraphs=[
 'Ведущая роль: kidsmap-orchestrator, исполнитель /root; каноническое определение `.agents/agents/kidsmap-orchestrator/agent.md`. Область: локальный аудит всех 28 этапов; production UNKNOWN / NOT_CONTACTED. Реализация новых функций не входила в поручение.',
 f'Дата отчёта —4 октября2026, Asia/Baku. Checkout C:/kidsmap, branch{entry["branch"]}, LOCAL HEAD `{entry["head"]}`. Проверялся dirty WORKTREE, а не один коммит. До начала сохранены{len(entry["files"])} файлов и binary patch;218 прежних source hashes совпали.',
 'Application source и существующие assertions не исправлялись. Новый код аудита — отдельные диагностические fixtures, collectors и оформление отчёта. Production не подключался. Тесты работали с DJANGO_TESTING=1, отдельными PostgreSQL/media/cache/email, запретом внешнего транспорта и проверкой принадлежности контейнеров перед очисткой.',
 'Выполнены свежие full suites в host и точном локальном image, browser-матрицы, независимые проверки безопасности, целевое воспроизведение спорных контрактов, повтор native recovery, проверка static/Compose/image и дополнительные JS-тесты. Диагностический PASS иногда означает успешное воспроизведение ограничения — это явно указано.',
 'Codebase Memory использован для архитектурной навигации. Начальный root snapshot имел index generation2026-10-03T21:35:01Z; поздняя проверка Django reviewer — generation2026-10-04T08:49:58Z. Это разные снимки индекса. Для важных services/forms наблюдались metadata_changed и coverage_unavailable, deploy исключён, часть templates разобрана неполно. Выводы сверялись по исходникам; граф не считается полным доказательством.',
 'Три специалиста работали в разных областях: Django/requirements, browser и security→release; root выполнял host full, первый image full, native recovery и сводил результаты. Исправленный повтор image full выполнил security/release reviewer. Переключение ролей одного исполнителя не делает их независимыми людьми. Предыдущее авторство backend27 и release override раскрыто в reviewer reports.'
],tables=[table('Тип доказательства',['Метка','Что она означает'],[
 ['Fresh execution','Команда или browser-сценарий выполнен заново в этом аудите; есть результат и snapshot.'],['Source verified','Прочитана фактическая реализация и её связи; это не заменяет runtime.'],['Retained same-source','Ранее выполненный тест относится к тем же байтам, но повтор не запускался; это указано отдельно.'],['Partial / gap','Часть обещания работает, часть отсутствует или не доказана.'],['Not run / external','Реальный внешний сервис, production-данные или эксплуатационный процесс здесь не проверены.']])])
section('4. Дорожная карта всех28 этапов: обещание и результат',paragraphs=[
 'Ниже — последовательность реализации и зависимости. Статусы описывают результат аудита, а не механически повторяют DONE из журнала. Этапы01–03 включают документы и принятие макетов; это предварительные условия, а не отдельные production-функции.',
 '[Подробная сверка требований](REQUIREMENTS.md) сохраняет все306 пунктов. [Domain review](domain-review.md) содержит source/test ссылки и объяснения ограничений.'
],tables=[table('Матрица28 этапов',['№','Этап','Что обещали','Что получилось','Статус аудита','Зависимости','Ограничения / остаток'],stage_rows)])
section('5. Проверка совместной работы',paragraphs=[
 'Проверялись как положительные действия, так и запреты: изменение чужого объекта, устаревшая версия, права прежнего владельца, непроверенная публикация, приватный документ и чужая площадка события. Наличие кнопки в интерфейсе не принималось за доказательство серверного права.',
 'Для новых диагностических сценариев использовались реальные services/writers там, где это возможно. Одобренные данные дополнительных browser-экранов подготовлены как синтетические fixtures: это проверка отображения и последующих действий, а не доказательство всего пути от регистрации до первой публикации.'
],tables=[table('Сквозные связи',['Связка этапов','Что проверяли','Результат и граница'],[
 ['06–07–12–13','Организация, филиал, выбранные права, будущие филиалы, отделение и передача владения.','Положительные/отрицательные контракты и browser scope проверены. Конкурентный transfer-test воспроизводимо требует уточнения ожидания при безопасном отказе.'],
 ['08–09–14–15–18','Черновик → candidate → модерация → публичная одобренная версия.','Версии и сохранность current проверяются suites и дополнительным Program edit/stale conflict сценарием.'],
 ['10–14–18–19–20','Программа/занятие → группа/тариф → поиск → карта.','Главная выявленная неполнота: standalone taxonomy и writer подкатегории. Отдельно измерены query counts и честность no-coordinates поведения.'],
 ['16–17','Модератор/волонтёр → решения → уведомления.','Права, статусы, durable outbox/retry/dedupe проверены локально. Реальная SMTP-доставка и расписание runner не доказаны.'],
 ['21–22','Язык, видимость, отзывы и редакции.','AZ/RU/EN UI, provenance/fallback и typed reviews проверены. Часть локализационной полировки остаётся.'],
 ['24–25–06–07','Claim человека → employment → права организации → документы.','Подтверждения и доступ разделены; приватные сведения не превращаются в имущество организации.'],
 ['26–27–24–22','Организатор/площадка → событие → афиша → отзыв/история.','Права организатора, online без фиктивной географии, календарь, отмены/переносы и точность времени проверены.'],
 ['11–23–28','Преобразование данных → выключение новых записей → восстановление после новых данных.','Свежая native rehearsal сохранила98 таблиц,25 публичных и2 приватных файла, новые записи/историю/outbox. Production объём не проверялся.']])])
section('6. Фактические результаты тестов',tables=[table('Все основные новые запуски',['Проверка','Результат','Evidence'],[
 ['Полный PostgreSQL suite, host Python3.12.3',label(full),'[full-results.json](full-results.json)'],
 ['Task33 внутри host full',f'{passed}/{task33["executed"]} без failed ID; остальные — в failure_review','В этом запуске ownership concurrency failed; прежние580/580 не подставлены.'],
 ['Полный PostgreSQL suite внутри точного image Python3.12.15',label(image),f'[{image_file}]({image_file}); Task33{image_passed}/{image_task["executed"]}'],
 ['Independent security selected260',label(security),'[security-results.json](security-results.json)'],
 ['Дополнительные auth/upload/redirect negatives',label(read('security-supplement.json')),'[security-supplement.json](security-supplement.json)'],
 ['Concurrency causal: original5 + forced ordering',label(read('security-causal.json')),'[security-causal.json](security-causal.json); отдельный PASS не отменяет failed260.'],
 ['Воспроизведения поиска, отображения и старых admin-контрактов',label(read('domain-results.json')),'[domain-results.json](domain-results.json); PASS означает подтверждение наблюдаемой причины, в том числе пробела поиска.'],
 ['Rendered browser',f'{browser["status"]}; {contexts} контекстов; {passed_checks}/{checks} проверок','[browser-results.json](browser-results.json), [browser-review.md](browser-review.md); функциональные assertions и ошибки браузера учтены отдельно.'],
 ['Отдельное воспроизведение ошибки перехода Program','2/2 бизнес-проверки; 2 ошибки ViewTransition при ответе 400 и перенаправлении после сохранения','[browser-motion-results.json](browser-motion-results.json); не включено повторно в 816 контекстов.'],
 ['Native recovery',f'{recovery["tables_compared_count"]} таблиц; {recovery["media_files_compared"]} public + {recovery["private_files_compared"]} private files совпали','[recovery-results.json](recovery-results.json)'],
 ['JS DOM contracts',f'{javascript["counts"]["pass"]}/{javascript["counts"]["tests"]}; {javascript["counts"]["fail"]} failure','[javascript-results.json](javascript-results.json); старый CSS-marker, отдельный causal2;1 case uses retained HTML.'],
 ['JS analytics attribution logic','PASS, отдельный Node script','Логика распознавания источника; реальная GA4-доставка NOT_RUN.'],
 ['Image / Compose / static','2794 image files MATCH; required config negatives3/3; static9305 MATCH','[security-image.json](security-image.json), [security-compose.json](security-compose.json), [security-static.json](security-static.json)']])],paragraphs=[
 'Full-suite failures/errors — записи результата unittest; несколько subtest-проблем могут относиться к одному test ID. Поэтому проценты успешности из простого вычитания этих чисел не рассчитываются.',
 'Browser PASS означает, что прошли перечисленные автоматические проверки сценариев. Он не отменяет замечаний ручного визуального и DOM-аудита: None, перевод сообщения, обрезанный счётчик и вложенные основные области страницы перечислены отдельно.',
 'В новом host прогоне108 problem IDs сохранились относительно28; один прошлый sitemap-test прошёл утром, а ownership-race впервые упал в полном наборе этого запуска. Это согласуется с зависимостью sitemap expectation от UTC/Baku границы дня и concurrency expectation от порядка потоков. Остальные метки baseline использованы как указатели для проверки причин, а не как автоматическое оправдание.',
 'Безусловный PASS всего приложения не получен. Успешное воспроизведение диагностического probe не является исправлением найденного ограничения. Application assertions не менялись.'
])
sections[-1]['paragraphs'].append('Первый image-full запуск: 1817 тестов, 125 failures и 28 errors; Task33 548/580. Его дополнительные ошибки включали несовместимое расположение тестового сокета и временных файлов. Эти результаты сохранены отдельно; для итогового повтора исправлялось только окружение QA, без добавления отсутствующих application-файлов. Причины и различия: [image-full-comparison.json](image-full-comparison.json).')
if image_file=='image-full-r2-results.json':
    sections[-1]['paragraphs'].append('Исправленный повтор в том же образе: 1817 тестов, 108 failures и 12 errors; Task33 580/580. С host совпадают 108 problem IDs без смены типа ошибки. Только в образе падает проверка наличия документа analytics-event-taxonomy.md: runtime-пакет намеренно не включает docs/product. Это несовместимость состава пакета с документным тестом, а не доказанная неисправность публичного сайта. Host-only ownership race в образе прошёл; его нестабильность остаётся незакрытой. Первоначальный единичный сбой rating calibration в повторе не появился, точная причина первого сбоя не доказана.')
failure_groups=collections.Counter()
for item in read('domain-failure-classification.json')['entries']:
    state=item['status']
    group=('Причина подтверждена отдельным воспроизведением'if state.startswith('CONFIRMED_')else
           'Причина первого отказа разобрана по исходнику; полнота сценария отдельно'if state.startswith('SOURCE_DIAGNOSED_')else
           'Причина или последующие части сценария ещё не доказаны'if state.startswith(('PARTIAL_','UNRESOLVED_'))else
           'Подтверждено увеличение числа запросов'if state.startswith('OBSERVED_')else
           'Упавший конкурентный сценарий требует закрепления допустимых исходов')
    failure_groups[group]+=1
sections[-1]['tables'].append(table('Разбор 120 записей проблем host full',['Группа причин','Записей'],[[k,v]for k,v in failure_groups.items()]))
sections[-1]['paragraphs'].append('Это группировка записей ошибок, а не число независимых дефектов. Точные assertion, subtest, причина, уверенность и границы каждого случая сохранены в [domain-failure-classification.json](domain-failure-classification.json). Разбор первого отказа не доказывает успешность последующих действий того же теста.')
section('7. Сильные стороны и реальные ограничения',paragraphs=[
 'Сильная сторона системы — разделение прав и публичных данных: владелец площадки не управляет чужим событием; организация не получает личность специалиста; бизнес не модерирует чужие отзывы; неопубликованные правки не должны подменять текущую одобренную карточку.',
 'Вторая сильная сторона — сохранность данных при изменениях: история событий и документов, прошлые редакции и реакции, snapshot после отделения от сети, durable outbox и проверенное восстановление после новых записей. Это подтверждено конкретными локальными сценариями, а не предполагается по названиям моделей.'
],tables=[table('Проблемы и долг',['Приоритет','Проблема','Что видит пользователь / эффект','Следующий шаг'],[
 ['P2 · функциональность','Нет полноценного taxonomy writer для standalone Activity; Program subcategory путь отсутствует.','Часть новых занятий пропадает при сочетании категории/подкатегории с возрастом.','Согласовать модель и writer, затем проверить создание → approval → поиск/карта на одинаковом предложении.'],
 ['P2 · качество регрессии','Полный backend suite остаётся NOT_GREEN.','Нет надёжного общего сигнала, что изменение безопасно для всей системы.','Разобрать каждый failed ID; обновить obsolete fixtures/assertions по принятым контрактам и устранить реальные дефекты, сохраняя negative checks.'],
 ['P2 · concurrency test contract','Тест требует завершённого transfer даже при допустимом отказе «структура изменилась».','Пользователь может получить просьбу обновить данные; проверка то проходит, то падает.','Явно закрепить допустимые исходы и UX повторной операции, проверить отсутствие stale rights для каждого исхода.'],
 ['P3 · непроверенный аварийный сценарий','Письмо отправлено, но процесс упал до фиксации доставки в БД.','Повтор после такого сбоя потенциально отправит письмо повторно; обычный retry/dedupe не доказывает ровно одну доставку.','Проверить управляемый сбой между SMTP и commit; согласовать гарантию доставки и защиту от дублей. Внешний SMTP в аудит не входил.'],
 ['P3 · тестовая поддержка','Старый JS-тест ожидает compact CSS-marker на generic detail call link.','Телефонная ссылка/focus/cache проходят probe; старый тест всё равно красный.','Привести fixture/assertion к фактическому типу кнопки, сохранив проверку поведения.'],
 ['P3 · интерфейс','При неизвестном стаже специалиста выводится None.','Родитель видит техническое слово вместо понятного отсутствующего значения.','Показать «стаж не указан» либо не выводить строку; проверить AZ/RU/EN.'],
 ['P3 · локализация','Сообщение об успешном сохранении события на RU-странице остаётся на AZ.','Владелец сохраняет черновик, но получает ответ на другом языке.','Дополнить перевод и повторить native save на трёх языках; остальные наблюдения см. browser-findings.json.'],
 ['Gate · эксплуатация','Реальные интеграции, production data/private storage/cohort/monitoring не проверены.','Локальная корректность ещё не гарантирует безопасную работу действующего сайта.','Выполнить отдельную подготовку запуска по release-gates.json.']])])
section('8. Производительность, данные и выпуск',paragraphs=[
 f'На свежем host control comparison одна карточка: {perf["baseline_one"]["queries"]}→{perf["batch_one"]["queries"]} SQL-запросов и{perf["baseline_one"]["seconds"]}→{perf["batch_one"]["seconds"]}s. Восемь карточек: {perf["baseline_eight"]["queries"]}→{perf["batch_eight"]["queries"]} запросов и{perf["baseline_eight"]["seconds"]}→{perf["batch_eight"]["seconds"]}s. Сокращение запросов подтверждено, ускорение именно этого замера не подтвердилось.',
 'Измерения выполнялись одновременно с другими QA-процессами и не являются изолированным нагрузочным тестом. Native20/200-row comparison также сохранён в recovery-results. Производительность реального объёма данных, p95/p99 и пределы инфраструктуры остаются отдельной задачей.',
 'Точный LOCAL image `sha256:6566a67c0b3ab3da8ea040314b016908b1cbe17e09a50912fc5c80fe5228f5fd`; artifact `r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2`. Свежие проверки подтвердили2794 файлов и9305 static файлов. Полный suite теперь действительно запущен внутри этого image; его результат приведён выше.',
 'Private-media bind, явный cohort default-off и build context должны входить в эффективную конфигурацию запуска. Проверенный override не применялся к production. Native recovery использует совместимый frozen reader на host Python3.12.3; image-based native recovery под Gunicorn и реальная off-host production restore здесь не исполнялись.',
 'Удаление legacy-кода или схемы не рекомендуется на основании этого аудита. Совместимые readers, старые IDs/URLs, version history и migration markers используются для сохранности данных. Наличие старого теста или bridge не доказывает, что соответствующий путь мёртв.'
])
section('9. Дорожная карта оставшейся работы',paragraphs=[
 'Это порядок действий, а не обещание сроков. Сначала закрываются функциональные и регрессионные вопросы, затем эксплуатационные. Исправления приложения и production запуск требуют отдельного согласованного объёма.'
],tables=[table('Что делать дальше',['Очередь','Работа','Зависит от','Критерий завершения','Владелец'],[
 ['1','Уточнить taxonomy самостоятельных занятий и программ.','Продуктовое решение: где задаётся категория/подкатегория и как наследуется.','Созданное через UI предложение находится по всем согласованным фильтрам; карта/каталог согласованы; нет чужих matches.','Django + frontend + integration'],
 ['2','Закрыть красную регрессию по списку конкретных IDs.','Согласованные contracts01–28, causal evidence этого отчёта.','Полный explicit suite зелёный на host и image; старые meaningful negative проверки сохранены.','Integration + владельцы доменов'],
 ['3','Уточнить конкурентную передачу владения и повтор операции.','Допустимые исходы при одновременном join/transfer.','Детерминированные tests обоих порядков; пользователь получает понятный результат; прежние права отозваны после commit.','Django + security'],
 ['4','Исправить подтверждённые UI тексты, обрезание, разметку и переходы.','Скриншоты, browser findings и воспроизведение Program POST400/302.','AZ/RU/EN: без None, неверного языка, обрезанного счётчика, лишнего main и ошибок перехода; расширить дополнительные Program/Activity/Organization проверки с двух ширин до семи.','Frontend + browser QA'],
 ['5','Подготовить эксплуатационные условия.','Точный image/config, ownership/private-media/cohort.','Сверены настоящие data/schema/media, доставка SMTP/runner, OAuth/Maps, TLS и monitoring; фактические limits определены.','Release + security + database'],
 ['6','Провести rehearsal на согласованном staging/копии production.','Предыдущие пункты и безопасный набор данных.','Полный набор проверок + migration/reconciliation + off-host restore после новых записей + stop criteria.','Integration + release + database'],
 ['7','Отдельно разрешённый ограниченный запуск.','Решение владельца и подтверждённые release gates.','Явный cohort, наблюдение метрик/ошибок, возможность остановить новые writes без потери истории.','Владелец продукта + release']])])
section('10. Реальные скриншоты',paragraphs=[
 'Это снимки нового browser-прогона приложения на локальных синтетических fixtures. Макеты этапов02/03 не выданы за работающие экраны. Галерея показывает верхнюю часть длинного снимка; нажмите её, чтобы открыть полный оригинал. Подробные context/URL/locale/width/source hashes находятся в [индексе](screenshots/index.json).',
 'Скриншот доказывает внешний вид конкретного состояния. Серверные права и сохранность данных подтверждаются отдельными POST/negative/DB проверками; невидимая кнопка сама по себе не доказывает запрет.'
],gallery=gallery_rows)
section('11. Пробелы проверки и границы окончательного вывода',lists=[[
 'Production revision, реальные данные и конфигурация, полноценная проверка миграции/доступности и recovery в целевой среде — не проверены.',
 'Реальные OAuth/Maps/SMTP/GA4, внешние CDN и фактическое расписание outbox runner — не заменяются local stubs.',
 'Физические iOS/Android устройства, Safari/Firefox, полный screen-reader audit, реальные звонки/WhatsApp и production нагрузка — не выполнены.',
 '306 строк requirements-map имеют разную силу доказательств: source, existing/fresh tests, accepted prerequisites, partial/external. Ни один общий зелёный module-run не является автоматическим подтверждением каждой фразы.',
 'Полный image-suite проверяет код в точном runtime с disposable PostgreSQL; это не запуск всего production compose stack, не реальный TLS и не registry publication.',
 'Ряд старых тестов привязан к прошлой структуре формы, новым optional fields или прежним правилам. Индивидуальная причинная сверка и её пределы описаны reviewers; blanket «все failures безвредны» не заявлено.'
]],tables=[table('Сводка всех требований: укрупнённые группы',['Сила подтверждения','Количество'],[[k,v]for k,v in sorted(requirement_groups.items())])])
section('12. Доказательства, воспроизведение и рекомендации',paragraphs=[
 '[Domain review](domain-review.md) · [Security/release review](security-review.md) · [Browser review](browser-review.md) · [Требования306](REQUIREMENTS.md) · [Дорожная карта запуска](release-gates.json) · [План](PLAN.md) · [Входной snapshot](entry.json) · [Сохранность исходников](final-verification.json) · [Сверка host/image](image-full-comparison.json).',
 'Root full: `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa26/backend_run.sh all final-audit-full-20261004`. Image full: `wsl -d Ubuntu-24.04 -u root --exec /root/km28-db/.venv/bin/python /mnt/c/kidsmap/docs/task33/final-audit/qa/image_full_run.py --mode all --output /tmp/task33-final-audit-image-full-20261004`.',
 'Исправленный image QA-повтор: `wsl -d Ubuntu-24.04 -u root --exec /root/km28-db/.venv/bin/python /mnt/c/kidsmap/docs/task33/final-audit/qa/security_image_full_r2.py --mode all --output /tmp/task33-final-audit-image-r2-20261004`. Это тот же образ и те же application assertions; отличаются только допустимые временные каталоги и монтирование принадлежащего тесту сокета.',
 'Имена run/output уникальны: для повторения нужно новое имя, а не перезапись сохранённых результатов. Full/native/browser raw traces находятся вне Git в `/root/task33-evidence/`; safe JSON, ссылки и выбранные synthetic screenshots находятся в этом каталоге.',
 'Все первоначальные неудачные QA-attempts сохранены: browser wrapper post-run failure, diagnostic adapter errors, original JS assertion failure. Основные 798 browser contexts получены в чистых запусках. Дополнительный Program-набор содержит ошибку ViewTransition при прошедших бизнес-проверках; она учитывается в строгом итоговом статусе. Результаты не собраны путём удаления failed assertions.',
 '**Рекомендация владельцу:** принять результат аудита как подтверждение работающей основной системы и конкретного оставшегося объёма. Сначала закрыть поиск и регрессионные gates, затем подтвердить эксплуатационную готовность. Говорить «вся задумка окончательно реализована и готова к боевому запуску» сейчас преждевременно.'
])
browser_findings=read('browser-findings.json')
browser_items=browser_findings if isinstance(browser_findings,list)else browser_findings.get('findings',[])
sections[6]['tables'].append(table('Подтверждённые наблюдения браузерного аудита',['ID / приоритет','Что наблюдалось','Источник / доказательство','Ответственный'],[[f"{x['id']} / {x['severity']}",x.get('user_explanation',x.get('title','')),words(x.get('source',[]))+'; '+words(x.get('evidence',[])),x.get('owner','frontend + browser QA')]for x in browser_items]))
sections[10]['paragraphs']=['Статус «частично подтверждено» не означает, что весь этап отсутствует. Он означает, что доказательства покрывают конкретные сценарии, а весь составной пункт нельзя честно назвать проверенным. Остаток раскрыт в каждой строке приложения. Процент «готовности продукта» не вычисляется из числа тестов: требования различаются по объёму, а один тест может проверять несколько связей.']
data={'title':'Что получилось в KidsMap: проверка всех28 этапов','subtitle':'Подробный аудит реализации, связей между функциями, тестов и готовности к дальнейшему запуску. Итог: основа работает, остаются подтверждённые ограничения и отдельный объём завершения.','snapshot':f'4 октября2026 · LOCAL WORKTREE · HEAD {entry["head"][:12]} · branch {entry["branch"]} · production NOT_CONTACTED','sections':sections}
def polish(value):
    if isinstance(value,str):
        return re.sub(r'(?<=[А-Яа-яЁё])(?=\d)|(?<=\d)(?=[А-Яа-яЁё])',' ',value)
    if isinstance(value,list):return[polish(x)for x in value]
    if isinstance(value,dict):return{k:polish(v)for k,v in value.items()}
    return value
data=polish(data)
(ROOT/'report-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(ROOT/'report-inputs.json').write_text(json.dumps(input_hashes,indent=2)+'\n',encoding='utf8')
print(json.dumps({'sections':len(sections),'stages':len(stages),'requirements':len(requirements),'screenshots':len(gallery_rows),'host_task33_pass':passed,'image_task33_pass':image_passed}))
