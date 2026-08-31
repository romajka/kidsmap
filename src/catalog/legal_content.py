from __future__ import annotations

from contextvars import ContextVar

from django.conf import settings


DEFAULT_LEGAL_CONTACT_EMAIL = "noreply@kidsmap.az"
_legal_contact_email: ContextVar[str] = ContextVar(
    "legal_contact_email", default=DEFAULT_LEGAL_CONTACT_EMAIL
)


def paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def bullets(*items: str) -> dict:
    return {"type": "bullets", "items": list(items)}


def email_block(label: str) -> dict:
    return {"type": "email", "label": label, "email": _legal_contact_email.get()}


def _current_legal_contact_email() -> str:
    """Use the public contact address configured in the admin panel."""
    from .models import SiteSettings

    configured_email = (SiteSettings.get_solo().footer_email or "").strip()
    return configured_email or DEFAULT_LEGAL_CONTACT_EMAIL


def section(section_id: str, title: str, *content: dict, children: list[dict] | None = None) -> dict:
    return {
        "id": section_id,
        "title": title,
        "content": list(content),
        "children": children or [],
    }


def sub_section(section_id: str, title: str, *content: dict) -> dict:
    return {
        "id": section_id,
        "title": title,
        "content": list(content),
    }


def _privacy_sections_ru(*, analytics_enabled: bool, maps_enabled: bool) -> list[dict]:
    analytics_text = (
        "На сайте в текущей конфигурации подключён Google Analytics, поэтому при загрузке страниц и выполнении поддерживаемых событий могут обрабатываться аналитические идентификаторы и технические данные браузера."
        if analytics_enabled
        else "На сайте используются собственные события аналитики внутри приложения. Внешний Google Analytics в текущей конфигурации не подключён."
    )
    maps_text = (
        "При открытии карт и инструментов выбора координат сайт может загружать Google Maps, а Google как поставщик картографического сервиса может получать технические данные, необходимые для показа карты."
        if maps_enabled
        else "Сайт поддерживает интеграцию с картографическим сервисом, но внешний провайдер карт подключается только если соответствующий ключ конфигурации включён."
    )
    return [
        section(
            "general",
            "1. Общие положения",
            paragraph(
                "Настоящая Политика конфиденциальности описывает, как KidsMap обрабатывает информацию пользователей сайта https://kidsmap.az, включая языковые версии сайта, формы, каталог, карточки мест, события, отзывы, личные кабинеты и связанные функции."
            ),
            paragraph(
                "Используя сайт, пользователь подтверждает, что ознакомился с настоящей Политикой. Если для отдельной обработки требуется отдельное согласие, такое согласие запрашивается отдельно."
            ),
            paragraph(
                "Само посещение сайта не считается согласием на те виды обработки, для которых по закону требуется отдельное волеизъявление."
            ),
            email_block("По вопросам обработки, исправления или удаления данных пользователь может обратиться по адресу:"),
        ),
        section(
            "purpose",
            "2. Назначение KidsMap",
            paragraph(
                "KidsMap является информационной платформой и каталогом детских кружков, секций, курсов, образовательных организаций, специалистов и временных мероприятий."
            ),
            bullets(
                "искать организации и мероприятия;",
                "применять фильтры и просматривать карточки;",
                "сохранять избранные места;",
                "публиковать отзывы и оценки;",
                "связываться с организациями;",
                "подавать заявки на управление карточками;",
                "создавать и редактировать карточки при наличии соответствующих прав;",
            ),
            paragraph(
                "Если прямо не указано иное, KidsMap не является организатором размещённых кружков и мероприятий, не оказывает соответствующие услуги от имени организаций и не гарантирует наличие мест, неизменность цен, расписания или условий."
            ),
        ),
        section(
            "user-categories",
            "3. Категории пользователей",
            paragraph("Функциями сайта могут пользоваться незарегистрированные посетители, зарегистрированные пользователи, родители и законные представители детей, владельцы и представители организаций, участники команд карточек, модераторы и администраторы."),
            paragraph("Сайт в первую очередь рассчитан на совершеннолетних пользователей."),
            paragraph("Дети не должны самостоятельно передавать персональные данные через сайт без участия родителя или законного представителя."),
        ),
        section(
            "data-categories",
            "4. Какие данные могут обрабатываться",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Технические данные посетителя",
                    paragraph("При использовании сайта могут автоматически обрабатываться технические сведения, необходимые для работы сервиса, статистики и безопасности."),
                    bullets(
                        "идентификаторы сессии и cookies;",
                        "дата и время обращения;",
                        "посещённые пути и страницы;",
                        "язык интерфейса;",
                        "технические данные, связанные с действиями пользователя на сайте;",
                        "приблизительное местоположение, если оно определяется картографическим сервисом или разрешено пользователем через браузер;",
                    ),
                    paragraph("В коде приложения KidsMap сохраняются посещения по сессии и события воронки, связанные с поиском, фильтрами, открытием карточек, кликами по контактам, избранным, отзывам и ownership-flow."),
                ),
                sub_section(
                    "account-data",
                    "4.2. Данные аккаунта",
                    bullets(
                        "username;",
                        "имя и фамилия, если пользователь их указал;",
                        "email;",
                        "номер телефона, если он запрашивается и был введён;",
                        "пароль в хешированном виде;",
                        "язык интерфейса;",
                        "статус подтверждения email;",
                        "роль пользователя и связанные права доступа;",
                        "даты создания и обновления связанных записей аккаунта;",
                    ),
                    paragraph("KidsMap не хранит пароль пользователя в открытом виде."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. Пользовательская активность",
                    bullets(
                        "избранные карточки;",
                        "отзывы и оценки;",
                        "лайки и дизлайки к отзывам;",
                        "история некоторых действий внутри каталога и owner-flow;",
                        "отправленные формы и обращения, необходимые для работы функций сайта;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Данные владельцев организаций",
                    bullets(
                        "имя, фамилия и username;",
                        "email и телефон, если они указаны;",
                        "сведения из ownership-заявки;",
                        "связь с организацией и роль в команде;",
                        "история рассмотрения заявки;",
                        "приглашения и роли в owner-команде;",
                        "аудит пользовательских и административных действий, связанных с карточками;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Данные организаций и мероприятий",
                    bullets(
                        "название и описание;",
                        "категория, возраст, цены и расписание;",
                        "адрес, район, метро и координаты;",
                        "телефон, email, сайт и ссылки на соцсети;",
                        "фотографии, логотипы и сведения о сотрудниках;",
                        "данные мероприятий и временных активностей;",
                    ),
                    paragraph("Часть этих сведений может относиться к физическим лицам и в таком случае рассматривается как персональная информация."),
                ),
            ],
        ),
        section(
            "children",
            "5. Информация о детях",
            paragraph("KidsMap не ставит своей целью прямой сбор персональных данных детей."),
            bullets(
                "полное имя ребёнка без необходимости;",
                "личный телефон, email или домашний адрес ребёнка;",
                "документы, сведения о здоровье или инвалидности;",
                "точное расписание перемещений;",
                "данные школы или класса в сочетании с идентифицирующей информацией;",
            ),
            paragraph("Фотографии и видеоматериалы с изображением детей могут размещаться только лицом, имеющим необходимые права и разрешения."),
            paragraph("При получении обоснованной жалобы администрация KidsMap вправе скрыть или удалить фотографию либо другую информацию о ребёнке."),
            email_block("Для обращения об удалении данных или изображения ребёнка используйте:"),
        ),
        section(
            "processing-purposes",
            "6. Цели обработки данных",
            bullets(
                "предоставление доступа к сайту и аккаунту;",
                "аутентификация и подтверждение email;",
                "обеспечение работы каталога, карты, отзывов и избранного;",
                "модерация контента и owner-flow;",
                "обработка ownership-заявок и управление командами владельцев;",
                "связь с пользователями и отправка сервисных уведомлений;",
                "обеспечение безопасности, предотвращение спама и злоупотреблений;",
                "ведение технической статистики, аналитики и журналов действий;",
                "улучшение интерфейса, исправление ошибок и защита прав пользователей, KidsMap и третьих лиц;",
            ),
        ),
        section(
            "legal-basis",
            "7. Основания обработки",
            bullets(
                "согласие пользователя, когда оно требуется;",
                "предоставление запрошенных пользователем функций;",
                "исполнение пользовательского соглашения и действия по запросу пользователя;",
                "соблюдение требований законодательства;",
                "защита безопасности сайта и предотвращение злоупотреблений;",
                "защита прав и законных интересов пользователей и третьих лиц;",
            ),
            paragraph("Если обработка основана на согласии, пользователь вправе отозвать его, однако это не отменяет законность обработки, выполненной до отзыва."),
        ),
        section(
            "cookies",
            "8. Cookies и локальное хранение",
            paragraph("Сайт использует cookies и аналогичные механизмы, необходимые для работы сессий, защиты форм, выбора языка и корректной работы функций аккаунта."),
            bullets(
                "обязательные cookies сессии и авторизации;",
                "cookies или значения, связанные с CSRF-защитой форм;",
                "cookies и локальные данные, связанные с языком интерфейса и настройками сессии;",
            ),
            paragraph(analytics_text),
            paragraph("Отключение обязательных cookies может привести к неправильной работе отдельных функций сайта."),
        ),
        section(
            "analytics",
            "9. Аналитика",
            paragraph("KidsMap ведёт внутреннюю продуктовую аналитику, достаточную для оценки использования каталога и основных пользовательских сценариев."),
            bullets(
                "фиксируются посещения по сессии в модели SiteVisit;",
                "сохраняются FunnelEvent для поиска, фильтров, открытия карточек, кликов по контактам, избранного, отзывов и owner-flow;",
                "во временной очереди сессии могут храниться аналитические события для последующей отправки на фронтенд;",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Карты и геолокация",
            paragraph("KidsMap использует координаты мест и поддерживает отображение карт, фильтрацию по районам и инструменты выбора точки для owner-форм."),
            paragraph(maps_text),
            paragraph("Браузерная геолокация может запрашиваться только через стандартный механизм браузера и только при разрешении пользователя."),
            paragraph("Отказ в доступе к геолокации не блокирует основные функции каталога, кроме сценариев, где пользователь сам хочет определить текущую точку."),
        ),
        section(
            "email",
            "11. Email и сервисные сообщения",
            bullets(
                "подтверждение регистрации и отправка OTP-кода на email;",
                "повторная отправка и проверка кода подтверждения;",
                "уведомления безопасности и ответы поддержки;",
                "сообщения, связанные с модерацией, ownership-заявками и owner-team приглашениями;",
                "письма для восстановления доступа средствами Django auth;",
            ),
            paragraph("Сервисные сообщения, необходимые для работы аккаунта и безопасности, отличаются от рекламных рассылок."),
        ),
        section(
            "reviews-content",
            "12. Отзывы, оценки и публичный контент",
            paragraph("Отзывы, оценки, имя пользователя или указанное имя автора, а также иной опубликованный контент могут быть доступны другим посетителям сайта."),
            bullets(
                "нельзя размещать персональные данные третьих лиц без законного основания;",
                "нельзя размещать сведения о детях без разрешения;",
                "нельзя публиковать незаконный, ложный, оскорбительный или спам-контент;",
            ),
            paragraph("KidsMap вправе модерировать, скрывать, отклонять или удалять материалы, нарушающие правила сайта или требования законодательства."),
        ),
        section(
            "owner-responsibility",
            "13. Ответственность владельцев карточек",
            bullets(
                "достоверность информации в карточке;",
                "актуальность адреса, цен, расписания и контактов;",
                "законность использования фотографий, логотипов и описаний;",
                "наличие прав на публикацию данных сотрудников и изображений детей;",
            ),
            paragraph("KidsMap вправе запросить подтверждение полномочий, временно скрыть карточку, отклонить изменения или ограничить права пользователя при злоупотреблении."),
        ),
        section(
            "third-parties",
            "14. Передача данных третьим лицам",
            paragraph("Данные могут передаваться только в объёме, необходимом для соответствующей цели."),
            bullets(
                "хостинг- и инфраструктурным поставщикам;",
                "поставщикам email-сервисов для доставки сервисных писем;",
                "поставщику картографического сервиса при использовании карт;",
                "поставщику аналитического сервиса, если он включён в текущей конфигурации;",
                "компетентным государственным органам при наличии законного требования;",
            ),
            paragraph("KidsMap не продаёт персональные данные пользователей."),
        ),
        section(
            "external-links",
            "15. Ссылки на сторонние ресурсы",
            paragraph("Карточки и страницы сайта могут содержать ссылки на внешние ресурсы, включая сайты организаций, соцсети и картографические сервисы."),
            paragraph("После перехода на сторонний ресурс обработка информации регулируется правилами соответствующего сервиса, которые KidsMap не контролирует."),
        ),
        section(
            "cross-border",
            "16. Трансграничная обработка",
            paragraph("Некоторые технические поставщики могут находиться или хранить данные за пределами Азербайджанской Республики."),
            paragraph("При использовании таких сервисов KidsMap учитывает применимые требования к трансграничной передаче данных в той мере, в какой это требуется действующим законодательством."),
        ),
        section(
            "retention",
            "17. Сроки хранения",
            paragraph("Информация хранится не дольше, чем это необходимо для целей обработки, если более длительный срок не требуется законодательством, безопасностью или разрешением спора."),
            paragraph("В проекте не установлена единая публичная таблица точных сроков хранения для всех категорий данных."),
            bullets(
                "данные активного аккаунта могут храниться, пока аккаунт используется или пока не поступит обоснованный запрос на удаление;",
                "часть информации может временно сохраняться в резервных копиях, журналах безопасности и audit history;",
                "после прекращения оснований для хранения данные удаляются, обезличиваются или блокируются в разумный срок по доступной технической модели проекта;",
            ),
        ),
        section(
            "security",
            "18. Защита информации",
            bullets(
                "разграничение прав доступа и роли пользователей;",
                "аутентификация и подтверждение email;",
                "хеширование паролей средствами Django;",
                "CSRF-защита форм и сессионные механизмы безопасности;",
                "административное и предметное журналирование отдельных действий;",
                "модерация пользовательского контента;",
                "ограничение доступа к административным разделам и инфраструктуре;",
            ),
            paragraph("Ни один способ хранения или передачи информации не обеспечивает абсолютную безопасность."),
        ),
        section(
            "incidents",
            "19. Инциденты безопасности",
            paragraph("При обнаружении утечки, неправомерного доступа или иного инцидента администрация KidsMap принимает разумные меры для ограничения последствий, устранения причины, документирования инцидента и выполнения обязательных уведомлений, если они требуются законодательством."),
        ),
        section(
            "rights",
            "20. Права пользователя",
            bullets(
                "узнать, обрабатываются ли его данные;",
                "получить информацию о целях и категориях обработки;",
                "потребовать исправления или обновления неточных данных;",
                "потребовать прекращения неправомерной обработки;",
                "отозвать ранее предоставленное согласие, когда оно применимо;",
                "потребовать удаления данных при наличии оснований;",
                "обжаловать действия, связанные с обработкой данных;",
            ),
            email_block("Для направления запроса используйте:"),
        ),
        section(
            "requests",
            "21. Порядок направления запроса",
            bullets(
                "имя и email, связанный с аккаунтом;",
                "username, если он есть;",
                "суть запроса;",
                "ссылку на карточку, отзыв, фотографию или другой материал;",
                "любые сведения, помогающие найти нужные данные;",
            ),
            paragraph("Для защиты информации администрация вправе запросить разумное подтверждение личности или полномочий заявителя."),
        ),
        section(
            "account-deletion",
            "22. Удаление аккаунта и данных",
            paragraph("В текущей реализации сайта нет отдельной публичной кнопки полного удаления аккаунта. Запрос на удаление аккаунта и связанных с ним данных направляется по email."),
            email_block("Запросы на удаление аккаунта и данных принимаются по адресу:"),
            paragraph("Удаление может включать прекращение доступа, удаление или обезличивание части данных профиля и необязательной активности, если это совместимо с архитектурой проекта и не нарушает целостность ownership, moderation и audit history."),
        ),
        section(
            "correction",
            "23. Исправление данных",
            paragraph("Пользователь может самостоятельно изменить часть доступных данных в личном кабинете и owner-разделах, а также направить запрос на исправление по email."),
            paragraph("Изменения в карточках мест и событий могут проходить модерацию до публичного отображения."),
        ),
        section(
            "materials-removal",
            "24. Удаление фотографий и материалов",
            paragraph("Лицо, считающее, что фотография, описание, отзыв или иной материал нарушает его права либо права ребёнка, может направить обращение на email KidsMap."),
            email_block("Для жалоб на материалы и запросов на удаление используйте:"),
            paragraph("На время проверки спорный материал может быть временно скрыт."),
        ),
        section(
            "marketing",
            "25. Маркетинговые сообщения",
            paragraph("Маркетинговые сообщения могут направляться только при наличии отдельного согласия или иного допустимого основания."),
            paragraph("На момент публикации этой Политики маркетинговые рассылки не являются основной реализованной функцией сайта, а сервисные письма используются прежде всего для аккаунта, безопасности и moderation/owner-flow."),
        ),
        section(
            "policy-changes",
            "26. Изменение Политики",
            paragraph("Политика может обновляться при изменении законодательства, функций сайта, подключении новых сервисов или изменении способов обработки данных."),
            paragraph("Актуальная версия публикуется на этой странице. Дата последнего обновления указывается в начале документа."),
        ),
        section(
            "law",
            "27. Применимое право",
            paragraph("Настоящая Политика применяется с учётом законодательства Азербайджанской Республики."),
            paragraph("Пользователь вправе обратиться в компетентный государственный орган или суд в порядке, установленном применимым законодательством."),
        ),
        section(
            "contacts",
            "28. Контакты",
            paragraph("По вопросам конфиденциальности, исправления информации, удаления аккаунта, отзыва согласия, удаления фотографий, жалоб на контент и безопасности аккаунта обращайтесь:"),
            email_block("Контактный email KidsMap:"),
        ),
    ]


def _privacy_sections_az(*, analytics_enabled: bool, maps_enabled: bool) -> list[dict]:
    analytics_text = (
        "Saytın cari konfiqurasiyasında Google Analytics qoşulub. Buna görə səhifələr açıldıqda və dəstəklənən hadisələr baş verdikdə analitik identifikatorlar və brauzerin texniki məlumatları emal oluna bilər."
        if analytics_enabled
        else "Saytda tətbiqin öz daxili analitika hadisələri istifadə olunur. Cari konfiqurasiyada xarici Google Analytics qoşulmayıb."
    )
    maps_text = (
        "Xəritələr və koordinat seçimi alətləri açıldıqda sayt Google Maps yükləyə bilər və xəritə xidməti təchizatçısı olaraq Google xəritənin göstərilməsi üçün zəruri texniki məlumatları ala bilər."
        if maps_enabled
        else "Sayt xəritə xidməti inteqrasiyasını dəstəkləyir, lakin xarici xəritə təchizatçısı yalnız müvafiq konfiqurasiya açarı aktiv olduqda qoşulur."
    )
    return [
        section(
            "general",
            "1. Ümumi müddəalar",
            paragraph("Bu Məxfilik siyasəti KidsMap saytında https://kidsmap.az istifadəçi məlumatlarının necə toplanmasını, istifadəsini, saxlanmasını, ötürülməsini və qorunmasını təsvir edir. Siyasət saytın dil versiyalarına, formalara, kataloqa, məkan kartlarına, tədbirlərə, rəylərə, şəxsi kabinetlərə və əlaqəli funksiyalara şamil olunur."),
            paragraph("Saytdan istifadə etməklə istifadəçi bu Siyasətlə tanış olduğunu təsdiq edir. Ayrı razılıq tələb olunan emal növləri üçün həmin razılıq ayrıca soruşulur."),
            paragraph("Sayta sadəcə daxil olmaq ayrıca iradə ifadəsi tələb olunan emal üçün razılıq hesab edilmir."),
            email_block("Məlumatların emalı, düzəldilməsi və ya silinməsi ilə bağlı müraciətlər üçün:"),
        ),
        section(
            "purpose",
            "2. KidsMap-in təyinatı",
            paragraph("KidsMap uşaq dərnəkləri, idman bölmələri, kurslar, təhsil təşkilatları, mütəxəssislər və müvəqqəti tədbirlər üçün məlumat platforması və kataloqdur."),
            bullets(
                "təşkilat və tədbirləri axtarmaq;",
                "filtrlərdən istifadə etmək və kartlara baxmaq;",
                "seçilmiş məkanları saxlamaq;",
                "rəy və qiymət dərc etmək;",
                "təşkilatlarla əlaqə yaratmaq;",
                "kartın idarə olunması üçün müraciət göndərmək;",
                "müvafiq hüquqlar olduqda kart yaratmaq və redaktə etmək;",
            ),
            paragraph("Ayrıca göstərilmədikdə KidsMap yerləşdirilmiş dərnək və tədbirlərin təşkilatçısı deyil, həmin təşkilatların adından xidmət göstərmir və yerlərin mövcudluğunu, qiymətlərin, cədvəllərin və şərtlərin dəyişməzliyini zəmanət vermir."),
        ),
        section(
            "user-categories",
            "3. İstifadəçi kateqoriyaları",
            paragraph("Sayt funksiyalarından qeydiyyatsız ziyarətçilər, qeydiyyatdan keçmiş istifadəçilər, valideynlər və qanuni nümayəndələr, təşkilat sahibləri və nümayəndələri, kart komandalarının iştirakçıları, moderatorlar və administratorlar istifadə edə bilər."),
            paragraph("Sayt ilk növbədə yetkin istifadəçilər üçün nəzərdə tutulub."),
            paragraph("Uşaqlar valideyn və ya qanuni nümayəndənin iştirakı olmadan sayt vasitəsilə şəxsi məlumat göndərməməlidirlər."),
        ),
        section(
            "data-categories",
            "4. Hansı məlumatlar emal oluna bilər",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Ziyarətçinin texniki məlumatları",
                    paragraph("Saytdan istifadə zamanı xidmətin işi, statistika və təhlükəsizlik üçün zəruri texniki məlumatlar avtomatik emal oluna bilər."),
                    bullets(
                        "sessiya identifikatorları və cookies;",
                        "müraciətin tarixi və vaxtı;",
                        "baxılan səhifələr və yollar;",
                        "interfeys dili;",
                        "saytda istifadəçi hərəkətləri ilə bağlı texniki məlumatlar;",
                        "xəritə xidməti və ya brauzer icazəsi ilə müəyyən edilən təxmini geolokasiya;",
                    ),
                    paragraph("KidsMap tətbiq kodunda sessiya üzrə ziyarətlər və axtarış, filtrlər, kart açılması, kontakt klikləri, seçilmişlər, rəylər və ownership-flow ilə bağlı funnel hadisələri saxlanılır."),
                ),
                sub_section(
                    "account-data",
                    "4.2. Hesab məlumatları",
                    bullets(
                        "username;",
                        "istifadəçi daxil edibsə ad və soyad;",
                        "email;",
                        "istənildiyi və daxil edildiyi halda telefon nömrəsi;",
                        "xəşlənmiş formada parol;",
                        "interfeys dili;",
                        "email təsdiqi statusu;",
                        "istifadəçi rolu və giriş hüquqları;",
                        "hesabla bağlı yazıların yaradılma və yenilənmə tarixləri;",
                    ),
                    paragraph("KidsMap parolu açıq mətndə saxlamır."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. İstifadəçi aktivliyi",
                    bullets(
                        "seçilmiş kartlar;",
                        "rəylər və qiymətlər;",
                        "rəylərə like və dislike reaksiyaları;",
                        "kataloq və owner-flow daxilində bəzi hərəkətlərin tarixçəsi;",
                        "sayt funksiyalarının işləməsi üçün göndərilmiş formalar və müraciətlər;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Təşkilat sahiblərinin məlumatları",
                    bullets(
                        "ad, soyad və username;",
                        "göstərildiyi halda email və telefon;",
                        "ownership müraciətindəki məlumatlar;",
                        "təşkilatla əlaqə və komandadakı rol;",
                        "müraciətə baxılma tarixçəsi;",
                        "dəvətlər və owner komandasında rollar;",
                        "kartlarla bağlı istifadəçi və inzibati hərəkətlərin auditi;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Təşkilat və tədbir məlumatları",
                    bullets(
                        "ad və təsvir;",
                        "kateqoriya, yaş, qiymət və cədvəl;",
                        "ünvan, rayon, metro və koordinatlar;",
                        "telefon, email, sayt və sosial şəbəkə keçidləri;",
                        "fotolar, loqolar və əməkdaşlar haqqında məlumat;",
                        "tədbir və müvəqqəti aktivlik məlumatları;",
                    ),
                    paragraph("Bu məlumatların bir hissəsi fiziki şəxslərə aid ola bilər və belə halda şəxsi məlumat kimi qiymətləndirilir."),
                ),
            ],
        ),
        section(
            "children",
            "5. Uşaqlar haqqında məlumat",
            paragraph("KidsMap uşaqların şəxsi məlumatlarını birbaşa toplamağı məqsəd qoymur."),
            bullets(
                "uşağın tam adı;",
                "uşağın şəxsi telefon nömrəsi, emaili və ya ev ünvanı;",
                "sənədlər, sağlamlıq və ya əlillik barədə məlumatlar;",
                "dəqiq hərəkət marşrutları;",
                "məktəb və ya sinif barədə identifikasiyaedici məlumatlarla birlikdə verilən məlumatlar;",
            ),
            paragraph("Uşaqların təsviri olan foto və videolar yalnız müvafiq hüquq və icazəsi olan şəxs tərəfindən yerləşdirilə bilər."),
            paragraph("Əsaslı şikayət olduqda KidsMap uşağa aid foto və ya digər məlumatı gizlətmək və ya silmək hüququna malikdir."),
            email_block("Uşağa aid məlumat və ya şəkilin silinməsi üçün müraciət:"),
        ),
        section(
            "processing-purposes",
            "6. Məlumatların emal məqsədləri",
            bullets(
                "sayta və hesaba giriş vermək;",
                "autentifikasiya və email təsdiqi;",
                "kataloq, xəritə, rəylər və seçilmişlər funksiyalarını işlətmək;",
                "kontentin moderasiyası və owner-flow;",
                "ownership müraciətlərini emal etmək və owner komandalarını idarə etmək;",
                "istifadəçilərlə əlaqə saxlamaq və servis bildirişləri göndərmək;",
                "təhlükəsizliyi təmin etmək, spam və sui-istifadənin qarşısını almaq;",
                "texniki statistika, analitika və jurnal qeydləri aparmaq;",
                "interfeysi yaxşılaşdırmaq, səhvləri aradan qaldırmaq və istifadəçilərin, KidsMap-in və üçüncü şəxslərin hüquqlarını qorumaq;",
            ),
        ),
        section(
            "legal-basis",
            "7. Emal əsasları",
            bullets(
                "tələb olunduqda istifadəçi razılığı;",
                "istifadəçinin soruşduğu funksiyaların təqdim edilməsi;",
                "istifadəçi razılaşmasının icrası və istifadəçi sorğusuna uyğun hərəkətlər;",
                "qanunvericiliyin tələblərinə əməl etmək;",
                "sayt təhlükəsizliyini qorumaq və sui-istifadənin qarşısını almaq;",
                "istifadəçilərin və üçüncü şəxslərin hüquq və qanuni maraqlarını qorumaq;",
            ),
            paragraph("Emal razılığa əsaslanırsa, istifadəçi həmin razılığı geri götürə bilər, lakin bu, geri götürülmədən əvvəl aparılmış emalın qanuniliyini ləğv etmir."),
        ),
        section(
            "cookies",
            "8. Cookies və lokal saxlanma",
            paragraph("Sayt sessiyaların işləməsi, formaların qorunması, dil seçimi və hesab funksiyalarının düzgün işi üçün zəruri cookies və oxşar mexanizmlərdən istifadə edir."),
            bullets(
                "sessiya və autentifikasiya cookies-ləri;",
                "formaların CSRF qorunması ilə bağlı cookies və dəyərlər;",
                "interfeys dili və sessiya ayarları ilə bağlı cookies və lokal məlumatlar;",
            ),
            paragraph(analytics_text),
            paragraph("Məcburi cookies-lərin söndürülməsi saytın bəzi funksiyalarının düzgün işləməməsinə səbəb ola bilər."),
        ),
        section(
            "analytics",
            "9. Analitika",
            paragraph("KidsMap kataloq və əsas istifadəçi ssenarilərinin istifadəsini qiymətləndirmək üçün daxili məhsul analitikasından istifadə edir."),
            bullets(
                "SiteVisit modelində sessiya üzrə ziyarətlər qeydə alınır;",
                "axtarış, filtr, kart açılması, kontakt klikləri, seçilmişlər, rəylər və owner-flow üçün FunnelEvent qeydləri saxlanılır;",
                "bəzi analitik hadisələr frontendə ötürülməzdən əvvəl sessiyada müvəqqəti saxlanıla bilər;",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Xəritələr və geolokasiya",
            paragraph("KidsMap məkan koordinatlarından istifadə edir və xəritələrin göstərilməsi, rayon üzrə filtrasiya və owner formalarında nöqtə seçimi alətlərini dəstəkləyir."),
            paragraph(maps_text),
            paragraph("Brauzer geolokasiyası yalnız brauzerin standart icazə mexanizmi ilə və istifadəçi razılığı olduqda soruşulur."),
            paragraph("Geolokasiyadan imtina kataloqun əsas funksiyalarını bloklamır; yalnız istifadəçinin cari nöqtəni müəyyən etmək istədiyi ssenarilərə təsir edə bilər."),
        ),
        section(
            "email",
            "11. Email və servis mesajları",
            bullets(
                "qeydiyyatın təsdiqi və email OTP kodunun göndərilməsi;",
                "kodun təkrar göndərilməsi və yoxlanması;",
                "təhlükəsizlik bildirişləri və dəstək cavabları;",
                "moderasiya, ownership müraciətləri və owner-team dəvətləri ilə bağlı mesajlar;",
                "Django auth vasitəsilə parol bərpası məktubları;",
            ),
            paragraph("Hesab və təhlükəsizlik üçün zəruri servis mesajları reklam məktublarından fərqlənir."),
        ),
        section(
            "reviews-content",
            "12. Rəylər, qiymətlər və açıq kontent",
            paragraph("Rəylər, qiymətlər, istifadəçi adı və ya göstərilmiş müəllif adı, eləcə də dərc edilmiş digər kontent başqa ziyarətçilərə görünə bilər."),
            bullets(
                "üçüncü şəxslərin şəxsi məlumatlarını qanuni əsas olmadan yerləşdirmək olmaz;",
                "uşaqlara aid məlumatlar icazəsiz yerləşdirilməməlidir;",
                "qanunsuz, yalan, təhqiramiz və ya spam kontent yerləşdirilməməlidir;",
            ),
            paragraph("KidsMap sayt qaydalarını və ya qanunvericiliyi pozan materialları moderasiya etmək, gizlətmək, rədd etmək və silmək hüququna malikdir."),
        ),
        section(
            "owner-responsibility",
            "13. Kart sahiblərinin məsuliyyəti",
            bullets(
                "kartdakı məlumatların düzgünlüyü;",
                "ünvanın, qiymətlərin, cədvəlin və kontaktların aktuallığı;",
                "foto, loqo və təsvirlərdən qanuni istifadə;",
                "əməkdaş məlumatlarının və uşaq şəkillərinin dərcinə dair hüquqların olması;",
            ),
            paragraph("KidsMap səlahiyyət təsdiqi tələb edə, kartı müvəqqəti gizlədə, dəyişiklikləri rədd edə və ya sui-istifadə zamanı istifadəçi hüquqlarını məhdudlaşdıra bilər."),
        ),
        section(
            "third-parties",
            "14. Məlumatların üçüncü şəxslərə ötürülməsi",
            paragraph("Məlumatlar yalnız müvafiq məqsəd üçün zəruri həcmdə ötürülə bilər."),
            bullets(
                "hostinq və infrastruktur təchizatçılarına;",
                "servis məktublarının çatdırılması üçün email xidmətlərinə;",
                "xəritələrdən istifadə zamanı xəritə xidməti təchizatçısına;",
                "cari konfiqurasiyada aktivdirsə analitika xidməti təchizatçısına;",
                "qanuni tələb olduqda səlahiyyətli dövlət orqanlarına;",
            ),
            paragraph("KidsMap istifadəçilərin şəxsi məlumatlarını satmır."),
        ),
        section(
            "external-links",
            "15. Üçüncü tərəf keçidləri",
            paragraph("Kartlar və sayt səhifələri təşkilat saytlarına, sosial şəbəkələrə və xəritə xidmətlərinə keçidlər ehtiva edə bilər."),
            paragraph("Üçüncü tərəf resursuna keçiddən sonra məlumatların emalı həmin xidmətin qaydaları ilə tənzimlənir və KidsMap buna nəzarət etmir."),
        ),
        section(
            "cross-border",
            "16. Sərhədlərarası emal",
            paragraph("Bəzi texniki təchizatçılar Azərbaycan Respublikasından kənarda yerləşə və ya məlumatları orada saxlaya bilər."),
            paragraph("Belə xidmətlərdən istifadə olunduqda KidsMap tətbiq olunan qanunvericiliyin tələb etdiyi həcmdə sərhədlərarası ötürmə qaydalarını nəzərə alır."),
        ),
        section(
            "retention",
            "17. Saxlanma müddətləri",
            paragraph("Məlumatlar emal məqsədləri üçün lazım olduğu müddətdən artıq saxlanılmır, əgər daha uzun müddət qanunvericilik, təhlükəsizlik və ya mübahisənin həlli üçün tələb olunmursa."),
            paragraph("Layihədə bütün məlumat kateqoriyaları üzrə vahid dəqiq açıq saxlanma cədvəli müəyyən edilməyib."),
            bullets(
                "aktiv hesab məlumatları hesab istifadə olunduğu müddətdə və ya əsaslı silmə sorğusu alınana qədər saxlanıla bilər;",
                "bəzi məlumatlar ehtiyat nüsxələrdə, təhlükəsizlik jurnallarında və audit tarixçəsində müvəqqəti qala bilər;",
                "saxlanma əsası bitdikdən sonra məlumatlar layihənin texniki imkanlarına uyğun olaraq silinir, anonimləşdirilir və ya bloklanır;",
            ),
        ),
        section(
            "security",
            "18. Məlumatların qorunması",
            bullets(
                "giriş hüquqlarının bölgüsü və istifadəçi rolları;",
                "autentifikasiya və email təsdiqi;",
                "Django vasitəsilə parolların xəşlənməsi;",
                "formaların CSRF qorunması və sessiya təhlükəsizlik mexanizmləri;",
                "bəzi hərəkətlərin inzibati və predmet auditi;",
                "istifadəçi kontentinin moderasiyası;",
                "inzibati bölmələrə və infrastruktura girişin məhdudlaşdırılması;",
            ),
            paragraph("Heç bir saxlanma və ya ötürmə üsulu mütləq təhlükəsizlik təmin etmir."),
        ),
        section(
            "incidents",
            "19. Təhlükəsizlik insidentləri",
            paragraph("Sızma, icazəsiz giriş və ya digər insident aşkarlandıqda KidsMap nəticələri məhdudlaşdırmaq, səbəbi aradan qaldırmaq, insidenti sənədləşdirmək və qanun tələb edirsə zəruri bildirişləri yerinə yetirmək üçün ağlabatan tədbirlər görür."),
        ),
        section(
            "rights",
            "20. İstifadəçi hüquqları",
            bullets(
                "məlumatlarının emal olunub-olunmadığını öyrənmək;",
                "emal məqsədləri və kateqoriyaları barədə məlumat almaq;",
                "dəqiq olmayan məlumatların düzəldilməsini və yenilənməsini tələb etmək;",
                "qanunsuz emalın dayandırılmasını tələb etmək;",
                "tətbiq olunarsa əvvəl verilmiş razılığı geri götürmək;",
                "əsas olduqda məlumatların silinməsini tələb etmək;",
                "emalla bağlı hərəkətlərdən şikayət vermək;",
            ),
            email_block("Sorğular üçün istifadə edin:"),
        ),
        section(
            "requests",
            "21. Sorğunun göndərilməsi qaydası",
            bullets(
                "ad və hesabla bağlı email;",
                "varsa username;",
                "sorğunun mahiyyəti;",
                "kart, rəy, foto və ya digər materiala keçid;",
                "məlumatı tapmağa kömək edən əlavə izahlar;",
            ),
            paragraph("Məlumatların qorunması üçün administrasiya şəxsiyyətin və ya səlahiyyətin ağlabatan təsdiqini tələb edə bilər."),
        ),
        section(
            "account-deletion",
            "22. Hesabın və məlumatların silinməsi",
            paragraph("Cari realizasiyada hesabın tam silinməsi üçün ayrıca açıq düymə yoxdur. Hesabın və əlaqəli məlumatların silinməsi sorğusu email vasitəsilə göndərilir."),
            email_block("Hesab və məlumatların silinməsi sorğuları üçün:"),
            paragraph("Silinmə girişin dayandırılmasını və profil məlumatlarının, eləcə də bəzi qeyri-məcburi aktivliyin silinməsi və ya anonimləşdirilməsini əhatə edə bilər; bu, layihənin arxitekturası və ownership, moderation və audit history bütövlüyü ilə uyğun olmalıdır."),
        ),
        section(
            "correction",
            "23. Məlumatların düzəldilməsi",
            paragraph("İstifadəçi şəxsi kabinetdə və owner bölmələrində əlçatan olan bəzi məlumatları özü dəyişə bilər, həmçinin düzəliş sorğusunu email ilə göndərə bilər."),
            paragraph("Məkan və tədbir kartlarındakı dəyişikliklər ictimai görünüşdən əvvəl moderasiyadan keçə bilər."),
        ),
        section(
            "materials-removal",
            "24. Foto və materialların silinməsi",
            paragraph("Şəkil, təsvir, rəy və ya digər materialın hüquqlarını və ya uşağın maraqlarını pozduğunu hesab edən şəxs KidsMap emailinə müraciət edə bilər."),
            email_block("Materialların silinməsi və şikayətlər üçün:"),
            paragraph("Yoxlama müddətində mübahisəli material müvəqqəti gizlədilə bilər."),
        ),
        section(
            "marketing",
            "25. Marketinq mesajları",
            paragraph("Marketinq mesajları yalnız ayrıca razılıq və ya digər qanuni əsas olduqda göndərilə bilər."),
            paragraph("Bu Siyasətin dərc olunduğu anda marketinq göndərişləri saytın əsas reallaşdırılmış funksiyası deyil; email əsasən hesab, təhlükəsizlik və moderation/owner-flow üçün istifadə olunur."),
        ),
        section(
            "policy-changes",
            "26. Siyasətin dəyişdirilməsi",
            paragraph("Qanunvericilikdə, sayt funksiyalarında, yeni xidmətlərin qoşulmasında və ya məlumat emalı üsullarında dəyişiklik olduqda bu Siyasət yenilənə bilər."),
            paragraph("Aktual versiya bu səhifədə yerləşdirilir. Son yenilənmə tarixi sənədin əvvəlində göstərilir."),
        ),
        section(
            "law",
            "27. Tətbiq olunan hüquq",
            paragraph("Bu Siyasət Azərbaycan Respublikasının qanunvericiliyi nəzərə alınmaqla tətbiq edilir."),
            paragraph("İstifadəçi tətbiq olunan qanunvericiliyə uyğun qaydada səlahiyyətli dövlət orqanına və ya məhkəməyə müraciət edə bilər."),
        ),
        section(
            "contacts",
            "28. Əlaqə",
            paragraph("Məxfilik, məlumatların düzəldilməsi, hesabın silinməsi, razılığın geri götürülməsi, foto və materialların silinməsi, kontent şikayətləri və hesab təhlükəsizliyi ilə bağlı müraciətlər üçün:"),
            email_block("KidsMap əlaqə emaili:"),
        ),
    ]


def _privacy_sections_en(*, analytics_enabled: bool, maps_enabled: bool) -> list[dict]:
    analytics_text = (
        "Google Analytics is enabled in the current site configuration, so analytics identifiers and browser technical data may be processed when pages load and supported events are triggered."
        if analytics_enabled
        else "The site currently uses internal product analytics inside the application. External Google Analytics is not enabled in the current configuration."
    )
    maps_text = (
        "When maps and coordinate pickers are opened, the site may load Google Maps, and Google as the map provider may receive technical data required to render the map."
        if maps_enabled
        else "The site supports a map-service integration, but an external map provider is loaded only when the related configuration key is enabled."
    )
    return [
        section(
            "general",
            "1. General provisions",
            paragraph("This Privacy Policy describes how KidsMap processes user information on https://kidsmap.az, including language versions of the site, forms, the catalog, place pages, events, reviews, personal dashboards, and related features."),
            paragraph("By using the site, the user confirms that they have reviewed this Policy. If a separate consent is required for a specific type of processing, that consent is requested separately."),
            paragraph("A mere visit to the site is not treated as consent for processing that legally requires a separate expression of will."),
            email_block("For questions about data processing, correction, or deletion, contact:"),
        ),
        section(
            "purpose",
            "2. What KidsMap is for",
            paragraph("KidsMap is an information platform and catalog for kids clubs, sports sections, courses, educational organizations, specialists, and temporary events."),
            bullets(
                "search for organizations and events;",
                "use filters and browse listing pages;",
                "save favorite places;",
                "publish reviews and ratings;",
                "contact organizations;",
                "submit place-ownership requests;",
                "create and edit listings when the user has the required rights;",
            ),
            paragraph("Unless explicitly stated otherwise, KidsMap is not the organizer of listed clubs or events, does not provide those services on behalf of organizations, and does not guarantee availability, pricing, schedules, or conditions."),
        ),
        section(
            "user-categories",
            "3. Categories of users",
            paragraph("The site may be used by anonymous visitors, registered users, parents and legal guardians, business owners and representatives, listing team members, moderators, and administrators."),
            paragraph("The site is primarily intended for adult users."),
            paragraph("Children should not submit personal data through the site without the involvement of a parent or legal guardian."),
        ),
        section(
            "data-categories",
            "4. What data may be processed",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Technical visitor data",
                    paragraph("When the site is used, technical data necessary for service operation, statistics, and security may be processed automatically."),
                    bullets(
                        "session identifiers and cookies;",
                        "date and time of requests;",
                        "visited pages and paths;",
                        "interface language;",
                        "technical data related to user actions on the site;",
                        "approximate location when determined by a map service or permitted by the user through the browser;",
                    ),
                    paragraph("The KidsMap application stores per-session visits and funnel events related to search, filters, listing opens, contact clicks, favorites, reviews, and the ownership flow."),
                ),
                sub_section(
                    "account-data",
                    "4.2. Account data",
                    bullets(
                        "username;",
                        "first and last name if provided by the user;",
                        "email;",
                        "phone number if requested and provided;",
                        "password in hashed form;",
                        "interface language;",
                        "email verification status;",
                        "user role and related permissions;",
                        "creation and update dates of account-related records;",
                    ),
                    paragraph("KidsMap does not store user passwords in plain text."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. User activity",
                    bullets(
                        "favorite listings;",
                        "reviews and ratings;",
                        "likes and dislikes on reviews;",
                        "history of certain actions inside the catalog and owner flow;",
                        "submitted forms and requests needed to provide site features;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Organization owner data",
                    bullets(
                        "name, surname, and username;",
                        "email and phone if provided;",
                        "information submitted in ownership requests;",
                        "relationship to an organization and team role;",
                        "request review history;",
                        "owner-team invitations and roles;",
                        "audit history of user and administrative actions related to listings;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Organization and event data",
                    bullets(
                        "name and description;",
                        "category, age range, prices, and schedule;",
                        "address, district, metro, and coordinates;",
                        "phone, email, website, and social links;",
                        "photos, logos, and staff information;",
                        "event and temporary-activity information;",
                    ),
                    paragraph("Some of this information may relate to natural persons and may therefore qualify as personal information."),
                ),
            ],
        ),
        section(
            "children",
            "5. Information about children",
            paragraph("KidsMap does not aim to directly collect children's personal data."),
            bullets(
                "a child's full name without necessity;",
                "a child's personal phone number, email, or home address;",
                "documents, health information, or disability information;",
                "precise movement schedules;",
                "school or class information combined with identifying details;",
            ),
            paragraph("Photos and videos showing children may be uploaded only by a person who has the necessary rights and permissions."),
            paragraph("If KidsMap receives a substantiated complaint, it may hide or remove a photo or other information about a child."),
            email_block("To request removal of a child's data or image, use:"),
        ),
        section(
            "processing-purposes",
            "6. Purposes of processing",
            bullets(
                "providing access to the site and account;",
                "authentication and email verification;",
                "operating the catalog, map, reviews, and favorites;",
                "content moderation and owner flow;",
                "processing ownership requests and managing owner teams;",
                "communicating with users and sending service notices;",
                "ensuring security and preventing spam or abuse;",
                "keeping technical statistics, analytics, and activity logs;",
                "improving the interface, fixing errors, and protecting the rights of users, KidsMap, and third parties;",
            ),
        ),
        section(
            "legal-basis",
            "7. Legal grounds for processing",
            bullets(
                "user consent where required;",
                "providing features requested by the user;",
                "performance of the user agreement and actions requested by the user;",
                "compliance with legal obligations;",
                "protecting the security of the site and preventing abuse;",
                "protecting the rights and legitimate interests of users and third parties;",
            ),
            paragraph("If processing is based on consent, the user may withdraw that consent, but the withdrawal does not invalidate processing already carried out before the withdrawal."),
        ),
        section(
            "cookies",
            "8. Cookies and local storage",
            paragraph("The site uses cookies and similar mechanisms necessary for sessions, form protection, language selection, and correct account operation."),
            bullets(
                "session and authentication cookies;",
                "cookies or values related to CSRF protection;",
                "cookies and local data related to interface language and session settings;",
            ),
            paragraph(analytics_text),
            paragraph("Disabling required cookies may break certain site features."),
        ),
        section(
            "analytics",
            "9. Analytics",
            paragraph("KidsMap uses internal product analytics to understand how the catalog and core user journeys are used."),
            bullets(
                "per-session visits are recorded in SiteVisit;",
                "FunnelEvent records are stored for search, filters, listing opens, contact clicks, favorites, reviews, and owner-flow actions;",
                "some analytics events may be queued in the session before being exposed to the frontend;",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Maps and geolocation",
            paragraph("KidsMap uses place coordinates and supports map rendering, district-based discovery, and point-selection tools in owner forms."),
            paragraph(maps_text),
            paragraph("Browser geolocation is requested only through the standard browser permission flow and only with the user's permission."),
            paragraph("Refusing geolocation does not block the core catalog experience, except in flows where the user explicitly wants to determine a current point."),
        ),
        section(
            "email",
            "11. Email and service messages",
            bullets(
                "registration confirmation and email OTP delivery;",
                "OTP resend and verification flows;",
                "security notices and support replies;",
                "messages related to moderation, ownership requests, and owner-team invitations;",
                "password-reset emails provided through Django auth;",
            ),
            paragraph("Service messages required for account operation and security are different from promotional messaging."),
        ),
        section(
            "reviews-content",
            "12. Reviews, ratings, and public content",
            paragraph("Reviews, ratings, usernames or provided author names, and other published content may be visible to other visitors."),
            bullets(
                "users must not publish third-party personal data without a lawful basis;",
                "users must not publish information about children without permission;",
                "users must not publish unlawful, false, abusive, or spam content;",
            ),
            paragraph("KidsMap may moderate, hide, reject, or remove materials that violate site rules or applicable law."),
        ),
        section(
            "owner-responsibility",
            "13. Responsibility of listing owners",
            bullets(
                "accuracy of listing information;",
                "up-to-date address, pricing, schedule, and contacts;",
                "lawful use of photos, logos, and descriptions;",
                "having rights to publish staff data and images of children;",
            ),
            paragraph("KidsMap may request authority confirmation, temporarily hide a listing, reject changes, or restrict user rights in case of abuse."),
        ),
        section(
            "third-parties",
            "14. Disclosure to third parties",
            paragraph("Data may be disclosed only to the extent necessary for the relevant purpose."),
            bullets(
                "hosting and infrastructure providers;",
                "email-service providers needed to deliver service emails;",
                "a map-service provider when maps are used;",
                "an analytics provider if enabled in the current configuration;",
                "competent public authorities when legally required;",
            ),
            paragraph("KidsMap does not sell users' personal data."),
        ),
        section(
            "external-links",
            "15. Links to third-party resources",
            paragraph("Listings and site pages may contain links to organization websites, social networks, and map services."),
            paragraph("Once a user leaves KidsMap for a third-party resource, information processing is governed by that service's own rules, which KidsMap does not control."),
        ),
        section(
            "cross-border",
            "16. Cross-border processing",
            paragraph("Some technical providers may be located outside the Republic of Azerbaijan or may store data there."),
            paragraph("When such services are used, KidsMap takes applicable cross-border transfer requirements into account to the extent required by law."),
        ),
        section(
            "retention",
            "17. Retention periods",
            paragraph("Information is kept no longer than necessary for the purposes of processing unless a longer period is required by law, security needs, or dispute resolution."),
            paragraph("The project does not currently publish a single exact retention schedule for every data category."),
            bullets(
                "active-account data may be kept while the account is used or until a justified deletion request is processed;",
                "some information may remain temporarily in backups, security logs, and audit history;",
                "once the grounds for retention end, data is deleted, anonymized, or blocked within the technical model available to the project;",
            ),
        ),
        section(
            "security",
            "18. Protection of information",
            bullets(
                "access separation and user roles;",
                "authentication and email verification;",
                "password hashing through Django;",
                "CSRF protection and session-based security mechanisms;",
                "administrative and domain-specific logging of selected actions;",
                "moderation of user content;",
                "restricted access to administrative areas and infrastructure;",
            ),
            paragraph("No storage or transmission method can provide absolute security."),
        ),
        section(
            "incidents",
            "19. Security incidents",
            paragraph("If a leak, unauthorized access, or another incident is detected, KidsMap takes reasonable steps to limit consequences, remove the cause, document the incident, and make any legally required notifications."),
        ),
        section(
            "rights",
            "20. User rights",
            bullets(
                "to know whether their data is being processed;",
                "to obtain information about processing purposes and categories;",
                "to request correction or update of inaccurate data;",
                "to request the cessation of unlawful processing;",
                "to withdraw consent where applicable;",
                "to request deletion where there are legal grounds;",
                "to challenge actions related to data processing;",
            ),
            email_block("To submit a request, use:"),
        ),
        section(
            "requests",
            "21. How to submit a request",
            bullets(
                "name and account-related email;",
                "username, if available;",
                "the substance of the request;",
                "a link to the listing, review, photo, or other material;",
                "any details that help identify the relevant data;",
            ),
            paragraph("To protect information, the administration may ask for reasonable proof of identity or authority."),
        ),
        section(
            "account-deletion",
            "22. Account and data deletion",
            paragraph("The current site implementation does not include a separate public button for full self-service account deletion. Requests to delete an account and related data should be sent by email."),
            email_block("Requests to delete an account and related data should be sent to:"),
            paragraph("Deletion may include access termination and deletion or anonymization of profile data and some non-essential activity, where this is technically compatible with the project architecture and does not break ownership, moderation, or audit integrity."),
        ),
        section(
            "correction",
            "23. Data correction",
            paragraph("Users can edit some available data in their personal dashboard and owner sections, and they can also send a correction request by email."),
            paragraph("Changes to place and event listings may go through moderation before becoming public."),
        ),
        section(
            "materials-removal",
            "24. Removal of photos and materials",
            paragraph("A person who believes that a photo, description, review, or other material violates their rights or a child's rights may contact KidsMap by email."),
            email_block("For removal requests and complaints about materials, use:"),
            paragraph("During review, disputed material may be temporarily hidden."),
        ),
        section(
            "marketing",
            "25. Marketing messages",
            paragraph("Marketing messages may be sent only where there is separate consent or another lawful basis."),
            paragraph("At the time this Policy is published, marketing mailings are not a primary implemented feature of the site; email is used mainly for account, security, moderation, and owner-flow purposes."),
        ),
        section(
            "policy-changes",
            "26. Changes to this Policy",
            paragraph("This Policy may be updated when laws change, site features change, new services are connected, or data-processing methods change."),
            paragraph("The current version is published on this page, and the last updated date is shown at the top of the document."),
        ),
        section(
            "law",
            "27. Applicable law",
            paragraph("This Policy is applied with due regard to the laws of the Republic of Azerbaijan."),
            paragraph("Users may apply to a competent public authority or court in the manner provided by applicable law."),
        ),
        section(
            "contacts",
            "28. Contacts",
            paragraph("For questions about privacy, data correction, account deletion, withdrawal of consent, removal of photos or materials, content complaints, and account security, contact:"),
            email_block("KidsMap contact email:"),
        ),
    ]


LEGAL_CONTENT = {
    "review-rules": {
        "az": (
            "Rəy qaydaları",
            [
                "Rəylər moderasiyadan sonra dərc olunur.",
                "Test, təhqiredici və mənasız mətnlər dərc edilmir.",
            ],
        ),
        "ru": (
            "Правила отзывов",
            [
                "Отзывы публикуются после модерации.",
                "Тестовые, оскорбительные и бессмысленные тексты не публикуются.",
            ],
        ),
        "en": (
            "Review Rules",
            [
                "Reviews are published after moderation.",
                "Test, abusive, and meaningless texts are not published.",
            ],
        ),
    },
    "listing-rules": {
        "az": (
            "Yerləşdirmə qaydaları",
            [
                "Qeydiyyatdan keçmiş istənilən istifadəçi məkan əlavə edə bilər; bunun üçün ayrıca sahib və ya biznes hesabı tələb olunmur.",
                "Kartda ad, kateqoriya, ünvan, kontakt, yaş, qiymət və cədvəl kimi əsas məlumatlar olmalıdır.",
                "Natamam və test kartları kataloqda göstərilmir.",
            ],
        ),
        "ru": (
            "Правила размещения",
            [
                "Добавить место может любой зарегистрированный пользователь; отдельный аккаунт владельца или бизнес-аккаунт для этого не нужен.",
                "В карточке должны быть базовые данные: название, категория, адрес, контакт, возраст, цена и расписание.",
                "Неполные и тестовые карточки не показываются в каталоге.",
            ],
        ),
        "en": (
            "Listing Rules",
            [
                "Any registered user can add a place; no separate owner or business account is required.",
                "A listing should include core data such as name, category, address, contact details, age range, price, and schedule.",
                "Incomplete and test listings are not shown in the catalog.",
            ],
        ),
    },
}


def get_legal_page_content(*, page_slug: str, language: str) -> dict:
    from .legal_terms_ru import _terms_sections_ru
    from .legal_terms_az import _terms_sections_az
    from .legal_terms_en import _terms_sections_en

    safe_language = language if language in {"az", "ru", "en"} else "az"
    analytics_enabled = bool(getattr(settings, "GOOGLE_ANALYTICS_MEASUREMENT_ID", ""))
    maps_enabled = bool(getattr(settings, "GOOGLE_MAPS_API_KEY", ""))
    contact_email = _current_legal_contact_email()
    _legal_contact_email.set(contact_email)

    if page_slug == "privacy":
        sections_map = {
            "az": _privacy_sections_az,
            "ru": _privacy_sections_ru,
            "en": _privacy_sections_en,
        }
        meta_map = {
            "az": {
                "title": "Məxfilik siyasəti — KidsMap",
                "description": "KidsMap Məxfilik siyasəti: istifadəçi məlumatlarının emalı, saxlanması və qorunması qaydaları.",
                "breadcrumb": "Məxfilik siyasəti",
                "breadcrumb_aria_label": "Səhifə yolu",
                "summary": "Bu sənəd KidsMap-də hansı məlumatların toplana biləcəyini, hansı məqsədlərlə istifadə olunduğunu və istifadəçinin hansı hüquqlara malik olduğunu izah edir.",
                "effective": "22 iyun 2026",
                "updated": "22 iyun 2026",
                "dates_aria_label": "Sənəd tarixləri",
                "effective_label": "Qüvvəyə minmə tarixi",
                "updated_label": "Son yenilənmə",
                "toc_title": "Mündəricat",
                "hero_label": "KidsMap",
                "contact_title": "Məxfiliklə bağlı əlaqə",
                "contact_body": "Məxfilik, məlumatların silinməsi, kontent şikayətləri və hesab təhlükəsizliyi ilə bağlı bütün müraciətlər bu emailə yönləndirilir.",
            },
            "ru": {
                "title": "Политика конфиденциальности — KidsMap",
                "description": "Политика конфиденциальности KidsMap: порядок обработки, хранения и защиты данных пользователей сайта.",
                "breadcrumb": "Политика конфиденциальности",
                "breadcrumb_aria_label": "Хлебные крошки",
                "summary": "Этот документ объясняет, какие данные могут обрабатываться в KidsMap, для чего они используются и какими правами обладает пользователь.",
                "effective": "22 июня 2026 года",
                "updated": "22 июня 2026 года",
                "dates_aria_label": "Даты документа",
                "effective_label": "Дата вступления в силу",
                "updated_label": "Последнее обновление",
                "toc_title": "Оглавление",
                "hero_label": "KidsMap",
                "contact_title": "Контакты по конфиденциальности",
                "contact_body": "Все обращения по вопросам конфиденциальности, удаления данных, жалоб на контент и безопасности аккаунта принимаются на этот email.",
            },
            "en": {
                "title": "Privacy Policy — KidsMap",
                "description": "KidsMap Privacy Policy: how user data is processed, stored, and protected on the site.",
                "breadcrumb": "Privacy Policy",
                "breadcrumb_aria_label": "Breadcrumbs",
                "summary": "This document explains what data may be processed by KidsMap, why it is used, and what rights the user has.",
                "effective": "June 22, 2026",
                "updated": "June 22, 2026",
                "dates_aria_label": "Document dates",
                "effective_label": "Effective date",
                "updated_label": "Last updated",
                "toc_title": "Contents",
                "hero_label": "KidsMap",
                "contact_title": "Privacy contact",
                "contact_body": "All questions about privacy, data deletion, content complaints, and account security should be sent to this email address.",
            },
        }
        meta = meta_map[safe_language]
        sections = sections_map[safe_language](analytics_enabled=analytics_enabled, maps_enabled=maps_enabled)
        return {
            "page_slug": "privacy",
            "is_privacy_document": True,
            "legal_title": meta["breadcrumb"],
            "page_title": meta["title"],
            "meta_description": meta["description"],
            "breadcrumb_current": meta["breadcrumb"],
            "hero_label": meta["hero_label"],
            "summary": meta["summary"],
            "effective_date": meta["effective"],
            "updated_date": meta["updated"],
            "breadcrumb_aria_label": meta["breadcrumb_aria_label"],
            "dates_aria_label": meta["dates_aria_label"],
            "effective_label": meta["effective_label"],
            "updated_label": meta["updated_label"],
            "toc_title": meta["toc_title"],
            "sections": sections,
            "contact_title": meta["contact_title"],
            "contact_body": meta["contact_body"],
            "contact_email": contact_email,
            "toc_items": [{"id": item["id"], "title": item["title"]} for item in sections],
        }

    elif page_slug == "terms":
        sections_map = {
            "az": _terms_sections_az,
            "ru": _terms_sections_ru,
            "en": _terms_sections_en,
        }
        meta_map = {
            "az": {
                "title": "İstifadə şərtləri — KidsMap",
                "description": "KidsMap İstifadə Şərtləri: kataloqla işləmək qaydaları, hesablar, təşkilat kartları, rəylər və istifadəçi məzmunu.",
                "breadcrumb": "İstifadə şərtləri",
                "breadcrumb_aria_label": "Səhifə yolu",
                "summary": "Bu sənəd KidsMap-dən istifadə qaydalarını, eləcə də istifadəçilərin və platformanın hüquq və vəzifələrini izah edir.",
                "effective": "22 iyun 2026",
                "updated": "22 iyun 2026",
                "dates_aria_label": "Sənəd tarixləri",
                "effective_label": "Qüvvəyə minmə tarixi",
                "updated_label": "Son yenilənmə",
                "toc_title": "Mündəricat",
                "hero_label": "KidsMap",
                "contact_title": "Şərtlərlə bağlı əlaqə",
                "contact_body": "Saytdan istifadə, şikayətlər, hesablar və məzmunla bağlı bütün müraciətlər bu emailə yönləndirilir.",
            },
            "ru": {
                "title": "Условия использования — KidsMap",
                "description": "Условия использования KidsMap: правила работы с каталогом, аккаунтами, карточками организаций, отзывами и пользовательским контентом.",
                "breadcrumb": "Условия использования",
                "breadcrumb_aria_label": "Хлебные крошки",
                "summary": "Этот документ объясняет правила использования KidsMap, а также права и обязанности пользователей и платформы.",
                "effective": "22 июня 2026 года",
                "updated": "22 июня 2026 года",
                "dates_aria_label": "Даты документа",
                "effective_label": "Дата вступления в силу",
                "updated_label": "Последнее обновление",
                "toc_title": "Оглавление",
                "hero_label": "KidsMap",
                "contact_title": "Контакты по Условиям",
                "contact_body": "Все вопросы по использованию сайта, жалобы на контент, аккаунты и публикации принимаются на этот email.",
            },
            "en": {
                "title": "Terms of Use — KidsMap",
                "description": "KidsMap Terms of Use: rules for using the catalog, accounts, organization listings, reviews, and user content.",
                "breadcrumb": "Terms of Use",
                "breadcrumb_aria_label": "Breadcrumbs",
                "summary": "This document explains the rules for using KidsMap, as well as the rights and responsibilities of users and the platform.",
                "effective": "June 22, 2026",
                "updated": "June 22, 2026",
                "dates_aria_label": "Document dates",
                "effective_label": "Effective date",
                "updated_label": "Last updated",
                "toc_title": "Contents",
                "hero_label": "KidsMap",
                "contact_title": "Terms contact",
                "contact_body": "All questions regarding site usage, complaints, accounts, and content should be directed to this email.",
            },
        }
        meta = meta_map[safe_language]
        sections = sections_map[safe_language]()
        return {
            "page_slug": "terms",
            "is_privacy_document": True,
            "legal_title": meta["breadcrumb"],
            "page_title": meta["title"],
            "meta_description": meta["description"],
            "breadcrumb_current": meta["breadcrumb"],
            "hero_label": meta["hero_label"],
            "summary": meta["summary"],
            "effective_date": meta["effective"],
            "updated_date": meta["updated"],
            "breadcrumb_aria_label": meta["breadcrumb_aria_label"],
            "dates_aria_label": meta["dates_aria_label"],
            "effective_label": meta["effective_label"],
            "updated_label": meta["updated_label"],
            "toc_title": meta["toc_title"],
            "sections": sections,
            "contact_title": meta["contact_title"],
            "contact_body": meta["contact_body"],
            "contact_email": contact_email,
            "toc_items": [{"id": item["id"], "title": item["title"]} for item in sections],
        }

    title, sections = LEGAL_CONTENT[page_slug][safe_language]
    return {
        "page_slug": page_slug,
        "is_privacy_document": False,
        "legal_title": title,
        "page_title": f"{title} — KidsMap",
        "meta_description": title,
        "legal_sections": sections,
    }
