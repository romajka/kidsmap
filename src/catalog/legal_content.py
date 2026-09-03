from __future__ import annotations

from contextvars import ContextVar

from django.conf import settings


DEFAULT_LEGAL_CONTACT_EMAIL = "info@kidsmap.az"
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
        "На сайте подключён сервис веб-аналитики Google Analytics, поэтому при просмотре страниц и использовании функций сайта могут обрабатываться стандартные технические параметры браузера и анонимизированные аналитические идентификаторы."
        if analytics_enabled
        else "На сайте используется собственная агрегированная продуктовая статистика для оценки популярности разделов. Внешний сервис Google Analytics в текущей конфигурации не подключён."
    )
    maps_text = (
        "При открытии интерактивных карт и инструментов выбора адреса сайт использует картографический сервис Google Maps, который может обрабатывать технические данные, необходимые для корректного отображения карты."
        if maps_enabled
        else "Сайт поддерживает отображение заведений на карте и выбор координат через картографический интерфейс."
    )
    return [
        section(
            "general",
            "1. Общие положения",
            paragraph(
                "Настоящая Политика конфиденциальности описывает, как KidsMap (https://kidsmap.az) собирает, использует, хранит и защищает информацию пользователей сайта во всех его языковых версиях, включая каталог кружков и секций, интерактивную карту, формы обратной связи, отзывы, личные кабинеты и сопутствующие сервисы."
            ),
            paragraph(
                "Используя сайт, пользователь подтверждает, что ознакомился с настоящей Политикой. Если для обработки отдельных категорий данных требуется специальное согласие в соответствии с законодательством, такое согласие запрашивается отдельно."
            ),
            paragraph(
                "Сам факт посещения общедоступных страниц сайта не рассматривается как согласие на те виды обработки, для которых требуется отдельное явное волеизъявление."
            ),
        ),
        section(
            "purpose",
            "2. Назначение KidsMap",
            paragraph(
                "KidsMap является информационным каталогом и навигационным сервисом по детским кружкам, спортивным секциям, творческим студиям, развивающим центрам, преподавателям и детским мероприятиям."
            ),
            bullets(
                "поиск детских занятий и мероприятий по районам, метро и интересам;",
                "применение фильтров по возрасту, категориям и параметрам;",
                "сохранение понравившихся мест в избранное;",
                "публикация отзывов, оценок и реакций;",
                "быстрая связь с администрацией детских центров через прямые контакты;",
                "добавление новых мест в каталог и подача заявок на управление карточками;",
                "редактирование и актуализация информации о кружках при наличии прав доступа;",
            ),
            paragraph(
                "Если прямо не указано иное, KidsMap является независимой информационной платформой, не является организатором размещённых кружков и не оказывает соответствующие образовательные или спортивные услуги от имени организаций."
            ),
        ),
        section(
            "user-categories",
            "3. Категории пользователей",
            paragraph(
                "Сервисом KidsMap могут пользоваться незарегистрированные посетители, зарегистрированные пользователи (родители и законные представители детей), пользователи, управляющие карточками заведений (создатели мест и подтверждённые представители центров), а также модераторы и администраторы платформы."
            ),
            paragraph("Сайт рассчитан на совершеннолетних пользователей."),
            paragraph(
                "Несовершеннолетние дети не должны самостоятельно передавать персональные данные через сайт без участия и согласия родителей или законных представителей."
            ),
        ),
        section(
            "data-categories",
            "4. Какие данные могут обрабатываться",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Технические данные посетителя",
                    paragraph(
                        "При использовании сайта автоматически обрабатываются технические параметры, необходимые для функционирования платформы, статистики и безопасности:"
                    ),
                    bullets(
                        "служебные идентификаторы сессии и технические cookies;",
                        "дата, время и путь просматриваемых страниц;",
                        "выбранный язык интерфейса;",
                        "технические данные об использовании основных функций (поиск, фильтры, клики по контактам);",
                        "приблизительное местоположение, если оно разрешено пользователем в настройках браузера для поиска ближайших секций;",
                    ),
                    paragraph(
                        "KidsMap ведёт агрегированную внутреннюю статистику использования каталога для оптимизации скорости работы, удобства поиска и предотвращения сбоев."
                    ),
                ),
                sub_section(
                    "account-data",
                    "4.2. Данные учётной записи",
                    bullets(
                        "имя пользователя (username);",
                        "адрес электронной почты (email);",
                        "номер телефона (если указан в профиле);",
                        "имя и фамилия (если указаны пользователем);",
                        "фотография профиля (аватар, если загружена);",
                        "пол (если выбран в настройках);",
                        "пароль в зашифрованном виде (криптографический хеш);",
                        "выбранный язык интерфейса;",
                        "статус подтверждения email;",
                        "права доступа к управлению конкретными карточками мест;",
                        "даты создания и обновления профиля;",
                    ),
                    paragraph("KidsMap никогда не хранит пароли пользователей в открытом виде."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. Пользовательская активность",
                    bullets(
                        "сохранённые карточки в списке избранного;",
                        "опубликованные отзывы, оценки и текстовые комментарии;",
                        "реакции (лайки и дизлайки) к отзывам;",
                        "отправленные формы обратной связи и обращения в службу поддержки;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Данные пользователей, управляющих карточками мест",
                    bullets(
                        "контактные данные заявителя (имя, email, телефон);",
                        "сведения из заявки на управление карточкой места и подтверждение связи с организацией;",
                        "статус и история рассмотрения заявки модераторами;",
                        "список участников с правами редактирования карточки (команда редакторов);",
                        "журнал изменений карточки для обеспечения достоверности данных;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Данные организаций и мероприятий",
                    bullets(
                        "название заведения, категория и описание занятий;",
                        "возрастные группы, расписание и стоимость обучения;",
                        "адрес, район, ориентиры, станции метро и географические координаты;",
                        "контактные телефоны, email, ссылки на официальный сайт и соцсети;",
                        "фотографии помещений, занятий, логотипы и данные о преподавателях;",
                        "информация о мастер-классах, днях открытых дверей и временных событиях;",
                    ),
                    paragraph(
                        "Если опубликованные контактные или персональные данные представителей организаций относятся к физическим лицам, они обрабатываются в строгом соответствии с законодательством о персональных данных."
                    ),
                ),
            ],
        ),
        section(
            "children",
            "5. Информация о детях",
            paragraph("KidsMap не осуществляет прямой сбор персональных данных несовершеннолетних детей."),
            bullets(
                "полные имена детей без законной необходимости;",
                "личные телефоны, адреса проживания или частная переписка детей;",
                "документы, удостоверяющие личность, или медицинские сведения;",
                "информация о точном индивидуальном распорядке дня ребёнка;",
            ),
            paragraph(
                "Фотографии и видеоматериалы с изображением детей могут размещаться в карточках заведений только при наличии законного согласия их родителей или уполномоченных представителей."
            ),
            paragraph(
                "При получении любого обращения от родителя или законного представителя о наличии изображения или данных ребёнка администрация KidsMap незамедлительно удаляет соответствующий материал."
            ),
        ),
        section(
            "processing-purposes",
            "6. Цели обработки данных",
            bullets(
                "предоставление доступа к каталогу, интерактивной карте, поиску и фильтрам;",
                "регистрация личного кабинета, вход в систему и подтверждение email через одноразовый код;",
                "сохранение избранных мест и публикация отзывов об организациях;",
                "приём, модерация и обработка заявок на добавление кружков и управление карточками;",
                "обеспечение совместного редактирования карточек подтверждёнными представителями;",
                "отправка сервисных уведомлений, ответов службы поддержки и сообщений безопасности;",
                "предотвращение спама, накруток рейтинга, мошенничества и злоупотреблений;",
                "технический анализ производительности, исправление ошибок и улучшение интерфейса;",
                "защита законных прав и интересов пользователей, платформы и третьих лиц;",
            ),
        ),
        section(
            "legal-basis",
            "7. Основания обработки",
            bullets(
                "согласие пользователя при совершении соответствующих действий;",
                "предоставление запрошенных пользователем функций сервиса;",
                "исполнение условий пользовательского соглашения;",
                "соблюдение применимых требований законодательства;",
                "законный интерес в обеспечении стабильности и безопасности платформы;",
            ),
            paragraph(
                "Пользователь вправе отозвать своё согласие на обработку данных, направив запрос в службу поддержки."
            ),
        ),
        section(
            "cookies",
            "8. Cookies и локальное хранилище",
            paragraph(
                "Сайт использует файлы cookies и локальное хранилище браузера исключительно для обеспечения корректной работы сервиса:"
            ),
            bullets(
                "технические сессионные cookies для авторизации в личном кабинете;",
                "cookies защиты веб-форм от межсайтовых подделок (защита безопасности);",
                "сохранение выбранного языка интерфейса (AZ, RU, EN) и параметров фильтрации;",
            ),
            paragraph(analytics_text),
            paragraph(
                "Пользователь может ограничить или отключить cookies в настройках своего браузера, однако это может повлиять на возможность входа в личный кабинет."
            ),
        ),
        section(
            "analytics",
            "9. Аналитика",
            paragraph(
                "KidsMap собирает обобщённую продуктовую статистику для понимания востребованности категорий и удобства каталога:"
            ),
            bullets(
                "количество просмотров страниц и карточек заведений;",
                "популярность поисковых запросов и фильтров по районам и категориям;",
                "число переходов по прямым контактам (звонки, WhatsApp, соцсети);",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Карты и геолокация",
            paragraph(
                "KidsMap использует географические координаты для отображения мест на карте города, фильтрации по районам и станциям метро, а также для точной привязки адреса при создании кружка."
            ),
            paragraph(maps_text),
            paragraph(
                "Определение текущего местоположения через браузер запрашивается исключительно с разрешения пользователя и используется только для показа ближайших секций."
            ),
        ),
        section(
            "email",
            "11. Email и сервисные сообщения",
            bullets(
                "отправка одноразового проверочного кода (OTP) при регистрации и смене email;",
                "письма для безопасного восстановления доступа и сброса пароля;",
                "уведомления о статусе модерации добавленного кружка или заявки на управление;",
                "приглашения для совместного редактирования карточки места;",
                "ответы службы поддержки и срочные уведомления безопасности;",
            ),
            paragraph(
                "Сервисные транзакционные письма являются частью работы аккаунта и не являются рекламой."
            ),
        ),
        section(
            "reviews-content",
            "12. Отзывы, оценки и публичный контент",
            paragraph(
                "Отзывы, текстовые комментарии, оценки и имя (или псевдоним) автора, указанные при публикации, становятся общедоступными в каталоге KidsMap."
            ),
            bullets(
                "запрещено публиковать чужие персональные данные без законного основания;",
                "запрещено публиковать конфиденциальные сведения о детях;",
                "запрещены оскорбления, угрозы, реклама, спам и заведомо ложные сведения;",
            ),
            paragraph(
                "KidsMap оставляет за собой право модерировать, отклонять или удалять любые отзывы, нарушающие правила платформы."
            ),
        ),
        section(
            "owner-responsibility",
            "13. Ответственность пользователей, управляющих карточками",
            bullets(
                "достоверность и актуальность контактных данных, адреса, цен и расписания;",
                "законность использования загружаемых фотографий, логотипов и материалов;",
                "наличие необходимых согласий на публикацию фотографий преподавателей и детей;",
            ),
            paragraph(
                "В случае выявления нарушений KidsMap вправе запросить подтверждающие документы, временно скрыть карточку или ограничить права доступа."
            ),
        ),
        section(
            "third-parties",
            "14. Передача данных третьим лицам",
            paragraph(
                "KidsMap не продаёт и не передаёт персональные данные пользователей третьим сторонам для их собственных маркетинговых целей. Данные могут обрабатываться привлечёнными техническими сервисами исключительно в рамках работы платформы:"
            ),
            bullets(
                "провайдеры защищённого облачного хостинга и серверной инфраструктуры;",
                "сервисы доставки служебных и транзакционных email-сообщений;",
                "провайдер картографического сервиса (Google Maps) при отображении карт;",
                "аналитические сервисы (Google Analytics, если активированы);",
                "государственные органы при наличии официального законного запроса в соответствии с законодательством;",
            ),
        ),
        section(
            "external-links",
            "15. Ссылки на сторонние ресурсы",
            paragraph(
                "Карточки организаций могут содержать ссылки на сторонние веб-сайты, страницы в социальных сетях и чаты в мессенджерах."
            ),
            paragraph(
                "KidsMap не контролирует политику конфиденциальности сторонних сайтов. При переходе по внешним ссылкам пользователю рекомендуется ознакомиться с правилами соответствующих сервисов."
            ),
        ),
        section(
            "cross-border",
            "16. Трансграничная обработка",
            paragraph(
                "Для обеспечения высокой доступности и надёжности сервиса отдельные технические инфраструктурные провайдеры могут размещать серверы за пределами Азербайджанской Республики с соблюдением стандартов защиты информации."
            ),
        ),
        section(
            "retention",
            "17. Сроки хранения данных",
            paragraph(
                "Данные хранятся в течение срока, необходимого для достижения целей обработки, предоставления функций сервиса и выполнения требований безопасности."
            ),
            bullets(
                "информация профиля хранится до момента удаления учётной записи пользователем;",
                "служебные журналы безопасности хранятся в течение разумного технического периода;",
                "при удалении аккаунта персональные данные удаляются или необратимо обезличиваются;",
            ),
        ),
        section(
            "security",
            "18. Защита информации",
            bullets(
                "криптографическое хеширование паролей без возможности восстановления в открытом виде;",
                "разграничение прав доступа к карточкам мест на уровне отдельных объектов;",
                "двухэтапная верификация email через защищённый одноразовый код;",
                "защита веб-форм от подделки запросов и сессионный контроль безопасности;",
                "постоянная модерация пользовательского контента и защита административного доступа;",
            ),
            paragraph(
                "KidsMap применяет современные организационные и технические меры безопасности для защиты информации от несанкционированного доступа."
            ),
        ),
        section(
            "incidents",
            "19. Инциденты безопасности",
            paragraph(
                "В случае выявления угроз безопасности или несанкционированного доступа администрация незамедлительно принимает меры по локализации инцидента, устранению уязвимостей и информированию пользователей в установленном законом порядке."
            ),
        ),
        section(
            "rights",
            "20. Права пользователя",
            bullets(
                "получать информацию об обработке своих персональных данных;",
                "требовать уточнения, изменения или обновления своих данных;",
                "требовать удаления своего аккаунта и связанных персональных сведений;",
                "отозвать ранее данное согласие на обработку данных;",
                "направлять жалобы и запросы в службу поддержки KidsMap;",
            ),
        ),
        section(
            "requests",
            "21. Порядок направления запросов",
            paragraph(
                "Для реализации своих прав пользователь может направить обращение на официальный email платформы, указав:"
            ),
            bullets(
                "имя и адрес электронной почты, привязанный к аккаунту;",
                "имя пользователя (username, если применимо);",
                "суть запроса и ссылку на соответствующую страницу или материал;",
            ),
        ),
        section(
            "account-deletion",
            "22. Удаление аккаунта и данных",
            paragraph(
                "Пользователь может в любой момент запросить полное удаление своего аккаунта и персональных данных, отправив письмо на официальный email службы поддержки."
            ),
            paragraph(
                "После обработки запроса доступ к аккаунту прекращается, персональные контактные данные удаляются или обезличиваются, а общедоступные карточки каталога сохраняются в нейтральном виде без связи с профилем заявителя."
            ),
        ),
        section(
            "correction",
            "23. Исправление данных",
            paragraph(
                "Пользователь может самостоятельно обновлять информацию профиля в личном кабинете, а представители мест — актуализировать данные в панели управления заведениями."
            ),
        ),
        section(
            "materials-removal",
            "24. Удаление фотографий и материалов",
            paragraph(
                "Если вы считаете, что опубликованная фотография, отзыв или материал нарушает ваши права либо права вашего ребёнка, направьте обращение с ссылкой на спорный объект на email KidsMap для оперативной проверки и удаления."
            ),
        ),
        section(
            "marketing",
            "25. Маркетинговые сообщения",
            paragraph(
                "Рекламные и информационные рассылки могут отправляться только при наличии отдельного согласия пользователя. Сервисные уведомления о работе аккаунта не являются маркетинговыми."
            ),
        ),
        section(
            "policy-changes",
            "26. Изменение Политики",
            paragraph(
                "KidsMap вправе периодически обновлять настоящую Политику при развитии функционала или изменении законодательства. Актуальная редакция с датой обновления всегда доступна на этой странице."
            ),
        ),
        section(
            "law",
            "27. Применимое право",
            paragraph(
                "Настоящая Политика конфиденциальности регулируется законодательством Азербайджанской Республики."
            ),
        ),
        section(
            "contacts",
            "28. Контакты по вопросам конфиденциальности",
            paragraph(
                "По всем вопросам конфиденциальности, защиты данных, удаления аккаунта, отзыва согласий и жалоб на контент обращайтесь в службу поддержки KidsMap:"
            ),
            email_block("Официальный email KidsMap:"),
        ),
    ]


def _privacy_sections_az(*, analytics_enabled: bool, maps_enabled: bool) -> list[dict]:
    analytics_text = (
        "Saytda Google Analytics veb-analitika xidməti qoşulub, buna görə səhifələrə baxıldıqda və funksiyalardan istifadə edildikdə brauzerin standart texniki parametrləri və anonimləşdirilmiş analitik identifikatorlar emal oluna bilər."
        if analytics_enabled
        else "Saytda bölmələrin populyarlığını qiymətləndirmək üçün tətbiqin öz daxili aqreqasiya statistikası istifadə olunur. Xarici Google Analytics xidməti cari konfiqurasiyada qoşulmayıb."
    )
    maps_text = (
        "İnteraktiv xəritələr və ünvan seçimi alətləri açıldıqda sayt Google Maps xəritə xidmətindən istifadə edir və xəritənin düzgün göstərilməsi üçün zəruri texniki məlumatlar emal oluna bilər."
        if maps_enabled
        else "Sayt məkanların xəritədə göstərilməsini və koordinatların təyin olunmasını dəstəkləyir."
    )
    return [
        section(
            "general",
            "1. Ümumi müddəalar",
            paragraph(
                "Bu Məxfilik siyasəti KidsMap platformasının (https://kidsmap.az) bütün dil versiyalarında istifadəçi məlumatlarının necə toplanmasını, istifadəsini, saxlanmasını və qorunmasını təsvir edir. Siyasət kataloqa, xəritəyə, formalara, rəylərə, şəxsi kabinetlərə və əlaqəli xidmətlərə şamil olunur."
            ),
            paragraph(
                "Saytdan istifadə etməklə istifadəçi bu Siyasətlə tanış olduğunu təsdiq edir. Qanunvericiliyə uyğun olaraq ayrıca razılıq tələb olunan xüsusi emal növləri üçün həmin razılıq ayrıca soruşulur."
            ),
            paragraph(
                "Saytın açıq səhifələrinə sadəcə daxil olmaq xüsusi iradə ifadəsi tələb olunan emal növləri üçün razılıq hesab edilmir."
            ),
        ),
        section(
            "purpose",
            "2. KidsMap-in təyinatı",
            paragraph(
                "KidsMap uşaq dərnəkləri, idman bölmələri, yaradıcılıq studiyaları, inkişaf mərkəzləri, müəllimlər və uşaq tədbirləri üçün məlumat və naviqasiya kataloqudur."
            ),
            bullets(
                "rayonlar, metro stansiyaları və maraqlar üzrə uşaq məşğələlərini axtarmaq;",
                "yaş, kateqoriya və qiymət parametrləri üzrə filtrlərdən istifadə etmək;",
                "bəyənilən məkanları seçilmişlər siyahısına əlavə etmək;",
                "rəylər, qiymətlər və reaksiyalar dərc etmək;",
                "birbaşa əlaqə vasitələri ilə təşkilatlarla əlaqə yaratmaq;",
                "yeni məkanlar əlavə etmək və kartın idarə edilməsi üçün müraciət göndərmək;",
                "müvafiq giriş hüquqları olduqda dərnək məlumatlarını yeniləmək;",
            ),
            paragraph(
                "Ayrıca göstərilmədikdə KidsMap müstəqil məlumat platformasıdır, yerləşdirilmiş dərnəklərin təşkilatçısı deyil və həmin təşkilatların adından təhsil və ya idman xidməti göstərmir."
            ),
        ),
        section(
            "user-categories",
            "3. İstifadəçi kateqoriyaları",
            paragraph(
                "KidsMap xidmətindən qeydiyyatsız ziyarətçilər, qeydiyyatdan keçmiş istifadəçilər (valideynlər və qanuni nümayəndələr), məkan kartlarını idarə edən istifadəçilər (məkan yaradıcıları və təsdiqlənmiş nümayəndələr), eləcə də moderatorlar və administratorlar istifadə edə bilər."
            ),
            paragraph("Sayt ilk növbədə yetkin istifadəçilər üçün nəzərdə tutulub."),
            paragraph(
                "Yetkinlik yaşına çatmayan uşaqlar valideynlərinin və ya qanuni nümayəndələrinin iştirakı olmadan sayt vasitəsilə fərdi məlumat göndərməməlidirlər."
            ),
        ),
        section(
            "data-categories",
            "4. Hansı məlumatlar emal oluna bilər",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Ziyarətçinin texniki məlumatları",
                    paragraph(
                        "Saytdan istifadə zamanı platformanın işləməsi, statistika və təhlükəsizlik üçün zəruri texniki parametrlər avtomatik emal olunur:"
                    ),
                    bullets(
                        "sessiya identifikatorları və texniki cookies;",
                        "baxılan səhifələrin tarixi, vaxtı və ünvanı;",
                        "seçilmiş interfeys dili;",
                        "əsas funksiyalardan istifadə üzrə texniki məlumatlar (axtarış, filtrlər, kontakt klikləri);",
                        "yaxınlıqdakı dərnəkləri tapmaq üçün brauzerdə icazə verildikdə təxmini geolokasiya;",
                    ),
                    paragraph(
                        "KidsMap axtarış sürətini və rahatlığını təmin etmək üçün kataloqun istifadəsinə dair aqreqasiya olunmuş daxili statistika aparır."
                    ),
                ),
                sub_section(
                    "account-data",
                    "4.2. Hesab məlumatları",
                    bullets(
                        "istifadəçi adı (username);",
                        "elektron poçt ünvanı (email);",
                        "telefon nömrəsi (profilə daxil edildikdə);",
                        "ad və soyad (istifadəçi daxil edibsə);",
                        "profil şəkli (avatar, yükləndikdə);",
                        "cins (seçildikdə);",
                        "şifrələnmiş formada parol (kriptoqrafik heş);",
                        "seçilmiş interfeys dili;",
                        "email təsdiqi statusu;",
                        "konkret məkan kartlarının idarə olunması hüquqları;",
                        "profilin yaradılma və yenilənmə tarixləri;",
                    ),
                    paragraph("KidsMap istifadəçi parollarını heç vaxt açıq mətndə saxlamır."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. İstifadəçi aktivliyi",
                    bullets(
                        "seçilmişlər siyahısına əlavə edilmiş kartlar;",
                        "dərc edilmiş rəylər, qiymətlər və şərhlər;",
                        "rəylərə verilən like və dislike reaksiyaları;",
                        "göndərilmiş əks-əlaqə formaları və dəstək müraciətləri;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Məkan kartlarını idarə edən istifadəçilərin məlumatları",
                    bullets(
                        "ərizəçinin əlaqə məlumatları (ad, email, telefon);",
                        "kartın idarə edilməsi müraciətində göstərilən məlumatlar və təşkilatla əlaqənin təsdiqi;",
                        "müraciətin moderatorlar tərəfindən baxılma statusu və tarixçəsi;",
                        "kartı birgə redaktə edən komanda üzvlərinin siyahısı və rolları;",
                        "məlumatların dəqiqliyini təmin etmək üçün kartın dəyişiklik tarixçəsi;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Təşkilat və tədbir məlumatları",
                    bullets(
                        "müəssisənin adı, kateqoriyası və dərnəklərin təsviri;",
                        "yaş qrupları, dərslərin cədvəli və qiymətlər;",
                        "ünvan, rayon, orientirlər, metro stansiyaları və koordinatlar;",
                        "əlaqə telefonları, email, rəsmi sayt və sosial şəbəkə linkləri;",
                        "otaqların, dərslərin fotoları, loqotiplər və müəllimlər haqqında məlumatlar;",
                        "ustad dərsləri və müvəqqəti tədbirlər haqqında məlumatlar;",
                    ),
                    paragraph(
                        "Təşkilat nümayəndələrinin dərc olunan əlaqə məlumatları fiziki şəxslərə aid olduqda, onlar fərdi məlumatlar haqqında qanunvericiliyə uyğun emal edilir."
                    ),
                ),
            ],
        ),
        section(
            "children",
            "5. Uşaqlar haqqında məlumatlar",
            paragraph("KidsMap yetkinlik yaşına çatmayan uşaqların fərdi məlumatlarının birbaşa toplanmasını həyata keçirmir."),
            bullets(
                "qanuni zərurət olmadan uşaqların tam adları;",
                "uşaqların şəxsi telefonları, yaşayış ünvanları və ya şəxsi yazışmaları;",
                "şəxsiyyəti təsdiq edən sənədlər və ya tibbi məlumatlar;",
                "uşağın fərdi gündəlik hərəkət marşrutu haqqında məlumatlar;",
            ),
            paragraph(
                "Uşaqların foto və video təsvirləri məkan kartlarında yalnız onların valideynlərinin və ya qanuni nümayəndələrinin qanuni razılığı olduqda yerləşdirilə bilər."
            ),
            paragraph(
                "Valideyn və ya qanuni nümayəndədən uşağın şəklinin və ya məlumatının silinməsi ilə bağlı müraciət daxil olduqda, KidsMap həmin materialı dərhal silir."
            ),
        ),
        section(
            "processing-purposes",
            "6. Məlumatların emalı məqsədləri",
            bullets(
                "kataloqa, interaktiv xəritəyə, axtarış və filtrlərə çıxışın təmin edilməsi;",
                "şəxsi kabinetin qeydiyyatı, giriş və emailin təsdiqlənməsi;",
                "seçilmiş məkanların saxlanması və rəylərin dərci;",
                "yeni məkanların əlavə edilməsi və kartın idarə olunması müraciətlərinin moderasiyası;",
                "təsdiqlənmiş nümayəndələr tərəfindən kartların birgə redaktə olunması;",
                "xidməti bildirişlərin, dəstək cavablarının və təhlükəsizlik məlumatlarının göndərilməsi;",
                "spamın, süni reytinq artımının və sui-istifadələrin qarşısının alınması;",
                "texniki məhsuldarlığın təhlili və interfeysin təkmilləşdirilməsi;",
                "istifadəçilərin, platformanın və üçüncü şəxslərin qanuni hüquqlarının qorunması;",
            ),
        ),
        section(
            "legal-basis",
            "7. Emalın hüquqi əsasları",
            bullets(
                "müvafiq hərəkətlər zamanı istifadəçinin razılığı;",
                "istifadəçinin tələb etdiyi xidmət funksiyalarının göstərilməsi;",
                "istifadəçi şərtlərinin icrası;",
                "qanunvericiliyin tələblərinə riayət edilməsi;",
                "platformanın sabitliyi və təhlükəsizliyinin təmin olunmasında qanuni maraq;",
            ),
            paragraph(
                "İstifadəçi dəstək xidmətinə müraciət edərək məlumatlarının emalına verdiyi razılığı geri götürə bilər."
            ),
        ),
        section(
            "cookies",
            "8. Kukilər və lokal yaddaş",
            paragraph(
                "Sayt xidmətin düzgün və təhlükəsiz işləməsi üçün cookies fayllarından və lokal yaddaşdan istifadə edir:"
            ),
            bullets(
                "şəxsi kabinetə daxil olmaq üçün texniki sessiya kukiləri;",
                "veb-formaları kənar saxtalaşdırmalardan qoruyan təhlükəsizlik kukiləri;",
                "seçilmiş interfeys dili (AZ, RU, EN) və axtarış parametrlərinin saxlanması;",
            ),
            paragraph(analytics_text),
            paragraph(
                "İstifadəçi brauzer tənzimləmələrində kukiləri məhdudlaşdıra bilər, lakin bu şəxsi kabinetə girişə təsir göstərə bilər."
            ),
        ),
        section(
            "analytics",
            "9. Analitika",
            paragraph(
                "KidsMap bölmələrin populyarlığını və kataloqun rahatlığını anlamaq üçün ümumiləşdirilmiş məhsul statistikası toplayır:"
            ),
            bullets(
                "səhifələrə və məkan kartlarına baxış sayı;",
                "axtarış sorğularının, rayon və kateqoriya filtrlərinin populyarlığı;",
                "birbaşa əlaqə düymələrinə (zəng, WhatsApp, sosial şəbəkələr) kliklərin sayı;",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Xəritə və geolokasiya",
            paragraph(
                "KidsMap coğrafi koordinatlardan məkanların şəhər xəritəsində göstərilməsi, rayonlar və metro üzrə axtarış, həmçinin yeni dərnək əlavə edilərkən dəqiq ünvanın qeyd olunması üçün istifadə edir."
            ),
            paragraph(maps_text),
            paragraph(
                "Brauzer vasitəsilə cari məkanın təyin edilməsi yalnız istifadəçinin icazəsi ilə yaxınlıqdakı dərnəkləri göstərmək üçün həyata keçirilir."
            ),
        ),
        section(
            "email",
            "11. E-poçt və xidməti bildirişlər",
            bullets(
                "qeydiyyat və email dəyişikliyi zamanı birdəfəlik təsdiq kodunun (OTP) göndərilməsi;",
                "parolun bərpası üçün təhlükəsizlik məktubları;",
                "əlavə edilmiş dərnəyin və ya kartın idarə edilməsi müraciətinin moderasiya statusu;",
                "kartın komanda ilə birgə redaktə olunması üçün dəvətlər;",
                "dəstək xidmətinin cavabları və təhlükəsizlik bildirişləri;",
            ),
            paragraph(
                "Xidməti bildirişlər hesabın fəaliyyətinin bir hissəsidir və reklam xarakteri daşımır."
            ),
        ),
        section(
            "reviews-content",
            "12. Rəylər, qiymətlər və ictimai məzmun",
            paragraph(
                "Rəylər, şərhlər, qiymətlər və dərc zamanı göstərilən istifadəçi adı kataloqda hər kəs üçün açıq olur."
            ),
            bullets(
                "başqalarının fərdi məlumatlarını icazəsiz yerləşdirmək qadağandır;",
                "uşaqlar haqqında gizli məlumatları paylaşmaq qadağandır;",
                "təhqir, hədə, reklam, spam və yalan məlumatlar yolverilməzdir;",
            ),
            paragraph(
                "KidsMap qaydaları pozan rəyləri moderasiya etmək, gizlətmək və ya silmək hüququnu özündə saxlayır."
            ),
        ),
        section(
            "owner-responsibility",
            "13. Məkan kartlarını idarə edən istifadəçilərin məsuliyyəti",
            bullets(
                "əlaqə məlumatlarının, ünvanın, qiymətlərin və cədvəlin düzgünlüyü və aktuallığı;",
                "yüklənən fotoşəkillərin, loqoların və mətnlərin qanuniliyi;",
                "müəllimlərin və uşaqların fotolarının dərcinə dair zəruri icazələrin mövcudluğu;",
            ),
            paragraph(
                "Qaydalar pozulduqda KidsMap təsdiqedici sənədlər tələb edə, kartı müvəqqəti gizlədə və ya giriş hüquqlarını məhdudlaşdıra bilər."
            ),
        ),
        section(
            "third-parties",
            "14. Məlumatların üçüncü tərəflərə ötürülməsi",
            paragraph(
                "KidsMap istifadəçilərin fərdi məlumatlarını üçüncü tərəflərə satmır. Məlumatlar yalnız platformanın fəaliyyəti üçün zəruri texniki xidmətlər çərçivəsində emal oluna bilər:"
            ),
            bullets(
                "təhlükəsiz bulud hostinqi və server infrastrukturu təchizatçıları;",
                "xidməti e-poçt bildirişlərinin çatdırılması xidmətləri;",
                "xəritə xidməti təchizatçısı (Google Maps);",
                "analitika təchizatçıları (Google Analytics, aktiv olduqda);",
                "qanunvericiliklə müəyyən edilmiş rəsmi tələb olduqda dövlət orqanları;",
            ),
        ),
        section(
            "external-links",
            "15. Kənar resurslara keçidlər",
            paragraph(
                "Məkan kartlarında təşkilatların rəsmi veb-saytlarına, sosial şəbəkə səhifələrinə və messencerlərinə keçidlər ola bilər."
            ),
            paragraph(
                "KidsMap kənar resursların məxfilik siyasətinə nəzarət etmir və istifadəçilərə həmin saytların qaydaları ilə tanış olmağı tövsiyə edir."
            ),
        ),
        section(
            "cross-border",
            "16. Transsərhəd emal",
            paragraph(
                "Xidmətin yüksək etibarlılığını təmin etmək üçün bəzi texniki infrastruktur təchizatçıları serverləri məlumatların qorunması standartlarına uyğun olaraq Azərbaycan Respublikasının hüdudlarından kənarda yerləşdirə bilər."
            ),
        ),
        section(
            "retention",
            "17. Məlumatların saxlanma müddəti",
            paragraph(
                "Məlumatlar emal məqsədlərinə nail olmaq, xidmət funksiyalarını təmin etmək və təhlükəsizlik tələblərini yerinə yetirmək üçün zəruri olan müddətdə saxlanılır."
            ),
            bullets(
                "profil məlumatları hesab istifadəçi tərəfindən silinənə qədər saxlanılır;",
                "təhlükəsizlik jurnalları ağlabatan texniki müddət ərzində saxlanılır;",
                "hesab silindikdə fərdi məlumatlar silinir və ya bərpa olunmaz şəkildə anonimləşdirilir;",
            ),
        ),
        section(
            "security",
            "18. Məlumatların qorunması",
            bullets(
                "parolların bərpa olunması mümkün olmayan kriptoqrafik heşlənməsi;",
                "məkan kartlarına giriş hüquqlarının fərdi obyekt səviyyəsində ayrılması;",
                "emailin birdəfəlik kodla təhlükəsiz verifikasiyası;",
                "veb-formaların saxtalaşdırmalardan qorunması və sessiya təhlükəsizliyi;",
                "istifadəçi məzmununun davamlı moderasiyası və inzibati girişin qorunması;",
            ),
            paragraph(
                "KidsMap məlumatları icazəsiz girişdən qorumaq üçün müasir təşkilati və texniki təhlükəsizlik tədbirləri tətbiq edir."
            ),
        ),
        section(
            "incidents",
            "19. Təhlükəsizlik insidentləri",
            paragraph(
                "Təhlükəsizlik təhdidləri aşkar edildikdə administrasiya dərhal insidentin qarşısını alır, boşluqları aradan qaldırır və qanunvericiliklə müəyyən edilmiş qaydada tədbirlər görür."
            ),
        ),
        section(
            "rights",
            "20. İstifadəçi hüquqları",
            bullets(
                "öz fərdi məlumatlarının emalı barədə məlumat almaq;",
                "məlumatlarının dəqiqləşdirilməsini, dəyişdirilməsini və ya yenilənməsini tələb etmək;",
                "hesabının və əlaqəli fərdi məlumatlarının silinməsini tələb etmək;",
                "məlumatların emalına verdiyi razılığı geri götürmək;",
                "KidsMap dəstək xidmətinə müraciət və şikayət göndərmək;",
            ),
        ),
        section(
            "requests",
            "21. Müraciətlərin göndərilmə qaydası",
            paragraph(
                "Hüquqlarını həyata keçirmək üçün istifadəçi rəsmi email ünvanına aşağıdakı məlumatları göstərməklə müraciət göndərə bilər:"
            ),
            bullets(
                "ad və hesaba bağlı elektron poçt ünvanı;",
                "istifadəçi adı (username, varsa);",
                "müraciətin mahiyyəti və müvafiq səhifəyə və ya materiala keçid linki;",
            ),
        ),
        section(
            "account-deletion",
            "22. Hesabın və məlumatların silinməsi",
            paragraph(
                "İstifadəçi istənilən vaxt rəsmi dəstək emailinə müraciət edərək hesabının və fərdi məlumatlarının tam silinməsini tələb edə bilər."
            ),
            paragraph(
                "Müraciət icra edildikdən sonra hesaba giriş dayandırılır, əlaqə məlumatları silinir və ya anonimləşdirilir, kataloqdakı ümumi məkan kartları isə ərizəçi profili ilə əlaqəsi kəsilərək saxlanılır."
            ),
        ),
        section(
            "correction",
            "23. Məlumatların düzəldilməsi",
            paragraph(
                "İstifadəçi şəxsi kabinetində profil məlumatlarını, məkan nümayəndələri isə idarəetmə panelində müəssisə məlumatlarını sərbəst şəkildə yeniləyə bilər."
            ),
        ),
        section(
            "materials-removal",
            "24. Foto və materialların silinməsi",
            paragraph(
                "Dərc edilmiş fotoşəkilin və ya rəyin sizin və ya uşağınızın hüquqlarını pozduğunu düşünürsünüzsə, operativ araşdırma və silinmə üçün linklə birlikdə KidsMap emailinə müraciət göndərin."
            ),
        ),
        section(
            "marketing",
            "25. Marketinq bildirişləri",
            paragraph(
                "Reklam xarakterli məlumatlar yalnız istifadəçinin ayrıca razılığı olduqda göndərilə bilər. Hesabın fəaliyyətinə dair xidməti bildirişlər reklam hesab edilmir."
            ),
        ),
        section(
            "policy-changes",
            "26. Siyasətin dəyişdirilməsi",
            paragraph(
                "KidsMap funksionallığın inkişafı və ya qanunvericiliyin dəyişməsi ilə əlaqədar bu Siyasəti vaxtaşırı yeniləyə bilər. Son yenilənmə tarixi ilə birlikdə aktual mətn həmişə bu səhifədə dərc olunur."
            ),
        ),
        section(
            "law",
            "27. Tətbiq olunan hüquq",
            paragraph(
                "Bu Məxfilik siyasəti Azərbaycan Respublikasının qanunvericiliyi ilə tənzimlənir."
            ),
        ),
        section(
            "contacts",
            "28. Məxfiliklə bağlı əlaqə",
            paragraph(
                "Məxfilik, məlumatların qorunması, hesabın silinməsi, razılığın geri götürülməsi və şikayətlərlə bağlı KidsMap dəstək xidmətinə müraciət edin:"
            ),
            email_block("KidsMap rəsmi əlaqə emaili:"),
        ),
    ]


def _privacy_sections_en(*, analytics_enabled: bool, maps_enabled: bool) -> list[dict]:
    analytics_text = (
        "Google Analytics web analytics is enabled in the current configuration, which means standard browser technical parameters and anonymized analytical identifiers may be processed when pages are viewed and features are used."
        if analytics_enabled
        else "The site uses internal aggregated analytics to evaluate section popularity. External Google Analytics is not enabled in the current configuration."
    )
    maps_text = (
        "When interactive maps and location pickers are opened, the site utilizes Google Maps services, which may process technical data required to render the map correctly."
        if maps_enabled
        else "The site supports displaying venue locations and coordinates on the map interface."
    )
    return [
        section(
            "general",
            "1. General Provisions",
            paragraph(
                "This Privacy Policy describes how KidsMap (https://kidsmap.az) collects, uses, stores, and protects user information across all language versions, including the directory of kids clubs, interactive map, forms, reviews, user dashboards, and associated features."
            ),
            paragraph(
                "By using the site, the user confirms that they have reviewed this Policy. If separate consent is required for specific data processing under applicable laws, such consent is requested separately."
            ),
            paragraph(
                "Merely browsing public pages does not constitute consent for types of processing that require explicit expression of intent."
            ),
        ),
        section(
            "purpose",
            "2. Purpose of KidsMap",
            paragraph(
                "KidsMap is an informational catalog and navigation platform for children's clubs, sports sections, creative studios, educational centers, specialists, and family events."
            ),
            bullets(
                "search for children's activities and events by districts, metro stations, and interests;",
                "apply filters by age, category, and preferences;",
                "save favorite places to personal bookmarks;",
                "publish reviews, ratings, and feedback reactions;",
                "connect directly with venue management through contact buttons;",
                "list new venues and submit place management requests;",
                "update and maintain club information when authorized;",
            ),
            paragraph(
                "Unless explicitly stated otherwise, KidsMap is an independent information directory, is not the organizer of listed clubs, and does not provide educational or athletic services on their behalf."
            ),
        ),
        section(
            "user-categories",
            "3. User Categories",
            paragraph(
                "KidsMap can be used by unregistered visitors, registered users (parents and legal guardians), users managing place listings (place creators and verified venue representatives), as well as platform moderators and administrators."
            ),
            paragraph("The platform is intended for adult users."),
            paragraph(
                "Minors should not transmit personal data through the platform without the involvement and consent of a parent or legal guardian."
            ),
        ),
        section(
            "data-categories",
            "4. Categories of Processed Data",
            children=[
                sub_section(
                    "technical-data",
                    "4.1. Visitor Technical Data",
                    paragraph(
                        "When using the site, technical parameters necessary for service operation, security, and statistics are automatically processed:"
                    ),
                    bullets(
                        "session identifiers and technical cookies;",
                        "date, time, and paths of viewed pages;",
                        "selected interface language;",
                        "technical usage data (search queries, filters, contact button clicks);",
                        "approximate location if permitted by the user in browser settings to find nearby clubs;",
                    ),
                    paragraph(
                        "KidsMap maintains aggregated internal analytics to optimize search speed, user experience, and platform reliability."
                    ),
                ),
                sub_section(
                    "account-data",
                    "4.2. User Account Data",
                    bullets(
                        "username;",
                        "email address;",
                        "phone number (if provided in profile);",
                        "first and last name (if specified by the user);",
                        "profile photo (avatar, if uploaded);",
                        "gender (if selected in settings);",
                        "password in securely hashed form (cryptographic hash);",
                        "interface language preference;",
                        "email verification status;",
                        "access permissions for managing specific place listings;",
                        "account creation and update timestamps;",
                    ),
                    paragraph("KidsMap never stores user passwords in plain text."),
                ),
                sub_section(
                    "activity-data",
                    "4.3. User Activity",
                    bullets(
                        "saved places in personal favorites;",
                        "published reviews, ratings, and comments;",
                        "likes and dislikes on community reviews;",
                        "submitted contact forms and support requests;",
                    ),
                ),
                sub_section(
                    "owner-data",
                    "4.4. Place Management Data",
                    bullets(
                        "applicant contact details (name, email, phone);",
                        "information submitted in place management requests and verification details;",
                        "moderation review status and history;",
                        "list of team members authorized to edit the listing (editor team);",
                        "place change audit logs to maintain data accuracy and security;",
                    ),
                ),
                sub_section(
                    "listing-data",
                    "4.5. Organization and Event Listings",
                    bullets(
                        "venue name, category, and class descriptions;",
                        "age groups, schedules, and tuition fees;",
                        "address, district, metro stations, landmarks, and coordinates;",
                        "phone numbers, email, official website, and social links;",
                        "photos of facilities, activities, logos, and instructor profiles;",
                        "information on masterclasses, open doors, and temporary events;",
                    ),
                    paragraph(
                        "Where published contact or profile information of venue representatives relates to individuals, it is processed in strict compliance with data privacy regulations."
                    ),
                ),
            ],
        ),
        section(
            "children",
            "5. Children's Information",
            paragraph("KidsMap does not directly collect personal data from minors."),
            bullets(
                "full names of children without lawful necessity;",
                "personal phone numbers, residential addresses, or private correspondence of minors;",
                "identity documents or medical information;",
                "detailed personal schedules of a child;",
            ),
            paragraph(
                "Photos and videos depicting children may only be published on place listings with lawful consent from their parents or legal guardians."
            ),
            paragraph(
                "Upon receiving any request from a parent or legal guardian regarding a child's photo or data, KidsMap will remove the content immediately."
            ),
        ),
        section(
            "processing-purposes",
            "6. Purposes of Data Processing",
            bullets(
                "providing access to the catalog, map, search, and filters;",
                "account registration, login, and secure email verification via one-time code;",
                "saving favorite listings and publishing reviews;",
                "processing and moderating place submissions and management requests;",
                "enabling team collaboration on place listings for verified representatives;",
                "sending transactional service messages, support replies, and security notices;",
                "preventing spam, rating manipulation, fraud, and abuse;",
                "technical performance analysis, bug fixing, and UI enhancements;",
                "protecting the legal rights and security of users, the platform, and third parties;",
            ),
        ),
        section(
            "legal-basis",
            "7. Legal Basis for Processing",
            bullets(
                "user consent provided during respective actions;",
                "delivering service features requested by the user;",
                "performance of terms of service;",
                "compliance with applicable legal obligations;",
                "legitimate interest in maintaining platform stability and security;",
            ),
            paragraph(
                "Users may withdraw their consent at any time by contacting our support team."
            ),
        ),
        section(
            "cookies",
            "8. Cookies and Local Storage",
            paragraph(
                "The site utilizes cookies and browser local storage strictly to ensure proper and secure functionality:"
            ),
            bullets(
                "technical session cookies for account authentication;",
                "security cookies preventing cross-site request forgery;",
                "storage of chosen language (AZ, RU, EN) and filter preferences;",
            ),
            paragraph(analytics_text),
            paragraph(
                "Users can manage or disable cookies in their browser settings, though this may affect dashboard login capabilities."
            ),
        ),
        section(
            "analytics",
            "9. Analytics",
            paragraph(
                "KidsMap gathers aggregated product analytics to understand catalog usage and improve user convenience:"
            ),
            bullets(
                "page and place listing view counts;",
                "popularity of search terms and district/category filters;",
                "number of clicks on direct contact buttons (Call, WhatsApp, Social links);",
            ),
            paragraph(analytics_text),
        ),
        section(
            "maps",
            "10. Maps and Geolocation",
            paragraph(
                "KidsMap uses coordinates to render venues on city maps, filter by districts and metro stations, and specify exact locations when creating listings."
            ),
            paragraph(maps_text),
            paragraph(
                "Browser geolocation is requested solely with explicit user permission to locate nearby activities."
            ),
        ),
        section(
            "email",
            "11. Email and Service Notifications",
            bullets(
                "delivery of one-time verification codes (OTP) upon registration and email change;",
                "secure password recovery messages;",
                "moderation status updates for submitted places and management requests;",
                "invitations to collaborate on place listings;",
                "support responses and urgent security alerts;",
            ),
            paragraph(
                "Transactional service emails are essential for account operation and do not contain marketing."
            ),
        ),
        section(
            "reviews-content",
            "12. Reviews, Ratings and Public Content",
            paragraph(
                "Reviews, ratings, comments, and the author name or pseudonym provided upon submission are publicly visible in the catalog."
            ),
            bullets(
                "publishing third-party personal data without consent is strictly prohibited;",
                "sharing confidential children's data is prohibited;",
                "abuse, harassment, advertising, spam, and false claims are not allowed;",
            ),
            paragraph(
                "KidsMap reserves the right to moderate, hide, or remove any reviews that violate platform policies."
            ),
        ),
        section(
            "owner-responsibility",
            "13. Responsibilities of Place Managers",
            bullets(
                "accuracy and timeliness of contact info, address, prices, and schedules;",
                "lawful rights to uploaded photos, logos, and descriptions;",
                "possession of necessary permissions to publish photos of staff and children;",
            ),
            paragraph(
                "In case of violations, KidsMap may request verification documents, temporarily hide the listing, or restrict access rights."
            ),
        ),
        section(
            "third-parties",
            "14. Third-Party Data Sharing",
            paragraph(
                "KidsMap does not sell personal data to third parties. Information may only be processed by trusted infrastructure services essential for platform operation:"
            ),
            bullets(
                "secure cloud hosting and infrastructure providers;",
                "transactional email delivery services;",
                "map service providers (Google Maps);",
                "analytics providers (Google Analytics, if enabled);",
                "governmental authorities upon formal lawful request pursuant to applicable legislation;",
            ),
        ),
        section(
            "external-links",
            "15. Links to External Resources",
            paragraph(
                "Place listings may contain links to third-party websites, social networks, and messaging apps."
            ),
            paragraph(
                "KidsMap does not control third-party privacy practices and encourages users to review the policies of external services."
            ),
        ),
        section(
            "cross-border",
            "16. Cross-Border Data Processing",
            paragraph(
                "To ensure high availability and security, certain technical infrastructure providers may operate servers outside Azerbaijan in compliance with data protection standards."
            ),
        ),
        section(
            "retention",
            "17. Data Retention Periods",
            paragraph(
                "Data is retained for the period necessary to fulfill processing purposes, provide service features, and comply with security requirements."
            ),
            bullets(
                "profile information is retained until account deletion by the user;",
                "security logs are kept for a reasonable technical duration;",
                "upon account deletion, personal data is erased or irreversibly anonymized;",
            ),
        ),
        section(
            "security",
            "18. Information Security",
            bullets(
                "cryptographic password hashing with no plain text recovery;",
                "object-level access control for place management permissions;",
                "secure one-time code email verification;",
                "web form request forgery protection and session safety controls;",
                "continuous moderation of user-submitted content and restricted administrative access;",
            ),
            paragraph(
                "KidsMap employs modern organizational and technical measures to protect information against unauthorized access."
            ),
        ),
        section(
            "incidents",
            "19. Security Incidents",
            paragraph(
                "If a security incident is identified, administration promptly mitigates risks, addresses vulnerabilities, and notifies users as required by applicable laws."
            ),
        ),
        section(
            "rights",
            "20. User Rights",
            bullets(
                "request information about the processing of their personal data;",
                "request correction, update, or rectification of their data;",
                "request deletion of their account and associated personal information;",
                "withdraw previously granted consent for processing;",
                "submit inquiries and complaints to KidsMap support;",
            ),
        ),
        section(
            "requests",
            "21. Submitting Requests",
            paragraph(
                "To exercise these rights, users may send an inquiry to our official email including:"
            ),
            bullets(
                "name and email address associated with the account;",
                "username (if applicable);",
                "nature of the request and relevant page or material link;",
            ),
        ),
        section(
            "account-deletion",
            "22. Account and Data Deletion",
            paragraph(
                "Users may request full deletion of their account and personal data at any time by emailing our support team."
            ),
            paragraph(
                "Upon processing the request, account access is terminated, personal contact information is erased or anonymized, and public catalog listings are preserved without association to the applicant's profile."
            ),
        ),
        section(
            "correction",
            "23. Data Rectification",
            paragraph(
                "Users can update profile details in their account dashboard, while place representatives can maintain venue data directly in the place management dashboard."
            ),
        ),
        section(
            "materials-removal",
            "24. Removal of Photos and Media",
            paragraph(
                "If you believe a published photo or review infringes your rights or your child's privacy, please email us with the link for prompt review and removal."
            ),
        ),
        section(
            "marketing",
            "25. Marketing Communications",
            paragraph(
                "Marketing emails may only be sent with explicit user consent. Transactional service messages regarding account functions do not constitute marketing."
            ),
        ),
        section(
            "policy-changes",
            "26. Changes to this Policy",
            paragraph(
                "KidsMap may update this Policy to reflect feature additions or legal changes. The latest version with the update date is always published on this page."
            ),
        ),
        section(
            "law",
            "27. Applicable Law",
            paragraph(
                "This Privacy Policy is governed by the laws of the Republic of Azerbaijan."
            ),
        ),
        section(
            "contacts",
            "28. Privacy Inquiries",
            paragraph(
                "For all inquiries regarding privacy, data protection, account deletion, consent withdrawal, and content complaints, contact KidsMap support:"
            ),
            email_block("KidsMap Official Email:"),
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
                "description": "KidsMap Məxfilik siyasəti: istifadəçi məlumatlarının toplanması, emalı, saxlanması və qorunması qaydaları.",
                "breadcrumb": "Məxfilik siyasəti",
                "breadcrumb_aria_label": "Səhifə yolu",
                "summary": "Bu sənəd KidsMap platformasında hansı məlumatların emal olunduğunu, hansı məqsədlərlə istifadə edildiyini və istifadəçinin hansı hüquqlara malik olduğunu aydın izah edir.",
                "effective": "22 iyun 2026",
                "updated": "03 sentyabr 2026",
                "dates_aria_label": "Sənəd tarixləri",
                "effective_label": "Qüvvəyə minmə tarixi",
                "updated_label": "Son yenilənmə",
                "toc_title": "Mündəricat",
                "hero_label": "Hüquqi məlumat və Məxfilik",
                "contact_title": "Məxfiliklə bağlı müraciətlər",
                "contact_body": "Məxfilik, məlumatların silinməsi, düzəlişlər, hesab təhlükəsizliyi və şikayətlərlə bağlı bütün müraciətlər bu email vasitəsilə qəbul edilir.",
            },
            "ru": {
                "title": "Политика конфиденциальности — KidsMap",
                "description": "Политика конфиденциальности KidsMap: порядок сбора, обработки, хранения и защиты данных пользователей сайта.",
                "breadcrumb": "Политика конфиденциальности",
                "breadcrumb_aria_label": "Хлебные крошки",
                "summary": "Этот документ объясняет, какие данные обрабатываются в KidsMap, для каких целей они используются и какими правами обладает пользователь.",
                "effective": "22 июня 2026 года",
                "updated": "03 сентября 2026 года",
                "dates_aria_label": "Даты документа",
                "effective_label": "Дата вступления в силу",
                "updated_label": "Последнее обновление",
                "toc_title": "Оглавление",
                "hero_label": "Правовая информация и конфиденциальность",
                "contact_title": "Вопросы о конфиденциальности",
                "contact_body": "Все обращения по вопросам конфиденциальности, удаления данных, исправления информации, безопасности аккаунта и жалоб на контент принимаются на этот email.",
            },
            "en": {
                "title": "Privacy Policy — KidsMap",
                "description": "KidsMap Privacy Policy: how user data is collected, processed, stored, and protected on the site.",
                "breadcrumb": "Privacy Policy",
                "breadcrumb_aria_label": "Breadcrumbs",
                "summary": "This document explains what data is processed by KidsMap, why it is used, and what privacy rights users have.",
                "effective": "June 22, 2026",
                "updated": "September 03, 2026",
                "dates_aria_label": "Document dates",
                "effective_label": "Effective date",
                "updated_label": "Last updated",
                "toc_title": "Contents",
                "hero_label": "Legal & Privacy Policy",
                "contact_title": "Privacy Inquiries",
                "contact_body": "All questions regarding privacy, data deletion, rectification, account security, and content complaints should be directed to this email.",
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
                "updated": "03 sentyabr 2026",
                "dates_aria_label": "Sənəd tarixləri",
                "effective_label": "Qüvvəyə minmə tarixi",
                "updated_label": "Son yenilənmə",
                "toc_title": "Mündəricat",
                "hero_label": "İstifadə Şərtləri",
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
                "updated": "03 сентября 2026 года",
                "dates_aria_label": "Даты документа",
                "effective_label": "Дата вступления в силу",
                "updated_label": "Последнее обновление",
                "toc_title": "Оглавление",
                "hero_label": "Условия использования",
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
                "updated": "September 03, 2026",
                "dates_aria_label": "Document dates",
                "effective_label": "Effective date",
                "updated_label": "Last updated",
                "toc_title": "Table of Contents",
                "hero_label": "Terms of Service",
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
