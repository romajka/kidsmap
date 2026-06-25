# Карта иконок каталога KidsMap

В проекте фактически не подключена библиотека Font Awesome (её нет в `base.html` и `site.css`). Однако в проекте локально присутствуют SVG-иконки библиотеки **coolicons** (в `static/img/icon/cooliocns SVG/`), которые используются через CSS `mask-image` (например, в `events_landing.html`). 

Для реализации единой системы иконок мы будем использовать `mask-image` с SVG-файлами, чтобы цвет наследовался через `currentColor` (управлялся CSS-классами: hover, active).

## Основные категории

| Code | RU | AZ | EN | Иконка (Путь) | Источник | Комментарий |
| ---- | -- | -- | -- | ------------- | -------- | ----------- |
| `early-development` | Раннее развитие | Erkən inkişaf | Early dev. | `icons/categories/early-development.svg` | **Свой SVG** | Кубики с буквами / росток (стиль outline 24x24) |
| `EDU` | Образование | Təhsil | Education | `img/icon/cooliocns SVG/Interface/Book_Open.svg` | coolicons | Открытая книга |
| `SPRT` | Спорт | İdman | Sports | `icons/categories/sports.svg` | **Свой SVG** | Медаль на ленте (стиль outline) |
| `dance` | Танцы | Rəqs | Dance | `icons/categories/dance.svg` | **Свой SVG** | Танцующая фигура |
| `MUS` | Музыка и сцена | Musiqi və səhnə | Music & stage | `icons/categories/music.svg` | **Свой SVG** | Театральные маски или нота |
| `TECH` | Технологии | Texnologiya | Technology | `img/icon/cooliocns SVG/System/Code.svg` | coolicons | Символ кода `< >` |
| `ART` | Творчество | Yaradıcılıq | Creativity | `img/icon/cooliocns SVG/Edit/Swatches_Palette.svg` | coolicons | Палитра |
| `intellect-skills` | Интеллект и навыки | İntellekt və bac. | Intellect & skills | `img/icon/cooliocns SVG/Environment/Puzzle.svg` | coolicons | Пазл |
| `development-support` | Развитие и поддержка | İnkişaf və dəstək | Dev. & support | `img/icon/cooliocns SVG/Interface/Heart_01.svg` | coolicons | Сердце (поддержка) |
| `FUN` | Развлечения и досуг | Əyləncə və asudə | Entertainment | `img/icon/cooliocns SVG/Interface/Ticket_Voucher.svg` | coolicons | Билет |
| `CAMP` | Лагеря | Düşərgələr | Camps | `icons/categories/camp.svg` | **Свой SVG** | Палатка |

## Подкатегории (Группы для переиспользования)

*Подкатегории пока не имеют поля `icon` в модели `Subcategory`. Согласно задаче, не добавляем поле, если оно не нужно в интерфейсе. Но если потребуется, маппинг будет следующим:*

* **Языки** (Azərbaycan dili, Rus dili, İngilis dili): Общая иконка диалога (`coolicons/Communication/Chat_Circle.svg`)
* **Единоборства** (Cüdo, Karate, Boks, Güləş): Общая иконка перчатки или пояса.
* **Лагеря (разные сезоны)**: Общая иконка `icons/categories/camp.svg`.
* **Музыкальные инструменты** (Piano, Guitar, Violin): Общая иконка ноты или гитары.
* **IT и программирование** (Robotics, Game Dev, Web): Иконка `Code.svg`.

## Что отсутствует в текущей библиотеке
В coolicons нет специфических иконок: медаль (спорт), палатка (лагерь), танцующий человек (танцы), театральные маски/специфичная нота (музыка).
Они будут созданы вручную в едином стиле (viewBox 0 0 24 24, stroke-width: 2, fill: none) и сохранены в `static/icons/categories/`.

## План обновления
Вместо хранения `fas fa-graduation-cap` мы будем хранить в поле `Category.icon` пути к SVG-файлам относительно папки `static/`.
В шаблонах иконки будут рендериться как:
```html
<div class="category-icon" aria-hidden="true" style="mask-image: url('{% static category.icon %}'); -webkit-mask-image: url('{% static category.icon %}');"></div>
```
Это позволит гибко менять цвет через `background-color` в CSS (состояния hover, active).
