# Пункт 4: надёжность уведомлений

APPROVED IMPLEMENT, active_run `completion-20261004-095717Z`, LOCAL dirty WORKTREE / HEAD `015d031d8eb17114bd860159dde805b38df3c13c`. Production и реальный SMTP не затронуты. Canonical security-reviewer; отдельный исполнитель от root. Codebase Memory `C-kidsmap` ready, bounded search deliver_batch 1/1, без pagination; граф — подсказка, актуальная логика проверена в исходнике.

Сервис и модель уже выполняют согласованную политику, поэтому изменение поведения не понадобилось. Добавлен `test_task33_notification_crashes.py`: десять TransactionTestCase на настоящем одноразовом PostgreSQL. Вместе с существующими одиннадцатью тестами уведомлений: **21/21 PASS**, 0F/0E/0skip. Фактический результат: [security-notifications.json](security-notifications.json), SHA исполненных четырёх файлов совпадают с WORKTREE: [security-notifications-source.json](security-notifications-source.json).

Синтетический почтовый backend сохраняет принятие письма в fsync-журнал вне транзакции БД. Проверены crash до SMTP, после принятия SMTP, после фактического UPDATE sent до COMMIT и после успешного COMMIT. В двух неоднозначных окнах новый DB connection видит откат pending/attempts0, но внешний журнал сохраняет одно принятие; автоматический повтор увеличивает журнал до двух. Это демонстрирует разрешённый дубликат без второго inbox/outbox. После зафиксированного sent три повтора не отправляют письмо. Два настоящих worker-thread/DB connection проверяют skip_locked: второй не отправляет, пока первый удерживает строку.

Перед повтором проверены смена адреса, деактивация пользователя, отмена приглашения и смена владельца штатным сервисом: старое письмо становится suppressed/stale_access, второго принятия нет. Перед crash приглашение, inbox и outbox уже зафиксированы бизнес-транзакцией; они не откатываются вместе с доставкой. Пять обычных SMTP ошибок подтверждают интервалы 2/4/8/16 минут, attempts5/failed и отсутствие шестой отправки. Повторные аварии до COMMIT не сохраняют счётчик attempts; это документированная граница, а не гарантия неограниченной доставки.

Первый фактический прогон: 20PASS/1ERROR — новый fixture попытался прямой save readonly ownership_version и был корректно отклонён structural guard. Сохранён [security-notifications-first.json](security-notifications-first.json). Fixture исправлен на реальный transfer_owner; проверяются version2 и два новых ownership_transfer notice, уникальность исходного invitation notice/outbox сохранена. Это ошибка fixture, не RED приложения; тесты не ослаблены, guard не изменён. Дополнительный application fix для получения GREEN не создавался.

Команды:

```text
cd /root/km-completion-security
.venv/bin/python docs/task33/qa04/run.py --mode all --output /tmp/task33-completion-security-notifications-final-20261004 --label catalog.testcases.test_task33_notification_crashes --label catalog.testcases.test_task33_notifications
```

DJANGO_TESTING=1, disposable PostgreSQL/cache/media/locmem email, transport/libpq guards TRUE, external_credentials FALSE, check/makemigrations exit0, normal cleanup PASS; точные версии/counts содержатся в JSON. Raw только внешний `/root/task33-evidence/completion-security-notifications-final-20261004`.

Политика для документов root: автоматические повторы используют at-least-once семантику; SMTP принятие до COMMIT sent допускает редкий дубликат. Зафиксированный sent никогда не повторяется. Свежие проверки адреса/активности/приглашения/владения предшествуют каждой попытке. Обычные SMTP ошибки ограничены пятью попытками с backoff; failed и suppressed означают отсутствие обещания eventual delivery. Inbox и бизнес-изменения независимы от сбоя письма; exactly-once не обещается.

NOT RUN: реальный SMTP/provider, OS SIGKILL/сбой PostgreSQL, production cron/worker, distributed external delivery. Fault injection использует необработанный BaseException и настоящий rollback, не обещает покрытие всех внешних отказов. Полный suite и независимый ACL/новая taxonomy/concurrency сверка — следующий согласованный шаг после readiness Django; этот bounded прогон не выдаётся за полный.

Named handoff **NOTIFICATIONS_POINT4 → root/django-reviewer**: принять фактическую семантику, обновить принадлежащие root decisions/stage17 docs, включить новые десять cases в полный host/image acceptance. Приложение, старые final-audit/QA/reports, production, Git/deploy не изменены.
