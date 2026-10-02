# KidsMap admin макеты — admin-public-03-r1

Status: **awaiting_user_review**. Только static synthetic fixtures этапа 03. Общий план не является принятием дизайна.

## Просмотр

`python3 docs/task33/design/shared03/preview.py` открывает allowlisted preview только на 127.0.0.1:8763. Затем `/docs/task33/design/admin/index.html`. Завершить Ctrl+C. Сервер не раздаёт env, приложение, media или БД. HTML также можно открыть локально; проверки выполнены через HTTP.

AZ/RU/EN в шапке. Параметры `long=1`, `missing=1` показывают длинный текст и AZ fallback. Переводы учебные, не редакторская готовность реальных карточек. Все фотографии отсутствуют намеренно; category placeholder использует действующие tokens/Material Symbols. Данные не сохраняются после reload.

## Экраны

- [groups](groups.html?lang=ru)
- [index](index.html?lang=ru)
- [organization](organization.html?lang=ru)
- [place](place.html?lang=ru)
- [review](review.html?lang=ru)
- [transfer](transfer.html?lang=ru)

Review variants: [volunteer](review.html?lang=ru&state=volunteer), [base conflict](review.html?lang=ru&state=conflict), [new](review.html?lang=ru&state=new), [shared program](review.html?lang=ru&state=program). Approve/return/transfer dialogs simulate consequences; no ACL/API/email or persistence. Readonly group name is reviewed separately; save control applies amount/schedule only.

## Browser screenshots

22 настоящих PNG Chromium, widths 390/1280. Отдельная матрица проверяет 320/360/390/768/1024/1280/1440 на AZ/RU/EN.

- [groups-ru-1280](screenshots/groups-ru-1280.png)
- [groups-ru-390](screenshots/groups-ru-390.png)
- [index-ru-1280](screenshots/index-ru-1280.png)
- [index-ru-390](screenshots/index-ru-390.png)
- [organization-ru-1280](screenshots/organization-ru-1280.png)
- [organization-ru-390](screenshots/organization-ru-390.png)
- [place-ru-1280](screenshots/place-ru-1280.png)
- [place-ru-390](screenshots/place-ru-390.png)
- [program-approve-dialog-en-1280](screenshots/program-approve-dialog-en-1280.png)
- [program-approve-dialog-en-390](screenshots/program-approve-dialog-en-390.png)
- [review-conflict-ru-1280](screenshots/review-conflict-ru-1280.png)
- [review-conflict-ru-390](screenshots/review-conflict-ru-390.png)
- [review-new-ru-1280](screenshots/review-new-ru-1280.png)
- [review-new-ru-390](screenshots/review-new-ru-390.png)
- [review-program-ru-1280](screenshots/review-program-ru-1280.png)
- [review-program-ru-390](screenshots/review-program-ru-390.png)
- [review-ru-1280](screenshots/review-ru-1280.png)
- [review-ru-390](screenshots/review-ru-390.png)
- [transfer-dialog-en-1280](screenshots/transfer-dialog-en-1280.png)
- [transfer-dialog-en-390](screenshots/transfer-dialog-en-390.png)
- [transfer-ru-1280](screenshots/transfer-ru-1280.png)
- [transfer-ru-390](screenshots/transfer-ru-390.png)

Evidence: [основная матрица](../shared03/verification.json), [дополнительная матрица](../shared03/extra-verification.json), [regressions](../shared03/regression-results.json), [отчёт 03](../../reports/03.md), [independent review](../../reports/03-review.md).
