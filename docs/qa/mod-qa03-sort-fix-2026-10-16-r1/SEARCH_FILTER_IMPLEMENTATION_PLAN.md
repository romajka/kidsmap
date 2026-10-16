# PLAN: сохранить фильтры при отправке поиска — approval pending

Новая причина вне одобренного SORT scope. Приложение для этой причины не изменено. Исторический MOD-QA ID не присваивается.

## Подтверждение и причина

`native-matrix-interrupted-ru.json`: Event RU360, native ввод SORTQA→Enter после открытия `?status__exact=published` убирает status до выбора sort. Это отдельный trigger; сортировка из комбинированного q+status URL проверяется отдельно. Старые FAIL сохранены; нельзя объявлять эту причину исправленной по GREEN сортировки.

Общая панель `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html:242` использует Jazzmin `admin_extra_filters`. Установленный Jazzmin (`.venv/lib/python3.12/site-packages/jazzmin/templatetags/jazzmin.py:260`) исключает из hidden inputs все `used_parameters` видимых list_filter. Для самостоятельной поисковой формы это убирает status и прочие фильтры: в её submit нет расположенной отдельно формы фильтров. Vendor не меняем.

## Точный предлагаемый scope — 3 файла

1. `src/catalog/templatetags/admin_dashboard_tags.py`: новый локальный template tag, возвращающий пары hidden query параметров из уже принятого ChangeList.filter_params, кроме q и pagination/error flag. Сохранить повторяющиеся значения, sort и действующие штатные фильтры; штатное HTML escaping. Не собирать ORM lookup из текста и не менять queryset/permissions.
2. `src/catalog/templates/admin/catalog/includes/km_changelist_search_panel.html`: заменить admin_extra_filters/items на пары нового tag в одном цикле hidden inputs. Текущие input q/toolbar/labels/JS/CSS не менять. Shared consumers: Place/Event/Specialist — проверить все три.
3. NEW `src/catalog/testcases/test_admin_queue_search_state.py`: meaningful regression до patch через реальные admin GET и разбор hidden inputs с HTMLParser, последующий GET как form submit. q+status+sort, повторяющийся поддержанный фильтр, reset pagination, escaping, ACL и неизменность доменных данных. Не ослаблять existing assertions.

## Выполнение после отдельного approval

- Fresh isolated DJANGO_TESTING=1 профиль/текущие RU/AZ/EN MO/source snapshot; чужие изменения сохраняются.
- Fresh RED на форме Event/Specialist и recheck Place. Приложение исправлять только после воспроизведения.
- Минимальный patch, targeted GREEN; только затронутые общие search/sort/permissions сценарии.
- Native search→sort→pager→reload→reset на трёх очередях, RU/AZ/EN×360/390/768/1024/1280/1440, sidebar где фон доступен; статус и другие параметры сверять по URL и реальным ID строк. Проверить empty/error cases, keyboard/focus, console/network, PNG.
- Полные CSS/menu/module08 наборы не повторять; полный08 только после завершения всех задач. Колонки/MOD04–08/production/commit/push/deploy не входят в этот scope.

Этот PLAN не является approval или результатом проверки.
