# MOD-QA-02 — Фото и галерея в централизованной модерации отображаются путями

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin / content reviewer. URL/endpoint: `/ru/admin/volunteer/moderation/content/39/`. Проверенные cells: Свежий валидный candidate: RU 1440/390; общая таблица comparison — 18 cells.

Шаги: В кабинете владельца выбрать главное фото и два фото галереи, дождаться ready, сохранить черновик, reload и отправить. Открыть реальную pending-заявку в moderation hub.

Ожидание: Просмотр текущего и предложенного главного фото и галереи с порядком, пригодный для визуального решения.

Факт: В .km-volunteer нет ни одного img. Главное фото — places/gallery.webp, галерея — строковое представление массива словарей. При этом native approve применяет фотографии; публичная карточка после reload реально загружает все три фото.

Причина / границы гипотезы: hub_detail.html выводит before/after как обычные строки. Native valid payload и публичный readback подтверждают, что дело не в повреждённой фикстуре. Отдельная legacy review имеет preview, но она superadmin-only; штатный content reviewer получает там 403.

Source: src/catalog/templates/admin/volunteer/hub_detail.html:9–11; src/catalog/services/moderation_hub.py:reviewer_scopes / changes. Доказательства: [gallery-finish.result.txt](../gallery-finish.result.txt), [flows2.result.txt](../flows2.result.txt), [acl.result.txt](../acl.result.txt), [gallery-valid-pending-hub-pc.png](../screenshots/gallery-valid-pending-hub-pc.png), [gallery-valid-pending-hub-mobile.png](../screenshots/gallery-valid-pending-hub-mobile.png), [gallery-approved-public-en-390.png](../screenshots/gallery-approved-public-en-390.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Проверяющий может принять фотографии, которых не видит в доступной ему поверхности. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Typed presentation of media changes in moderation hub; безопасная выдача preview по существующим правам. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; publication payload/gallery order; privacy/storage; модуль01. Не расширять права на приватные документы.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-02.txt).
