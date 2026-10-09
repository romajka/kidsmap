# ORG-04 — свежая проверка и план совместимости

2026-10-08, `/root`, kidsmap-orchestrator. PLAN ONLY по явному условию готового ORG-04 prompt; приложение не изменено. Один исполнитель, без независимого reviewer. AGENTS/контракты и оба audit reports прочитаны; исторические findings перепроверены.

LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, task33-progress,185 dirty/untracked entries. Runtime QA8788:source2758,digest `b195aa9e839f4b63d306dfa036230426757a5e94510fa37581901b43acb5ece5`, start2026-10-08T08:16:31.472041+00:00. [Snapshot](org-04-compatibility-2026-10-08/evidence/snapshot.json). Production UNKNOWN/NOT RUN.

Проверки только в отдельной disposable PostgreSQL unit DB:DJANGO_TESTING=1, LocMem cache/email, изолированные media/private-media, отключённые credentials, network/libpq guards. Созданы только локальные вымышленные fixtures. Ни preview стенда, ни его существующие данные не менялись; unit DB после запуска уничтожена.

Команда: `.venv/bin/python .tmp/org04-plan-20261008/run_unit.py --script probes.py`.4/4 probes PASS,3.232s,0F/0E; это успешное подтверждение **существующего дефекта**, а не исправление. [Evidence](org-04-compatibility-2026-10-08/evidence/probes.json), [точный log](org-04-compatibility-2026-10-08/evidence/probes.log).

| Проверка | Свежий результат | Оценка |
|---|---|---|
| Старый HTML POST,актуальная версия,действительный CSRF,без consent/receipt |302,связь удалена,operation не создана |ORG-04 CONFIRMED |
| Старый JSON detach,то же |200,связь удалена,operation не создана |ORG-04 CONFIRMED |
| Существующий detach-preview |GET200;без consent409 и связь сохранена;с consent302 и detach |Новый путь работает в проверенном случае |
| Владелец архивной сети,приватное место другого владельца |canonical detach разрешён;preview PermissionDenied |Подтверждён compatibility gap,простого redirect недостаточно |

Первопричина:organization_workspace.organization_detach и ownership API detach напрямую вызывают canonical mutation, не проверяя receipt/consent/snapshot зависимостей. Действующий consumer остался в owner_places.html:88 — это не только устаревший маршрут. Organization workspace уже использует preview ссылку. Репозиторный literal поиск нашёл API route и tests; внешние клиенты UNKNOWN, отсутствие их в исходниках не доказывает отсутствия использования.

Предложение: [конкретный implementation/compatibility plan](../superpowers/plans/2026-10-08-org-04-detach-compatibility.md). Старый HTML направляет к review; JSON detach прекращает мутацию и возвращает409 confirmation_required с review URL. Coordinator сохраняет lawful mutation authority, отделяя её от права читать metadata. Canonical detach и другие права/действия не меняются.

Codebase Memory callable; wildcard поиск detach дал0, поэтому impact проверен bounded rg + actual source:controllers,urls,services,owner/workspace templates и transport/canonical tests. Graph-negative не использован как доказательство отсутствия callers.

**NOT RUN:** реализация, браузерная приёмка RU/AZ/EN×widths/keyboard, скриншоты изменённого UI, full suite/CI/image, внешние API clients, production/commit/push/deploy. После согласования план предусматривает эти локальные проверки с отдельными границами. Прочие findings не исправлялись.

Все входные файлы сохранены; [preservation manifest](org-04-compatibility-2026-10-08/evidence/preservation.json). Новые Git-visible файлы только этот отчёт/evidence и план. active_run остаётся NONE. Требуется согласование API compatibility; до него никакой application implementation не выполняется.
