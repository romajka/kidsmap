# ORG-QA-02 — владелец не может отозвать сетевой доступ через кабинет

Статус OPEN; P2; высокая уверенность для отсутствия UI. API отзыв проверен отдельно. Локальный текущий WORKTREE; regression не установлена.

Роль: владелец сети. URL: `/ru/account/organizations/1/#org-team`.

1. Владелец приглашает сотрудника MANAGER на всю сеть через форму.
2. Сотрудник принимает приглашение в уведомлениях. Доступ к связанному месту действительно появляется.
3. Владелец открывает «Сотрудники»: есть список активного разрешения и приглашения, форма нового приглашения и обновление списка.
4. Нет действия изменения/отзыва разрешения или отмены pending приглашения в этом интерфейсе.

Ожидание: пользователь может завершить управление созданным через кабинет доступом — с понятным подтверждением, сохранением и актуализацией списка. Факт: серверные `grant`/`cancel` поддержаны, но действия владельцу через рабочий кабинет не предлагаются. Сотруднику в уведомлениях также не предлагается явное «Отказаться»; основной finding ограничен отзывом владельцем.

Доказательства: [UI invitation / real acceptance](../team.result.txt), [controls and API cancellation](../team-api.result.txt), [native revoke](../final-access.result.txt), [supported-route access proof](../access-proof.result.txt), [active informational scope / revoke](../informational-access.result.txt), [owner screenshot](../screenshots/team-no-management-390.png). В final-access строка UI должна быть FAIL; API revoke — PASS; первоначальные URL-only checks использовали ошибочный singular route и не засчитываются. Последующие проверки настоящего plural route доказывают прекращение сетевого и сохранность прямого доступа.

Source: `src/catalog/templates/pages/organization_workspace.html:463–496` выводит grants/invitations без management actions; JS обслуживает invitation creation/refresh. Существующие методы `/account/business/team/organization/<id>/grant/`, `cancel/`, `reject/` позволяют завершить серверный сценарий. Нельзя добавлять ещё одну модель прав.

Влияние P2: владелец вынужден обращаться к API/администратору для отзыва сотрудника. Не утверждается, что существующий API даёт лишние права. Ответственные: frontend account + Django team transport. Зависимости: grant version/CAS, invitation status, network/direct scope. Следующий шаг — отдельный согласованный UI repair.
