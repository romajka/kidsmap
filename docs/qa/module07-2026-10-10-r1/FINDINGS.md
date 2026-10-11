# ACCESS-QA — подтверждённые findings, модуль07 / 2026-10-10-r1

LOCAL WORKTREE `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. HTTP `http://localhost:8820`. Все данные вымышленные. Приложение не исправлялось. Пять P2; P0/P1 не установлены. Наличие дефектов на этом snapshot не устанавливает дату регрессии. Полная матрица: [matrix.csv](matrix.csv), ограничения: [coverage-gaps.json](coverage-gaps.json).

## ACCESS-QA-01 — фокус выходит из модального окна восстановления пароля

- Роль: anonymous; URL `/ru/auth/login/`, `/auth/login/`, `/en/auth/login/`.
- P2: пользователь клавиатуры попадает на скрытые за модальным окном элементы и теряет место после закрытия. Обход ACL не обнаружен.
- Шаги: открыть «Забыли пароль?», дождаться фокуса в email, нажать Tab несколько раз; затем Escape.
- Ожидание: фокус циклически остаётся в открытом диалоге; после закрытия возвращается на кнопку открытия.
- Факт: уже второй Tab переводит фокус на BODY, затем на элементы фона. Escape закрывает окно, но оставляет фокус на фоне. 18/18 сочетаний RU/AZ/EN × 360/390/768/1024/1280/1440; 36 FAIL observations по двум проверкам. Само закрытие после завершения CSS-перехода PASS.
- Доказательства: [modal-proof.result.txt](modal-proof.result.txt), [mobile](screenshots/reset-focus-trap-ru-390.png), [PC](screenshots/reset-focus-trap-en-1440.png). Лог actual `document.activeElement` важнее одного изображения фокуса.
- Подтверждённая причина: `src/catalog/templates/auth/login.html:312` / `openModal`, `:338` / `closeModal`, `:380` / keydown. Есть начальный focus и Escape, нет Tab trap/inert фонового содержимого и восстановления opener.
- Область: login/reset-modal accessibility; зависимости: существующие AJAX, input preservation, i18n и CSS transitions. Confidence HIGH.
- Промпт: [repair-ACCESS-QA-01.txt](repair-ACCESS-QA-01.txt).

## ACCESS-QA-02 — получатель не может отклонить приглашение через UI

- Роль: получатель приглашения; URL `/ru/account/notifications/` и языковые варианты.
- P2: приглашение можно принять или пометить прочитанным, но нельзя выразить отказ. Это недостающий пользовательский шаг; серверный отказ работает.
- Шаги: владелец места/сети отправляет приглашение вымышленному пользователю; получатель открывает уведомления.
- Ожидание: у актуального приглашения доступны принятие и отказ с корректной обработкой повтора/устаревания.
- Факт: две свежие карточки приглашений места и организации имеют только Accept и Mark read. Native decline NOT RUN из-за отсутствующего control. Реальный CSRF POST `/ru/account/business/team/place/1/reject/` →200, статус REJECTED. Это не проблема серверного перехода.
- Доказательства: [person-deletion.result.txt](person-deletion.result.txt) содержит actual form actions, [две карточки](screenshots/recipient-pending-place-and-org-ru-390-person.png), [place HTTP rejection](team-resume.result.txt), [исходный inbox](screenshots/reject-inbox-no-action-ru-390.png).
- Подтверждённая причина: `src/catalog/templates/pages/account_notifications.html:16` выводит только accept; `controllers/workflow_notifications.py` реализует accept/mark_read; reject реализован в `controllers/business_team_api.py` и `services/business_team.py`.
- Область: recipient inbox presentation + безопасный POST adapter к существующему service; не расширять роли/ACL. Проверено rendered RU390; наличие одного общего шаблона установлено source, native decline остальных комбинаций явно NOT RUN. Confidence HIGH.
- Промпт: [repair-ACCESS-QA-02.txt](repair-ACCESS-QA-02.txt).

## ACCESS-QA-03 — управление сотрудниками сети отсутствует в кабинете

- Роль: network owner; URL `/ru/account/organizations/1/`, `/account/organizations/1/`, `/en/account/organizations/1/`.
- P2: владелец может приглашать, но в пользовательском интерфейсе не может изменить роль, отозвать сотрудника или отменить ожидающее приглашение сети.
- Шаги: пригласить пользователя через UI; принять из inbox; открыть раздел «Сотрудники» владельцем. Для pending invitation также открыть список приглашений.
- Ожидание: разрешённые владельцу операции управления имеют доступные controls, отправляют актуальную version и честно показывают конфликт/ошибку.
- Факт: grants и invitations — read-only строки; native role/remove/cancel NOT RUN. Отсутствие controls подтверждено на всех18 сочетаниях. При этом actual JSON role change/remove возвращают200, stale expected_version →409 без изменений. Native invite и accept PASS.
- Доказательства: [supplement-matrix.result.txt](supplement-matrix.result.txt), [PC](screenshots/organization-team-filled-en-1440.png), [mobile](screenshots/organization-team-filled-ru-390.png), [HTTP transition/conflict](team-resume.result.txt), [отзыв и открытая вкладка](access-transitions.result.txt).
- Подтверждённая причина: `src/catalog/templates/pages/organization_workspace.html:462` и `:482` отображают grants/invitations без management forms; `static/js/organization_workspace.js:301` обрабатывает invite. Серверные `grant`, `cancel`, `confirm` существуют в business-team API/service.
- Область: organization workspace UI и его JSON adapters; зависимости: server permission configuration, selected_places/all_network, expected_version, актуальная ownership version, notifications. Confidence HIGH.
- Промпт: [repair-ACCESS-QA-03.txt](repair-ACCESS-QA-03.txt).

## ACCESS-QA-04 — карточки приглашений места обрезаются на 360px

- Роль: place owner; URL `/ru/account/places/team/` и языковые варианты.
- P2: email получателя невозможно целиком прочитать на минимальной заявленной ширине.
- Шаги: отправить вымышленному `cancelled07@example.invalid` приглашение; открыть список при viewport360.
- Ожидание: карточка помещается в доступную ширину, длинные email/имена переносятся.
- Факт: карточка начинается x21 и заканчивается x380.1875 при viewport360. Правый край и email обрезаны. BODY/root scrollWidth остаётся360, поэтому один root-overflow check дефект пропускает. RU/AZ/EN360 FAIL;390 и более в проверенном наборе PASS.
- Доказательства: [bounds](supplement-matrix.result.txt), [RU360](screenshots/place-team-filled-ru-360.png), [EN360](screenshots/place-team-filled-en-360.png).
- Подтверждённая причина: `static/css/site.css:9724` / `.owner-team-list`, `:9730` / `.owner-team-item`, `:9740` / headings: grid min-content не ограничен, непрерывный email не переносится. Geometry и rendered clipping подтверждены; итоговое CSS-решение требует обычной проверки каскада.
- Область: team cards responsive CSS; учитывать shared selectors `.owner-review-item`, не менять review поведение без проверки. Confidence HIGH.
- Промпт: [repair-ACCESS-QA-04.txt](repair-ACCESS-QA-04.txt).

## ACCESS-QA-05 — ошибки удаления аккаунта на AZ/EN остаются русскими

- Роль: обычный пользователь; `/account/deletion/<fixture UUID>/confirm/` (AZ prefix `/`), `/en/account/deletion/<fixture UUID>/confirm/`.
- P2: критичная операция показывает инструкцию/ошибку на другом языке, пользователь не понимает, что исправлять. Деактивация не происходит при неверном подтверждении.
- Шаги: на своём аккаунте запросить удаление; в AZ/EN отправить неверный код, затем неверную точную фразу.
- Ожидание: язык ошибок соответствует активному AZ/EN, смысл объясняет неверный код/фразу.
- Факт: «Неверный код подтверждения.» и «Введите фразу подтверждения точно так, как она показана.» отображаются по-русски внутри AZ/EN формы. Native evidence AZ/EN390/1440, 8 FAIL observations. Functional denial PASS. Проверка выполнена с SIMULATED существующей TEST_POLICY; штатная политика в initial settings inactive.
- Доказательства: [AZ code](screenshots/deletion-code-error-az-390.png), [EN code](screenshots/deletion-code-error-en-1440.png), [EN phrase](screenshots/deletion-phrase-error-en-390.png), [locale-runtime.json](locale-runtime.json), [deletion native flow](deletion-flow.result.txt).
- Подтверждённая причина: сообщения `src/catalog/views.py:1980–1981` используют gettext; runtime gettext возвращает русский msgid. Записи code error в `locale/az/LC_MESSAGES/django.po:17809` и `locale/en/LC_MESSAGES/django.po:17701` fuzzy и содержат неверный смысл («ввести код»). Переданный WORKTREE включает существующие `.mo`; новые каталоги в этом аудите не компилировались и не подменялись.
- Область: точные auth/deletion locale messages + воспроизводимая сборка runtime catalogs в изолированном verification. Не удалять fuzzy флаги массово и не изменять серверную проверку ради UI. Confidence HIGH. Свести общие locale причины с другими модулями в13, но данный finding доказан свежим браузером.
- Промпт: [repair-ACCESS-QA-05.txt](repair-ACCESS-QA-05.txt).
