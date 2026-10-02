# Перенос домой — 2026-10-02

Ветка: `task33-progress`, remote: `git@github.com:romajka/kidsmap.git`.
Пользователь отдельно разрешил commit и push этой ветки. Push в `main`, merge и deployment не разрешены. Workflow `.github/workflows/deploy.yml` запускает deployment только для push в `main`.

Переносится текущая реализация этапов 05–20, миграции 0117–0127, переводы, static/templates, тесты и весь переносимый пакет `docs/task33` (включая макеты, PNG, планы, отчёты, QA helpers и журнал). `.env`, credentials, local DB, virtualenv, compiled bytecode и игнорируемые scratch-файлы не включены.

## Продолжение

1. Клонировать ветку `task33-progress` и открыть корень проекта. Не переключаться на исторический HEAD из отчётов: SHA в них описывает состояние до этого transfer commit.
2. Создать локальную `.venv`, установить зависимости из `requirements.txt`. Не копировать production credentials. Требования изолированного QA: [qa04/README.md](qa04/README.md); нужны local Docker и cached `postgres:17-alpine`, launcher не скачивает image сам.
3. Прочитать [implementation-status.md](implementation-status.md), проверить `active_run`, затем [prompts/21.md](prompts/21.md) и непосредственный отчёт [reports/20.md](reports/20.md).
4. Поручение новому диалогу: «Выполни только этап 21 по docs/task33/prompts/21.md. Следующие этапы и production запуск не выполнять». Этот перенос не выполняет этап 21.

Последний статус: stage20 DONE locally, stage21 NOT_STARTED, active_run NONE. Historical full-suite/application NOT_GREEN; новый полный прогон в рамках переноса не выполнялся. Перенос не является production release или новой приёмкой приложения.

## Отдельный QA архив

На исходной машине: `scratch/task33-transfer-20261002/task33-qa-evidence-20261002.tar.gz` (ignored, через Git не переносится). Рядом `SHA256SUMS` и `manifest.json`. Скопировать эту папку отдельно на домашнюю машину.

Архив содержит 2966 сохранившихся файлов из `/tmp`, на которые ссылается пакет Task33, в том числе 436 PNG, локальные synthetic QA results/logs, harness scripts и source snapshots. Все архивные файлы сверены с SHA256 manifest; symlinks/compiled bytecode исключены. Не все исторические `/tmp` пути ещё существуют; архив не восстанавливает отсутствующие файлы и не переносит running containers, local DB или установленную среду.

Размер архива: 98933296 bytes. SHA256: `b8e0da871020f215db3f9fa9e08e364b01b34235f1493fc89fd7515e7740e84c`.
Имена внутри архива относительны к `/tmp`; распаковать в отдельную scratch-папку, если нужны старые screenshots/evidence. Для новой проверки запускать QA заново и сохранять новые результаты.
