# CE-C-02 — согласованный scope

Авторизация: пользователь прямо поручил доделать CE-C-02. Один root/kidsmap-orchestrator, без подагентов.

1. Свежий rendered RED на текущем8790, сверить обязательность lat/lng и readiness на synthetic данных.
2. Заменить единственную административную подсказку: «Точка на карте необязательна. Рекомендуем указать её; можно вернуться к карте позже.»
3. Обновить только соответствующий ключ RU/AZ/EN PO/MO, сохранить остальные переводы и весь другой source. Никаких JS/CSS/backend/schema изменений.
4. Новый owned snapshot/runtime, rendered RU/AZ/EN×360/390/768/1024/1280/1440: тексты, карта недоступна, keyboard toggle, address without coordinates, saved coordinates, native save/reload/publication. Скриншоты PC/mobile, diff/report/PASS/FAIL/NOT RUN.
5. Закрыть свой active_run. Production/commit/push/deploy запрещены.
