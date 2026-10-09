# CE-C-01 — принятый локальный scope

Авторизация: «продолжи» после отчёта с отдельными CE-C-01/02; первым выполняется CE-C-01. Один исполнитель, без подагентов.

1. Зафиксировать HEAD/WORKTREE и byte baseline; воспроизвести реальным admin POST.
2. Добавить падающую регрессию: сохранённые photo/cover_photo → reload → POST без файла → publish → public.
3. Минимально исправить PlaceAdminForm: для bound POST установить initial только двух file fields из canonical saved candidate; остальные поля, source/token/CAS, ACL, requirements оставить прежними.
4. Проверить repeat draft, replacement, clear, published revision, stale version, storage failure; related admin/media/publication regressions.
5. На isolated8790: fresh runtime hashes, RU/AZ/EN×360/390/768/1440, Enter/modal, PC/mobile before/after. Отчёт/diff/NOT RUN. CE-C-02 и остальные findings не менять. Без production/commit/push/deploy.

Уточнение по свежему RED в том же scope: кроме initial, проецировать только два media поля в bound instance. Иначе пустой candidate даёт cleaned None, который FileField.save_form_data трактует как no change и восстанавливает live photo. Для действующего удаления исправить selector checkbox в одном месте media JS. Регрессия clear опубликованного фото → draft → POST без повторного clear → publication обязательна.
