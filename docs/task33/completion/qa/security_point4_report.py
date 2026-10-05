"""Bounded approved point4 handoff; prior final-audit remains immutable."""
import hashlib
import json
from pathlib import Path

root=Path('/mnt/c/kidsmap');docs=root/'docs/task33/completion';mirror=Path('/root/km-completion-security')
results=json.loads((docs/'security-notifications.json').read_text())
suite=results['suite-results.json'];run=results['run.json'];isolation=results['isolation.json']
assert suite['tests_run']==21 and suite['failures']==suite['errors']==suite['skipped']==0
assert run['cleanup']=='PASS' and run['run_root_removed'] and run['socket_root_removed']
assert isolation['network_guard'] and isolation['libpq_guard'] and not isolation['external_credentials_present']
paths=['src/catalog/services/workflow_notifications.py','src/catalog/models/workflow_notification.py',
       'src/catalog/testcases/test_task33_notifications.py','src/catalog/testcases/test_task33_notification_crashes.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[{'path':n,'workspace_sha256':sha(root/n),'executed_mirror_sha256':sha(mirror/n)} for n in paths]
assert all(f['workspace_sha256']==f['executed_mirror_sha256'] for f in files)
proof={'active_run':'completion-20261004-095717Z','executor':'/root/stage28_release canonical security-reviewer',
       'mode':'APPROVED IMPLEMENT point4','production':'NOT_CONTACTED','files':files,
       'service_or_model_changed':False,'new_cases':10,'existing_cases':11,
       'at_least_once_crash_duplicate_proved':True,'committed_sent_not_resent':True,
       'smtp_acceptance_ledger':'fsync file outside database transaction; synthetic acceptance only',
       'new_tests':suite['executed_ids'],'guards':isolation,'cleanup':run,
       'policy_limit':'Five handled SMTP failures terminate; an uncommitted crash rolls back attempts. No unconditional delivery/exactly-once promise.'}
(docs/'security-notifications-source.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
report='''# Пункт 4: надёжность уведомлений

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
'''
(docs/'security-notifications.md').write_text(report,encoding='utf-8')
print({'tests':21,'source_files':4,'source_match':True,'service_changed':False,'production':'NOT_CONTACTED'})
