# EVENT-QA-02 — кнопка удаления главного фото ничего не удаляет

Статус: OPEN, P2. Роль: административный редактор. URL: `http://localhost:8815/admin/catalog/event/3/change/`. Среда: fresh isolated module04, тот же HEAD/WORKTREE. Уверенность высокая; current baseline, отсутствие доказанного healthy baseline исключает утверждение «новая регрессия».

Шаги: создать Event черновиком через кабинет; открыть его в admin; загрузить главное фото → «Сохранить и продолжить» → reload; нажать видимую кнопку «Удалить» под главным фото → сохранить → reload. Ожидание: в черновике удаляется главное фото, UI и сохранённое значение согласованы. Факт: `photo-clear` остаётся unchecked, preview и сохранённое фото остаются прежними. Сервер сообщает успешное сохранение. P2: заявленное редактирование медиа не работает; без доказанной потери других данных.

Доказательства: [точный before/selected/after DOM](../photo-clear-probe.result.txt), [после клика](../screenshots/draft-photo-clear-before-submit-ru-1440.png), [после reload](../screenshots/draft-photo-clear-after-reload-ru-1440.png), [серверное сохранённое фото Event 3](../server-final.json). Фото/галерея созданы в собственном media; Event переходы только через UI.

Первопричина подтверждена: `static/admin/js/kidsmap_admin_form_shell.js:1144` ищет `mainInput.id + '-clear'` (`id_photo-clear`); настоящий Django checkbox имеет `id='photo-clear_id'`, `name='photo-clear'`. `clearMainPhoto()` не отмечает отсутствующий в lookup checkbox и возвращает старое preview. Другие lookup того же id есть около строк 2335. Это shared JS: размер влияния на другие редакторы требует отдельной проверки, в этом запуске подтверждён только EventAdmin.

Область: shared admin media handler + Event form/preview integration, сохранение/reload, правильная готовность при действительно отправленном удалении. Владелец: frontend-admin, Django review для публикационного gate. Зависимости: стандартный ClearableFileInput и шаблон media_section; не заменять существующие assertions. Отдельный эксперимент `media.js` ожидал отказ удаления фото опубликованного события, но кнопка вообще не отправила удаление: публикационный gate этим экспериментом НЕ проверен, вывод об обходе gate не сделан.

## Самостоятельный промпт на исправление

```text
Исправь EVENT-QA-02 по docs/qa/module04-2026-10-10-r1/findings/EVENT-QA-02.md в KidsMap. Прочитай AGENTS.md/.agents, сохрани чужие изменения/active_run/стенды. Scope: штатная кнопка удаления главного фото EventAdmin и её shared handler, честное preview/readiness и серверное сохранение; не менять правила публикации или schema. Сначала составь конкретный implementation-план по каноническим правилам.
Свежая причина: JS ищет id_photo-clear, а реальный checkbox name=photo-clear имеет id photo-clear_id. Проверь все соответствующие lookup, стандартные widgets и shared consumers. Привяжи handler к действительному контролу без хрупкой догадки об id. Черновик должен после клика/сохранения/reload действительно иметь пустое фото; отмена выбора/замена должны работать. Для опубликованного события отдельно проверь настоящий серверный контракт удаления обязательного фото и честную ошибку/готовность; прежний audit не доказал gate bypass.
Добавь содержательную регрессионную проверку roundtrip, не меняй существующие assertions ради green. На новом изолированном DJANGO_TESTING=1 стенде с вымышленными данными пройди UI upload→save→reload→delete→save→reload и replace, проверь публичную карточку, RU/AZ/EN и mobile/PC, shared consumers по impact analysis. Сохрани свежие доказательства и точные counts/exits. Без production, commit/push/deploy. При обязательном отдельном согласовании плана предъяви его до implementation.
```
