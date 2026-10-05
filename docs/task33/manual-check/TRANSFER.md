# Продолжить тестирование на другом компьютере

Ветка: **task33-progress**. Это весь текущий код этапов21–28, завершение пунктов1–5, исправления карты/админки, тесты, отчёты и скриншоты. Production готовность остаётся отдельным пунктом6; push этой ветки не запускает deployment workflow.

## 1. Забрать код в Windows

Если проекта ещё нет, откройте PowerShell:

```powershell
git clone --branch task33-progress https://github.com/romajka/kidsmap.git C:\kidsmap
cd C:\kidsmap
```

Если проект уже есть:

```powershell
cd C:\kidsmap
git status
git fetch origin
git switch task33-progress
git pull --ff-only origin task33-progress
```

Если `git status` показывает собственные незакоммиченные изменения, сохраните их отдельным коммитом или `git stash push -u` перед переключением. Не используйте reset/clean/force pull.

## 2. Подготовить окружение один раз

Нужны **WSL Ubuntu24.04**, Docker Desktop с Linux containers и включённой интеграцией с этой WSL-дистрибуцией, Python≥3.12. В Linux можно выполнять те же команды прямо из папки checkout.

Откройте Ubuntu/WSL и выполните:

```bash
cd /mnt/c/kidsmap
sudo apt-get update
sudo apt-get install -y python3-venv python3-dev build-essential pkg-config default-libmysqlclient-dev libpq-dev gettext
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
docker pull postgres:17-alpine
```

`docker info` должен завершаться без ошибки. Секреты, `.env` и production credentials для этого стенда не нужны.

## 3. Запустить

Из WSL:

```bash
cd /mnt/c/kidsmap
.venv/bin/python docs/task33/manual-check/qa/portable.py
```

Дождитесь строки **READY**. Первый запуск компилирует переводы, применяет миграции в отдельной локальной PostgreSQL и создаёт синтетические роли, организацию/программу/занятия, события, специалистов и **100 дополнительных мест с фотографиями**. Всего публичных мест —103. Повторный запуск не создаёт повторных100 записей и не переписывает уже существующие демо-места.

| Что открыть | Ссылка | Ожидаемый результат |
|---|---|---|
| Ручной маршрут и смена роли | http://localhost:8780/qa/ | Пошаговая инструкция и ссылки именно на записи нового стенда |
| Главная | http://localhost:8780/ru/ | Страница загружается, карта и поиск доступны |
| Каталог | http://localhost:8780/ru/catalog/ | 103 места, фотографии, фильтры |
| Админка | http://localhost:8780/admin/ | Вход и боковое меню |
| Организации | http://localhost:8780/admin/catalog/organization/ | Обычная высота таблицы и маленькая стрелка сортировки |
| События | http://localhost:8780/ru/events/ | Публичные события нового стенда |
| Специалисты | http://localhost:8780/ru/specialists/ | Демонстрационные профили |
| Исторический полный отчёт | http://localhost:8780/qa/files/report/report.html | Таблицы и скриншоты завершения |

Локальный администратор: **demo_moderator / KidsMap-local-2026**. Владелец: **demo_owner / KidsMap-local-2026**. Другие роли: `demo_parent`, `demo_manager`, `demo_person`, `demo_outsider`, `demo_volunteer`, пароль тот же. Это намеренно публичные пароли исключительно синтетического локального QA-стенда.

Сначала просмотрите данные; затем по `/qa/` проходите создание → сохранение → модерация → публичный каталог → фильтры → карта. На320/390px проверьте прокрутку таблицы внутри её области, меню «…», «Ещё», сортировку Enter и переключение RU/AZ/EN.

## 4. Остановить и обновить код

```bash
cd /mnt/c/kidsmap
.venv/bin/python docs/task33/manual-check/qa/portable.py stop
git pull --ff-only origin task33-progress
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python docs/task33/manual-check/qa/portable.py
```

При обновлении сначала остановите процесс: Python-сервер не включает autoreload. Остановка сохраняет PostgreSQL volume и медиа. Не выполняйте `docker volume rm` или удаление QA-root, если хотите сохранить ручные изменения.

Если8780 занят другим процессом, в WSL задайте `KIDSMAP_PREVIEW_PORT=8781` перед **обеими** командами start/stop. Все ссылки в живом `/qa/` адаптируются к выбранному порту.

## Что сохраняется и что создаётся заново

Git переносит код, миграции, seed-скрипты, исходные демо-фотографии, инструкции и доказательства проверок. Реальная БД и секреты в Git не отправляются. На другом компьютере создаётся **новая синтетическая база**; IDs и даты событий могут отличаться, поэтому используйте живой `/qa/`, а не IDs из исторических скриншотов. Ручные изменения старой локальной БД через Git не переносятся.

Portable-данные: `/tmp/kidsmap-task33-qa04-manual-portable`; Docker container `kidsmap-manual-portable`, volume `kidsmap-manual-portable-data`. PostgreSQL не имеет сети и опубликованных портов; приложение слушает только loopback. Cache/mail локальные, внешние TCP/SMTP и посторонние Unix/libpq подключения заблокированы guard. `.env` не загружается. Старый стенд и исторические `completion/`/`final-audit/` не переписываются.

Старые `.env#` и `backups/db.sqlite3.before-migrate-20260831-151210` исключены из нового Git-tip, локальные файлы сохранены. История Git не переписывается; это не заявление об очистке старой истории.

Новые доказательства переноса — `transfer/verification.json`; исправления админки — `admin-fix/REPORT.md`. Исторические большие наборы тестов не объявляются заново выполненными этим переносом.

Перенос проверен 2026-10-05 на отдельном порт8781 и новой PostgreSQL:168 миграций,103public places/396images, перезапуск0new records;3 portable-contract tests PASS. Реальный Chromium: вход администратора/стрелка14px, каталог103 и12 декодированных фото после прокрутки, мобильная строка99.84px без переполнения, ссылки нового `/qa/` с актуальными IDs/портом PASS; console/network ошибок0. Проверены146 исторических файлов completion и164 final-audit, без изменений. Проверка Git-whitespace отмечает только сохранённые пробелы/пустые строки исторических материалов и ранее проверенных источников; они не редактировались ради push.
