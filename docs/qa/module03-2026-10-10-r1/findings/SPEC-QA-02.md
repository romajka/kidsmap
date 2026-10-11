# SPEC-QA-02 — после 409 сломано превью сохранённого фото

Статус OPEN; P2; подтверждённый специалист. Среда localhost:8814, fresh WORKTREE HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, 2026-10-10. Current baseline failure; regression относительно предыдущей версии не установлена. Уверенность высокая в факте, source-backed объяснение цепочки.

URL: `/ru/account/specialists/1/`; запрос фото `/media/proposal_…webp` возвращает404.

1. Открыть профиль с уже сохранённым фото в двух вкладках одной person-сессии.
2. В первой изменить альтернативное имя на STALE; во второй на NEWER и сохранить.
3. Сохранить первую, получить настоящий409 и сообщение «Запись изменилась».
4. Прокрутить к фотографии; затем reload второй вкладки.

Ожидание: ошибка конфликта сохраняет ввод и показывает существующее фото по действующему URL. Факт: STALE остаётся, NEWER защищено, но основное превью имеет naturalWidth0 и URL без `specialists/photos/`, HTTP404. Каноническое фото на сервере остаётся; потери данных не установлено. Обычная400 на чрезмерном стаже сохраняет работающее превью — отдельная отрицательная контрольная проверка PASS.

Доказательства: [conflict-recheck.result.txt](../conflict-recheck.result.txt), [контроль400](../error-preview.result.txt), [PC](../screenshots/person-conflict-photo-1440.png), [mobile](../screenshots/person-conflict-photo-390.png), [все 18 конфликтов](../state-matrix.result.txt).

Цепочка источников: `owner_specialist_use_cases.py:71` бросает stale_version до штатного form.full_clean; `controllers/specialist_workspace.py:328` вызывает form.add_error, который запускает clean; `forms.py:2370–2378` нормализует даже уже сохранённое фото для draft; ModelForm меняет instance в памяти; `templates/pages/owner_specialist_create.html:171` читает specialist.photo.url этого instance. Получается имя нового ещё не сохранённого ContentFile вместо канонического пути. Проверить эту цепочку тестом до выбора реализации.

P2: конфликт сохранения показывает сломанное фото и создаёт сомнение в сохранности анкеты. Область — изоляция persisted preview от bound/invalid/conflicted form и корректная обработка существующего FieldFile; сохранить CAS и ввод. Зависимости: контроллер, форма, template; соседние400 и новый выбранный upload должны остаться корректными.

Самостоятельный промпт:

```text
Работай в фактическом корне KidsMap, прочитай AGENTS.md/.agents и docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-02.md. Исправь только сломанное превью существующего фото при stale-version409. Перед реализацией подготовь конкретный план; следуй имеющейся авторизации, иначе согласуй scope.
В двух вкладках person-профиля сохранение NEWER, затем STALE даёт правильный409 и защищает NEWER, но HTML основного превью получает /media/proposal_…webp без specialists/photos/ и image404. Исследуй связку save_owner_specialist_profile stale check → controller form.add_error → OwnerSpecialistForm.clean/нормализация существующего FieldFile → template specialist.photo.url. Нужно показывать действующее persisted фото и сохранять пользовательский ввод при конфликте без повторной записи/копирования существующего файла. Не ослабляй CAS, проверку person и публикационную модерацию. Meaningful regression test должен проверять реальный URL, файл и состояние БД на409, плюс контроль400 и новый upload. Затем свежий rendered UI двух вкладок/reload на RU/AZ/EN PC/mobile, screenshot ошибок и network. Только DJANGO_TESTING=1 с отдельными DB/cache/media/private-media/email и вымышленными данными. Не меняй assertions ради зелёного. Сохрани чужие изменения/active_run/стенды; без commit/push/deploy/production и других исправлений.
```
