# Локальное завершение заполнения KidsMap

Scope разрешён пользователем 2026-10-07: продолжить оставшиеся локальные исправления и итоговую приёмку. HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`; начальный dirty WORKTREE сохранён отдельным hash manifest. Без commit/push/deploy, production и реальных данных. Один исполнитель, последовательно.

## Исправления

1. **PP-01:** воспроизвести потерю candidate photo через OwnerPlaceEditForm→save_form; проецировать сохранённый кандидат для bound edit также, не брать photo из POST path. Явные clear/новый upload сохраняют прежнюю семантику; stale source/candidate по-прежнему отклоняется до записи.
2. **PP-02:** старый review adapter передаёт nature/operating_state и server-stored nested pricing в действующий readiness. Обработка решений продолжает использовать publication.review; не ослаблять его ACL, версию или обязательность цены.
3. **PP-03:** дать сохранённым файлам candidate галереи стабильные локальные ключи, производные от server-stored image names; не выдумывать PlacePhoto ID. Включить их в существующие delete/order controls и allowlist validation. Новые upload `new:N`, опубликованные `saved:ID`, candidate `candidate:hash` различаются; revision token защищает от устаревшего набора. Удаление live фото и новый порядок применяются после прежней модерации, файлы на диске не чистить.
4. **ACE-21:** добавить original updated_at token Event admin; в atomic POST заблокировать и проверить свежую запись до save_model/save_related/publication. Stale форму показать с сохранённым вводом. Add-form без версии допустима, edit без исходного token отклоняется. Не менять организатора, snapshot/date/publication/permissions.
5. **PP-04 / ORG-VIS-01:** точечные переводы старых admin labels; использовать уже имеющийся bundled Material Symbols font вместо внешнего CDN. Без замены библиотеки иконок или redesign.
6. **ACE-09/10:** свежий public GET подтвердил пустой текст RU/EN при существующем AZ описании/биографии. Общий helper отображения возвращает текст/фактический язык/fallback, сохраняет приоритет существующего RU fallback специалиста. Методы отображения Event/Specialist и public templates используют его; при fallback видна подпись исходного языка и lang attribute. Переводы/поля БД автоматически не создаются. Проверить образование и опыт с тем же подходом.

Основные файлы: forms.py, publication_forms.py, photo_gallery.py, volunteer_places.py, EventAdmin в domain_admin/place.py; existing owner photo/continuous includes и JS, Event admin template; scoped locales/base footer, методы представления Event/Specialist и public text includes. Добавить отдельный regression module. Поля моделей, constraints и схема данных не меняются.

## Проверка и итог

- Содержательные RED→GREEN: draft/save/reload/submit сохраняют photo; clear/upload; candidate gallery reorder/delete/add/limits/foreign keys/stale; group-only price и public-space contact exemption; Event stale POST не пишет parent/inlines/publication.
- Изолированный localhost:8788, собственные PostgreSQL/socket/cache/media/private media, вымышленные роли. Targeted suites последовательно; затем полный локальный suite с точным отчётом об оставшихся baseline failures.
- Реальный браузер: места, организация без филиалов и подключение 10 готовых мест, мероприятия очно/онлайн, специалист/места приёма. Черновик/refresh/recovery/errors/submit/review/public/edit. Подтверждённые чужие права, документы, переключатели публичных разделов и конфликт вкладок.
- RU/AZ/EN, 360/390/768/1024/1280/1440, keyboard/focus/overflow. Скриншоты PC/mobile и таблица PASS/FAIL/NOT RUN для реально выполненных сценариев; external integrations/реальные devices/screen readers отдельно.
- Сохранить прежние отчёты как историю; новый итоговый отчёт и актуальный статус остатка. Проверить HEAD/source hash и отсутствие изменений вне разрешённых путей, освободить свой active_run.

7. Свежая проверка ACE-06/07: передавать координаты площадки без локализации и подставлять город/район через существующее init_location_fields. Правила выбора площадки и серверная проверка не меняются.

8. ACE-11 воспроизведён на свежих данных: каталог специалиста использует Place.district_i18n для строкового района площадки. Уточнить существующие тестовые payload нового токена и явного отображения исходного языка, не ослабляя проверки.

9. Свежая проверка: пустые координаты площадки должны передаваться пустыми строками, а не `None`. Регион и точка для мероприятия остаются необязательными; новых требований и предупреждения об обязательном регионе нет.

### Подтверждение общей галереи админки — 2026-10-08

Первый новый файл попадал в отрисованную Django empty_form с именем `__prefix__` вне HTML template и не сохранялся. Исключить служебную форму из списка реальных строк; сохранить единственный шаблон создания новых строк. Дать существующему маркеру перемещения фокус и клавиши стрелок, сохраняя штатный порядок inline formset. Публикация, лимиты, файлы и права не меняются. RED: серверный HTMLParser-тест и реальная загрузка двух фото (сохранялось одно).

10. Админка места после сохранения gallery candidate отрисовывала live PlacePhoto вместо редакции. Сформировать строки candidate из сохранённого server payload как unsaved extra forms без fake IDs, передавать исходную строку адаптеру сохранения; удаление/порядок/новые файлы меняют только candidate. Проверить запрет присланного чужого ID/изменённого management form, публикацию после обычной проверки.
11. Browser matrix: specialist admin загружал штатный Django change_form.js без обязательного script ID; добавить стандартный django-admin-form-add-constants. Ошибка JS воспроизведена на add/edit, 36 сочетаний. Прав и полей не менять.

12. Админский observer тарифов наблюдал собственную безусловную запись hidden, что при бесплатном/событийном режиме создавало microtask loop и блокировало браузер. Делать запись hidden только при реальном изменении. Проверка: браузер остаётся отзывчивым после смены режима и операций галереи; серверные правила цены не меняются.

13. Свежий PC-скриншот: длинные названия разделов specialist admin обрезаются из-за nowrap/overflow:hidden, а legacy mobile CSS на 901–1024 конфликтует с двухколоночной entry-навигацией. Внутри specialist form на ширине от901 сделать боковой список вертикальным и переносить текст; мобильный select до900 сохранить. Проверка полного текста, клавиатуры и RU/AZ/EN × шесть ширин. Только scoped CSS, бизнес-правила не меняются.
