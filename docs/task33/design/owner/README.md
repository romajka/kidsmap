# Owner макеты · owner-02-r1

Этап 02, PROTOTYPES ONLY. **awaiting_user_review**. Это синтетические HTML-макеты с интеракциями в памяти вкладки: не backend, не приложение и не production. Сохранение, saved_at, продолжение на другом устройстве, загрузка фото, модерация и письма только демонстрируются. При перезагрузке ввод исчезает. Нет API/fetch, localStorage или настоящей отправки.

Откройте [стартовую страницу](index.html) в браузере прямо из checkout. Все assets локальные; сохранение структуры checkout необходимо. JavaScript должен быть включён. Можно открыть через обычный локальный static preview; Django не нужен. В шапке — AZ/RU/EN, внизу каждого экрана — «Сценарии макета» для состояния и длинного текста.

| Экран | HTML | 390 px RU | 1280 px RU |
|---|---|---|---|
| Форма самостоятельного центра | [place](place.html?lang=ru) | [снимок](screenshots/place-ru-390.png) | [снимок](screenshots/place-ru-1280.png) |
| Парк без организации и занятия | [park](place.html?lang=ru&sample=park) | [снимок](screenshots/place-park-ru-390.png) | [снимок](screenshots/place-park-ru-1280.png) |
| Создание организации | [organization](organization.html?lang=ru) | [снимок](screenshots/organization-ru-390.png) | [снимок](screenshots/organization-ru-1280.png) |
| Кабинет без мест | [empty](cabinet.html?lang=ru&sample=empty) | [снимок](screenshots/cabinet-empty-ru-390.png) | [снимок](screenshots/cabinet-empty-ru-1280.png) |
| Организация без филиалов | [zero branches](cabinet.html?lang=ru&sample=org-empty) | [снимок](screenshots/cabinet-org-empty-ru-390.png) | [снимок](screenshots/cabinet-org-empty-ru-1280.png) |
| Сеть и список филиалов | [cabinet](cabinet.html?lang=ru&sample=network) | [снимок](screenshots/cabinet-ru-390.png) | [снимок](screenshots/cabinet-ru-1280.png) |
| Общая программа и влияние | [program](program.html?lang=ru) | [снимок](screenshots/program-ru-390.png) | [снимок](screenshots/program-ru-1280.png) |
| Группы филиала | [groups](groups.html?lang=ru) | [снимок](screenshots/groups-ru-390.png) | [снимок](screenshots/groups-ru-1280.png) |
| Приглашение сотрудника | [team](team.html?lang=ru) | [снимок](screenshots/team-ru-390.png) | [снимок](screenshots/team-ru-1280.png) |

## Состояния формы

[empty](place.html?state=empty), [draft](place.html?state=draft), [saving](place.html?state=saving), [save-failed](place.html?state=save-failed), [browser-only](place.html?state=browser-only), [pending](place.html?state=pending), [rejected](place.html?state=rejected), [conflict](place.html?state=conflict), [published + pending](place.html?sample=network&state=published-pending). Для каждого состояния есть снимки `screenshots/place-<state>-ru-{390,1280}.png`.

- Секции формы видны одновременно; навигация переносит focus к заголовку. Нет обязательного «Далее», организации, дополнительных занятий, переводов и фото.
- Черновик можно сохранить с пустыми полями. Отправка на проверку показывает связанные с полями ошибки. При ошибке и конфликте ввод остаётся; сравнение не перезаписывает его. Выбор своего варианта требует отдельного сохранения.
- Публикация отделена от сохранения черновика. Для live-карточки одобренная публичная версия остаётся видимой во время autosave/проверки/отклонения правок. `published=1` показывает live-версию вместе с любым состоянием редакции.
- Контакты: общие используются при пустых местных; source явно подписан. Прекращение связи не копирует телефон и не скрывает место автоматически.
- Общий текст программы распространяется после одобрения; локальные группы, расписание и цены остаются. Group metadata/условия показывают проверку; только сумма и текстовое расписание — немедленное применение после explicit save.
- Права команды: owner-only приглашение; отдельные Org/Program/branch-create действия; selected current branches не включает будущие, all_network включает. Преподаватель синтетический, личных документов нет. Бизнес не модерирует чужие отзывы.
- Названия, `.example.test` адреса сайтов, email, адреса и учитель вымышлены. `long=1` — stress fixture для текста текущего языка, не полноценный перевод AZ-карточки. RU/EN карточка с AZ fallback подписана.

## Повторить проверку

`verify.cjs` — самостоятельный browser automation script, не application test suite. Нужна установленная Playwright library; поиск существующей cached 1.55.0 автоматический. При другой установке укажите `OWNER_PLAYWRIGHT_MODULE=/absolute/path/to/playwright`. Новый framework в приложение не добавлялся.

Из корня checkout:

```bash
node --check docs/task33/design/owner/copy.js
node --check docs/task33/design/owner/prototype.js
node --check docs/task33/design/owner/verify.cjs
DJANGO_TESTING=1 node docs/task33/design/owner/verify.cjs
```

По умолчанию используется `file://`. Для loopback static preview можно задать `OWNER_BASE_URL=http://127.0.0.1:8762/docs/task33/design/owner/`. Результат — [verification.json](verification.json), снимки 390/1280. Реальная матрица: AZ/RU/EN × 320/360/390/768/1024/1280/1440 с long text, 11 экранов/вариантов и девять статусов формы. Проверяются overflow, labels, дубли ID, focus/Tab/Escape, ошибки, retry/conflict, контакты, группы, scope команды, фото, console/resource failures и отсутствие внешних запросов.

[Отчёт этапа](../../reports/02.md), [независимый review](../../reports/02-review.md), [приёмка](../acceptance.md). User acceptance записывается только после явного ответа с revision и набором экранов.
