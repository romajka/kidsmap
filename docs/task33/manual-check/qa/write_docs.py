import ast,json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
html=(root/'guide.html').read_text(encoding='utf-8')
steps=ast.literal_eval(re.search(r'const steps=(\[.*?\]);\nlet fixture',html,re.S).group(1))
fixture=json.loads((root/'fixtures.json').read_text(encoding='utf-8'))
groups=re.search(r'const groups=(.*?);\nconst steps=',html,re.S).group(1)
names=dict(re.findall(r"(\w+):'([^']+)'",groups))
smoke=json.loads((root/'browser-results.json').read_text(encoding='utf-8-sig'))
guide=json.loads((root/'guide-results.json').read_text(encoding='utf-8-sig'))
lines=['# KidsMap — локальная ручная проверка','',
'Откройте [инструкцию с кнопками входа и скриншотами](http://localhost:8780/qa/). Стенд запущен 4 октября 2026 года на отдельной синтетической PostgreSQL-базе.',
'','## Что проверено при запуске','',
f'- {len(smoke["checks"])} проверок страниц и прав: {smoke["status"]}; неожиданных ошибок JS — {len(smoke["errors"])}, неудачных сетевых запросов — {len(smoke["failed"])}.',
'- Публичные страницы проверены на AZ/RU/EN; основные кабинеты — по соответствующим ролям.',
'- Сняты 8 основных скриншотов, дополнительно — карта в режиме без ключа и два вида инструкции.',
'- Инструкция: 26 сценариев, 45 основных ссылок на каждом языке; отметки сохраняются после перезагрузки, переключение языка работает.',
'- Инструкция проверена на ширинах 320/390/768/1024/1440 без горизонтального переполнения.',
'- Это проверка готовности локального стенда, а не новый полный прогон регрессии. Автоматическая регрессия завершения хранится отдельно в ../completion/.',
'','## Ограничения','',
'Интерактивная Google-карта, геокодирование, Google-вход и реальная доставка почты отключены. Панель карты показывает **3 точки** и сообщение «Интерактивная карта станет доступна после настройки Google Maps». Счётчики и серверные данные доступны; клики по настоящим Google-маркерам этим запуском не проверены.',
'','В верхнем промоблоке каталога остаётся штатный статический текст «65+ мест / 17 категорий». Фактическая исходная выдача стенда — 3 места, смотрите строку «Найдено». Данные карточек вымышленные; общие контакты сайта в подвале могут быть штатными. Не звоните и не отправляйте реальные документы.',
'','## Вход','',
'В панели /qa/ выберите роль. Вход действует на все вкладки этого браузера с тем же адресом. Для проверки гостем одновременно с владельцем используйте инкогнито. Не смешивайте localhost и 127.0.0.1 — это разные браузерные сессии.',
'','Общий локальный пароль: `KidsMap-local-2026`.','',
'| Роль | Логин |','|---|---|']
for role,row in fixture['roles'].items():lines.append(f'| {role} | `{row["username"]}` |')
lines+=['','## Все основные ссылки','', '| Страница | RU | AZ | EN |','|---|---|---|---|']
for key,name in names.items():
    if key in fixture['links']['ru']:lines.append('| '+name+' | '+' | '.join('[Открыть](http://localhost:8780'+fixture['links'][lang][key]+')' for lang in ('ru','az','en'))+' |')
lines+=['','[Админка](http://localhost:8780/admin/) · [Отчёт завершения](http://localhost:8780/qa/files/report/report.html)','', '## Последовательность ручной проверки','',
'Сначала смотрите исходные карточки, затем редактируйте. Отделение филиала выполняйте последним: оно меняет связи и права. Передача владения и аварийные сценарии подтверждаются отдельными автоматическими проверками в completion/; этот ручной маршрут их не воспроизводит. Ожидаемые результаты ниже — задания для вашей приёмки, а не отметки о том, что все эти действия уже выполнены на этом наборе данных.','']
for i,(role,title,keys,actions,expected) in enumerate(steps,1):
    lines += [f'### {i}. {title}', '',f'Роль: **{role}**.','', ' · '.join('['+names.get(k,k)+'](http://localhost:8780'+fixture['links']['ru'][k]+')' for k in keys),'',actions,'','**Ожидаемый результат:** '+expected,'']
lines+=['## Скриншоты','']
for name in ('catalog-desktop','catalog-mobile','organization','program-editor','activity','specialist','events','event-editor','map','guide-desktop','guide-mobile'):lines+=['['+name+'](screenshots/'+name+'.png)','']
lines+=['## Повторный запуск и остановка','', 'Из PowerShell:','', '```powershell','wsl -d Ubuntu-24.04 -- /root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/manual-check/qa/start.py','```','',
'Остановить сайт, сохранив синтетическую базу:','', '```powershell','wsl -d Ubuntu-24.04 -- /root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/manual-check/qa/start.py stop','```','',
'Сайт слушает 127.0.0.1:8780 внутри WSL и доступен через Windows localhost. Docker-контейнер `kidsmap-manual-20261004` использует `--network none`, без TCP-портов; база хранится в volume `kidsmap-manual-20261004-data`. Повторный запуск не сбрасывает правки. Медиа, журнал и служебные файлы: `/tmp/kidsmap-task33-qa04-manual20261004`; они не предназначены для долговременного хранения. Очистка /tmp может удалить медиа.',
'','Приложение работает из `/root/km-manual-mapfix`; актуальные 2761 файла сверены с WORKTREE по source-manifest.json (исправление карты); исходный снимок завершения сохранён отдельно. Локальная обвязка находится только в `docs/task33/manual-check/qa/`; бизнес-код не подменяется. Используются DJANGO_TESTING=1, отдельная БД, локальный кеш и почта в памяти. Исходящие TCP/SMTP/Redis и чужие libpq-соединения заблокированы.',
'','Production не подключался. Исторические материалы `final-audit/` и `completion/` не изменялись; commit/push/deploy не выполнялись. Этот стенд оставлен работающим по запросу пользователя.',
'','## Как записать найденную проблему','', 'Номер шага → роль → URL → язык и ширина окна → действия → ожидание → фактический результат. Приложите скриншот и текст неожиданной ошибки Console. Не отправляйте настоящие персональные документы.']
(root/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('README written: '+str(len(steps))+' steps, '+str(len(names))+' route labels')
