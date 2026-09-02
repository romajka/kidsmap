# Задача: починить проверку качества карточек места

Репозиторий KidsMap (Django, без сборщика фронтенда). Проблема воспроизводится на
**проде**: при добавлении и публикации мест админка выдаёт невнятные ошибки, часть
опубликованных карточек не видна на сайте без каких-либо объяснений.

Всё описанное ниже — дефекты кода, они не зависят от данных и воспроизводятся в любой среде.

---

## Контекст: три несогласованные системы проверки

| Система | Файл | Что решает |
|---|---|---|
| `place_quality_check()` | `src/catalog/services/content_quality.py:153` | бейдж в админке, гейт кнопки «Опубликовать» |
| `public_place_queryset()` | `src/catalog/services/content_quality.py:43` | что реально попадает в каталог, на карту, в sitemap |
| `validate_place_card()` | `src/catalog/services/place_card_validation.py:87` | только CLI-отчёт `manage.py validate_places`, ни на что не влияет |

Первые две расходятся по правилам — отсюда все симптомы. Третью в этой задаче не трогаем.

Коды ошибок у `place_quality_check`: `missing_name`, `missing_category`,
`description_too_short`, `test_content`, `missing_contact`, `missing_address`,
`missing_coordinates`, `missing_age`, `missing_price`, `missing_schedule`, `missing_photo`.

---

## Дефект 1 — сырой код ошибки вместо текста

**Где:** `src/catalog/domain_admin/place.py:54`, словарь `PLACE_QUALITY_ERROR_LABELS`.

В словаре **нет ключа `missing_coordinates`**, а `place_quality_error_labels()`
(`place.py:86`) при промахе возвращает сам код:

```python
return ", ".join(str(PLACE_QUALITY_ERROR_LABELS.get(error, error)) for error in errors)
```

Пользователь на проде видит буквально:

```
Карточка сохранена, но не опубликована: missing_coordinates.
```

**Что сделать.** Не добавлять ключ в этот словарь, а **устранить дублирование** —
см. дефект 4. Если делать по частям, то минимальный шаг: добавить
`"missing_coordinates": _("не указана точка на карте")`.

**Критерий приёмки:** ни один код из списка выше не может попасть в UI сырым.
Добавить тест, который проходит по всем кодам `place_quality_check` и проверяет,
что для каждого есть подпись.

---

## Дефект 2 — кнопка «Опубликовать» отправляет карточку в черновик

**Где:** `src/catalog/domain_admin/place.py:3227`, `_handle_publish_submit`.

```python
quality = place_quality_check(obj)
if not quality.is_ready:
    obj.status = Place.STATUS_DRAFT
    obj.is_active = False
    obj.save(update_fields=["status", "is_active", "updated_at"])
    self.message_user(request, _("Карточка сохранена, но не опубликована: %(reasons)s.") % ..., level=messages.WARNING)
```

Статус понижается **безусловно**, в том числе для карточки, которая уже была
опубликована. Пользователь нажимает «Опубликовать» после мелкой правки — карточка
молча исчезает с сайта. Формулировка «сохранена, но не опубликована» этого не сообщает.

**Что сделать.**
- Если карточка **не была** опубликована — оставить текущее поведение (в черновик), но
  сообщение должно перечислять все проблемы (см. дефект 3).
- Если карточка **была** опубликована (`status == PUBLISHED and is_active` до сохранения) —
  не понижать статус молча. Либо оставить как есть и предупредить, либо снять с публикации,
  но написать прямо: «Карточка снята с публикации: …».
- Решение о том, какой из двух вариантов, — за владельцем продукта; по умолчанию выбрать
  «не понижать, предупредить», как менее разрушительный.

**Критерий приёмки:** тест, где опубликованная карточка с испорченным качеством
проходит через `_handle_publish_submit` и не теряет `status=published` молча.

---

## Дефект 3 — список проблем обрезан в двух местах

**Где:**
- `src/catalog/domain_admin/place.py:2700` — `visible_issues = issue_labels[:2]` в `publication_readiness`
- `src/catalog/domain_admin/place.py:2548` — `place_quality_error_labels(check.errors[:4])` в `quality_status_display`

Пользователь видит 2 пункта из N (или 4 из N), остальные не показаны нигде. Это прямая
причина жалобы «написано, что не проходит, но что и где — не сказано».

**Что сделать.** Показывать полный список. Если мешает вёрстка колонки — выводить все
пункты в `title`/тултипе, а в самой колонке оставить счётчик. Сообщение
`message_user` в `_handle_publish_submit` должно содержать **все** причины без обрезки.

---

## Дефект 4 — два словаря подписей для одних и тех же кодов

**Где:**
- админ: `src/catalog/domain_admin/place.py:54` — `PLACE_QUALITY_ERROR_LABELS`, 10 кодов, короткие фразы
- владелец: `src/catalog/controllers/owner_places_controller.py:118` — `_quality_issue_labels`, 11 кодов, развёрнутые формулировки

Владелец на том же наборе ошибок видит:

```
Перед отправкой на проверку исправьте: Точка на карте: выберите точку вручную
или проверьте адрес и обновите координаты.
```

Админ на той же карточке видит `missing_coordinates`.

**Что сделать.** Один источник правды. Перенести словарь подписей в
`src/catalog/services/content_quality.py` рядом с `place_quality_check` (или в новый
`catalog/services/place_quality_labels.py`) и переиспользовать его в обоих местах.
Привязку кодов к полям формы (`_add_quality_errors_to_form`,
`owner_places_controller.py:141`) оставить на стороне владельца — она специфична для формы.

**Критерий приёмки:** в кодовой базе остаётся ровно одно место, где код ошибки
превращается в человеческий текст.

---

## Дефект 5 — бейдж «Опубликовано» не знает про фильтр каталога

**Где:** `src/catalog/models/place.py:482` (`Place.is_public`) против
`src/catalog/services/content_quality.py:43` (`public_place_queryset`).

```python
@property
def is_public(self) -> bool:
    return self.is_active and self.status == self.STATUS_PUBLISHED and not self.is_deleted
```

А видимость на сайте требует дополнительно: непустые `category` и `address`; расписание
(`schedule` или `schedule_days`); хотя бы один контакт; возраст; цену **в старых полях**;
описание ≥ 120 символов; отсутствие junk-токенов; и не-временное мероприятие, если
`is_events_section_enabled()` выключен.

Из-за этого карточка может иметь бейдж «Опубликовано» и отсутствовать на сайте — без
единого сообщения. Отдельный подслучай: временные мероприятия при выключенном разделе
мероприятий исчезают из каталога, а админка про флаг не знает.

**Что сделать.** В `_place_visibility_state` (`place.py:2065`) сверяться не только с
`place_quality_check`, но и с фактическим попаданием в `public_place_queryset`, и когда
карточка выпадает — писать конкретную причину, включая «раздел мероприятий выключен».

**Критерий приёмки:** для любой карточки бейдж в админке совпадает с реальной видимостью
на сайте, а при расхождении показывает причину.

---

## Дефект 6 — цена из тарифов не считается ценой для каталога

**Где:** `src/catalog/services/content_quality.py` — `_has_price_q()` (строка 30) смотрит
только `price_from`, `price_to`, `price_per_lesson`, `price_per_month`, `price_per_8_lessons`.
А `place_quality_check` (строка ~215) дополнительно принимает `pricing_plans`.

Карточка, у которой цена задана **только тарифами**, проходит проверку качества и не
попадает в каталог.

**Что сделать.** Согласовать: либо `_has_price_q()` учитывает наличие активного тарифа с
ценой (через `pricing_plan_records`), либо `place_quality_check` перестаёт принимать
тарифы как цену. Первое предпочтительнее — тарифы это актуальная модель цены.

---

## Дефект 7 — фильтр «мусорных» данных ловит настоящие телефоны

**Где:** `src/catalog/services/content_quality.py:71-89`.

```python
junk_fields = ("name", "name_ru", "name_az", "name_en", "description_ru",
               "description_az", "description_en", "schedule", "address",
               "phone1", "instagram", "website")
for token in ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty"):
    token_filter |= Q(**{f"{field}__icontains": token})
```

`icontains` **без границ слова**. Номер `+994501234567` содержит подстроку `123456` →
карточка вырезается из каталога, карты и sitemap.

При этом `place_quality_check` использует `contains_test_content()`
(`content_quality.py:19`) с regex **с** `\b`, поэтому телефон он не забраковывает.
Итог: админка говорит «Опубликовано», сайта карточки не показывает, сообщения нет нигде.

**Что сделать.**
- Убрать `phone1`, `instagram`, `website` из `junk_fields` — цифры номера и части URL не
  являются признаком тестовых данных.
- Для остальных полей перейти на ту же проверку с границами слова, что и
  `contains_test_content()`, чтобы SQL-фильтр и `place_quality_check` не расходились.
- Аналогичный `icontains`-цикл есть в `public_review_filter()` (`content_quality.py:121`) —
  проверить его теми же глазами, там комментарий явно объясняет, почему выбран `icontains`
  (несовместимость `\b` между PostgreSQL и SQLite). Решение должно работать на обеих СУБД:
  например, сравнивать по нормализованному значению или вынести проверку в Python там, где
  это допустимо по производительности.

**Масштаб на проде неизвестен** — измерить скриптом ниже. Локально так выпал 21 номер.

---

## Диагностика перед началом и после

Read-only скрипт, ничего не пишет в базу. Запускать на проде:

```bash
python manage.py shell < diagnose_visibility.py
```

Скрипт печатает: сколько карточек имеет статус «опубликовано» против того, сколько реально
видно в каталоге; разбивку причин выпадения с примерами id; ложные срабатывания
junk-фильтра по полям; списки расхождений «админка ↔ сайт» в обе стороны; коды ошибок без
человеческой подписи.

Исходник скрипта — в конце этого файла (Приложение A). Сохранить его в корень проекта.

Проверить, не пострадали ли недавно добавленные карточки от дефекта 2:

```bash
python manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from catalog.models import Place
from catalog.services.content_quality import place_quality_check
qs = Place.objects.filter(created_at__gte=timezone.now()-timedelta(days=7), deleted_at__isnull=True).order_by('-created_at')
print('Добавлено за 7 дней:', qs.count())
for p in qs:
    print(f'#{p.pk} {p.created_at:%d.%m %H:%M} status={p.status} active={p.is_active} ошибки={\",\".join(place_quality_check(p).errors) or \"нет\"}')
"
```

Карточки в `draft` — следы молчаливого понижения статуса.

---

## Порядок работ

1. **Дефект 7** — `content_quality.py`. Даёт немедленный эффект: карточки возвращаются на сайт.
2. **Дефект 1 + 4** — единый словарь подписей. Убирает «непонятную ошибку».
3. **Дефект 3** — показывать все проблемы.
4. **Дефект 2** — прекратить молчаливое снятие с публикации.
5. **Дефекты 5 и 6** — свести правила админки и каталога.

---

## Ограничения

- **Не менять** модели и не добавлять миграции: все дефекты чинятся в сервисах, админке и
  контроллерах.
- **Переводы**: каталоги `locale/{ru,az,en}/LC_MESSAGES/django.po` в этом проекте правятся
  **вручную**. `manage.py makemessages` переформатирует весь файл и даёт диф на ~35 000 строк —
  не запускать. Новые строки дописывать блоками `#: <ref>` / `msgid` / `msgstr` в конец файла,
  затем `manage.py compilemessages -l az -l en -l ru`.
  Две ловушки: запись с флагом `#, fuzzy` **молча пропускается** msgfmt (на странице появится
  русский msgid); устаревшая запись `#~ msgid` считается дубликатом, если такой же msgid
  добавить заново — старый `#~`-блок надо удалить. В `ru.po` `msgstr` равен `msgid`.
- **Русское склонение**: в `.po` стоит `nplurals=2`, поэтому `{% blocktrans count %}` не даёт
  третью форму. Использовать фильтр с `pgettext`-контекстами по образцу `review_count`
  и `tariff_count` в `src/catalog/templatetags/catalog_i18n.py`.
- **Тесты**: `python manage.py test catalog`. На момент написания в suite есть
  **10 предсуществующих падений**, не связанных с этой задачей (5× `TestAdminOwnershipModerationUX`,
  2× `TestAdminSidebarStructure`, 1× `TestAdminTemporaryEventInputs`, 1× `TestOwnerPlaceManagementAndPermissions`,
  1× `CatalogMapQueryEfficiencyTests`). Они воспроизводятся на чистом `HEAD` — сверяться с ними
  как с базовой линией, а не пытаться чинить в рамках этой задачи.
- **Внимание:** файлы `src/catalog/domain_admin/place.py` и
  `src/catalog/controllers/owner_places_controller.py` недавно правились параллельно другой
  работой по i18n. Перед началом сделать `git status` и убедиться, что рабочее дерево
  стабильно.

---

## Приложение A — diagnose_visibility.py

```python
"""Read-only: why published places are missing from the public catalog."""

from collections import Counter

from django.db.models.functions import Length

from catalog.models import Place
from catalog.services.content_quality import place_quality_check, public_place_queryset
from catalog.services.features import is_events_section_enabled

JUNK_FIELDS = (
    "name", "name_ru", "name_az", "name_en",
    "description_ru", "description_az", "description_en",
    "schedule", "address", "phone1", "instagram", "website",
)
JUNK_TOKENS = ("aaa", "aaaa", "aaaaa", "test", "lorem", "123456", "qwerty")

published = Place.objects.filter(is_active=True, deleted_at__isnull=True, status="published")
in_catalog = set(public_place_queryset(Place.objects.all()).values_list("id", flat=True))

print("=" * 64)
print(f"Статус «опубликовано» + активна : {published.count()}")
print(f"Реально видны в каталоге        : {len(in_catalog & set(published.values_list('id', flat=True)))}")
print(f"Раздел мероприятий включён      : {is_events_section_enabled()}")
print("=" * 64)

reasons, junk_hits, examples = Counter(), Counter(), {}

for place in published.annotate(
    dr=Length("description_ru"), da=Length("description_az"), de=Length("description_en")
).prefetch_related("schedule_days"):
    if place.id in in_catalog:
        continue
    why = []
    if not place.category_id:
        why.append("нет категории")
    if not place.address:
        why.append("нет адреса")
    if not (place.schedule or place.schedule_days.exists()):
        why.append("нет расписания")
    if not (place.phone1 or place.instagram or place.website):
        why.append("нет контакта")
    if place.age_from is None and place.age_to is None:
        why.append("нет возраста")
    if all(v is None for v in (place.price_from, place.price_to, place.price_per_lesson,
                               place.price_per_month, place.price_per_8_lessons)):
        why.append("нет цены в старых полях (тарифы тут НЕ считаются)")
    if max(place.dr or 0, place.da or 0, place.de or 0) < 120:
        why.append("описание короче 120 символов")
    if place.is_temporary and not is_events_section_enabled():
        why.append("временное мероприятие, раздел выключен")
    for token in JUNK_TOKENS:
        for field in JUNK_FIELDS:
            if token in (getattr(place, field, "") or "").lower():
                why.append(f"«мусорный» токен {token!r} в поле {field}")
                junk_hits[f"{token} в {field}"] += 1
    if not why:
        why.append("причина не определена — проверить вручную")
    for item in why:
        reasons[item] += 1
        examples.setdefault(item, []).append(place.pk)

print("\nПОЧЕМУ КАРТОЧКИ НЕ ВИДНЫ (у одной карточки может быть несколько причин):\n")
for reason, count in reasons.most_common():
    print(f"  {count:>4}  {reason}")
    print(f"        примеры: {', '.join(f'#{pk}' for pk in examples[reason][:8])}")

if junk_hits:
    print("\nЛОЖНЫЕ СРАБАТЫВАНИЯ ФИЛЬТРА «ТЕСТОВЫХ ДАННЫХ»:\n")
    for key, count in junk_hits.most_common():
        print(f"  {count:>4}  {key}")

print("\nРАСХОЖДЕНИЯ АДМИНКА ↔ САЙТ:\n")
ready_hidden, shown_unready = [], []
for place in published:
    check = place_quality_check(place)
    if check.is_ready and place.id not in in_catalog:
        ready_hidden.append(place.pk)
    if not check.is_ready and place.id in in_catalog:
        shown_unready.append((place.pk, ",".join(check.errors)))
print(f"  Админка «Готово/Опубликовано», а на сайте НЕТ : {len(ready_hidden)}")
print(f"        {', '.join(f'#{pk}' for pk in ready_hidden[:12])}")
print(f"  Админка «Нужна доработка», а на сайте ЕСТЬ    : {len(shown_unready)}")
for pk, errs in shown_unready[:12]:
    print(f"        #{pk}: {errs}")

print("\nКОДЫ БЕЗ ЧЕЛОВЕЧЕСКОЙ ПОДПИСИ В АДМИНКЕ:\n")
from catalog.domain_admin.place import PLACE_QUALITY_ERROR_LABELS

seen = Counter()
for place in Place.objects.filter(deleted_at__isnull=True):
    for code in place_quality_check(place).errors:
        if code not in PLACE_QUALITY_ERROR_LABELS:
            seen[code] += 1
for code, count in seen.most_common():
    print(f"  {count:>4}  {code}  ← показывается пользователю сырым кодом")
if not seen:
    print("  нет")
```
