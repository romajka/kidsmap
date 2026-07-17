from django.utils.translation import gettext_lazy as _


AZERBAIJAN_REGIONS = [
    _("Баку"),
    _("Ясамал"),
    _("Насими"),
    _("Низами"),
    _("Нариманов"),
    _("Сабаиль"),
    _("Сабунчи"),
    _("Бинагади"),
    _("Сураханы"),
    _("Хатаи"),
    _("Хазар"),
    _("Гарадаг"),
    _("Пираллахы"),
    _("Абшерон"),
    _("Агджабеди"),
    _("Агдам"),
    _("Агдаш"),
    _("Агстафа"),
    _("Агсу"),
    _("Астара"),
    _("Бабек"),
    _("Балакен"),
    _("Барда"),
    _("Бейлаган"),
    _("Билясувар"),
    _("Габала"),
    _("Гаджикабул"),
    _("Газах"),
    _("Гах"),
    _("Гедабек"),
    _("Гянджа"),
    _("Гёйгёль"),
    _("Гёйчай"),
    _("Гобустан"),
    _("Горанбой"),
    _("Губа"),
    _("Губадлы"),
    _("Гусар"),
    _("Дашкесан"),
    _("Джебраил"),
    _("Джалилабад"),
    _("Джульфа"),
    _("Евлах"),
    _("Загатала"),
    _("Зангилан"),
    _("Зардаб"),
    _("Имишли"),
    _("Исмаиллы"),
    _("Кельбаджар"),
    _("Кенгерли"),
    _("Кюрдамир"),
    _("Лачин"),
    _("Ленкорань"),
    _("Лерик"),
    _("Масаллы"),
    _("Мингячевир"),
    _("Нахчыван"),
    _("Нафталан"),
    _("Нефтчала"),
    _("Огуз"),
    _("Ордубад"),
    _("Саатлы"),
    _("Сабирабад"),
    _("Садарак"),
    _("Сальян"),
    _("Самух"),
    _("Сиазань"),
    _("Сумгаит"),
    _("Тертер"),
    _("Товуз"),
    _("Уджар"),
    _("Физули"),
    _("Хачмаз"),
    _("Ходжавенд"),
    _("Ходжалы"),
    _("Хызы"),
    _("Шабран"),
    _("Шамахы"),
    _("Шамкир"),
    _("Шарур"),
    _("Шахбуз"),
    _("Шеки"),
    _("Ширван"),
    _("Шуша"),
    _("Ярдымлы"),
]

# Backward-compatible name for older imports and existing tests.
BAKU_DISTRICTS = AZERBAIJAN_REGIONS

BAKU_METRO_STATIONS = [
    _("Ичеришехер"),
    _("Сахил"),
    _("28 Май"),
    _("Гянджлик"),
    _("Нариман Нариманов"),
    _("Бакмил"),
    _("Улдуз"),
    _("Кёроглу"),
    _("Гара Гараев"),
    _("Нефтчиляр"),
    _("Халглар Достлугу"),
    _("Ахмедлы"),
    _("Ази Асланов"),
    _("Низами"),
    _("Эльмляр Академиясы"),
    _("Иншаатчылар"),
    _("20 Января"),
    _("Мемар Аджеми"),
    _("Насими"),
    _("Азадлыг Проспекти"),
    _("Дернегюль"),
    _("Джафар Джаббарлы"),
    _("Шах Исмаил Хатаи"),
    _("Мемар Аджеми-2"),
    _("Автовагзал"),
    _("8 Ноября"),
    _("Ходжасан"),
]

AZERBAIJAN_REGION_SEO = [
    ("baku", "Баку"),
    ("absheron", "Абшерон"),
    ("sumgait", "Сумгаит"),
    ("ganja", "Гянджа"),
    ("mingachevir", "Мингячевир"),
    ("shirvan", "Ширван"),
    ("lankaran", "Ленкорань"),
    ("sheki", "Шеки"),
    ("yevlakh", "Евлах"),
    ("nakhchivan", "Нахчыван"),
    ("gabala", "Габала"),
    ("guba", "Губа"),
    ("qusar", "Гусар"),
    ("shamakhi", "Шамахы"),
    ("zagatala", "Загатала"),
    ("masalli", "Масаллы"),
]

# Backward-compatible name for older imports.
BAKU_DISTRICT_SEO = AZERBAIJAN_REGION_SEO

HOME_CATEGORIES = [
    {"code": "SPRT", "title": _("Спорт")},
    {"code": "ART", "title": _("Творчество")},
    {"code": "MUS", "title": _("Музыка и сцена")},
    {"code": "EDU", "title": _("Образование")},
    {"code": "TECH", "title": _("Технологии")},
    {"code": "FUN", "title": _("Досуг")},
]

SEO_LANDING_PAGE_COPY = {
    "ru": {
    "kruzhki-v-baku": {
        "title": "Кружки в Баку для детей",
        "meta_description": "Кружки в Баку для детей: спорт, творчество, музыка и технологии. Сравнивайте по району, возрасту и цене на KidsMap.",
        "intro": "Подборка детских кружков в Баку с фильтрами по району, метро, возрасту и бюджету. Откройте карточку места и свяжитесь с ним напрямую.",
        "benefits": [
            "Кружки по спорту, музыке, творчеству и технологиям",
            "Фильтрация по району, метро и возрасту ребенка",
            "Сравнение стоимости до звонка или записи",
        ],
        "catalog_query": "?district=baku",
        "faq": [
            ("Как выбрать кружок для ребенка в Баку?", "Сначала определите цель: развитие, спорт или подготовка к школе. Затем сравните места по району, возрасту и цене."),
            ("С какого возраста лучше начинать кружки?", "Чаще всего с 4-6 лет, но это зависит от направления. В карточках можно отфильтровать возрастные границы."),
        ],
    },
    "kruzhki-v-azerbaydzhane": {
        "title": "Кружки в Азербайджане для детей",
        "meta_description": "Кружки в Азербайджане для детей: спорт, творчество, музыка, технологии. Сравнивайте по региону, возрасту и цене на KidsMap.",
        "intro": "На этой странице собраны детские кружки по Азербайджану с удобным фильтром по возрасту, региону и бюджету. Можно быстро перейти в карточку и связаться с местом.",
        "benefits": [
            "Кружки по спорту, музыке, творчеству и технологиям",
            "Фильтрация по региону, метро и возрасту ребенка",
            "Сравнение стоимости до звонка или записи",
        ],
        "catalog_query": "",
        "faq": [
            ("Как выбрать кружок для ребенка в Азербайджане?", "Сначала определите цель: развитие, спорт или подготовка к школе. Затем сравните места по региону, возрасту и цене."),
            ("С какого возраста лучше начинать кружки?", "Чаще всего с 4-6 лет, но это зависит от направления. В карточках можно отфильтровать возрастные границы."),
        ],
    },
    "kursy-dlya-detey-v-baku": {
        "title": "Курсы для детей в Баку",
        "meta_description": "Курсы для детей в Баку: языки, программирование, творчество и подготовка. Найдите подходящий курс на KidsMap.",
        "intro": "Подборка детских курсов в Баку для школьников и дошкольников. На KidsMap можно сравнить курсы по стоимости, району и формату занятий.",
        "benefits": [
            "Курсы по образованию, технологиям и творческим направлениям",
            "Удобный поиск рядом с домом или школой",
            "Быстрый переход к контактам и расписанию",
        ],
        "catalog_query": "?category=EDU",
        "faq": [
            ("Какие курсы популярны для детей в Баку?", "Чаще всего выбирают языковые курсы, подготовку к школе, программирование и математику."),
            ("Как понять, что курс подходит ребенку?", "Проверьте возраст, программу, формат уроков и нагрузку. Лучше сравнить 2-3 варианта перед выбором."),
        ],
    },
    "sportivnye-sekcii-v-baku": {
        "title": "Спортивные секции в Баку для детей",
        "meta_description": "Спортивные секции в Баку для детей: футбол, гимнастика, боевые искусства и другие направления. Выберите по району и цене.",
        "intro": "Секции для активных детей в Баку: от базовой физической подготовки до соревновательных направлений. Смотрите условия и выбирайте по району.",
        "benefits": [
            "Секции для разного возраста и уровня подготовки",
            "Фильтры по району и стоимости занятий",
            "Контакты клубов в одном месте",
        ],
        "catalog_query": "?category=SPRT",
        "faq": [
            ("Какая секция лучше для начинающего?", "Для старта обычно выбирают плавание, гимнастику или общую физподготовку. Главное учитывать интерес ребенка."),
            ("Сколько раз в неделю оптимально заниматься спортом?", "Обычно 2-3 раза в неделю достаточно для прогресса без перегрузки."),
        ],
    },
    "tvorcheskie-kruzhki-v-baku": {
        "title": "Творческие кружки в Баку для детей",
        "meta_description": "Творческие кружки в Баку для детей: рисование, лепка, актерское мастерство и музыка. Найдите занятия рядом с вами.",
        "intro": "Творческие занятия помогают ребенку развивать воображение, речь и уверенность. В каталоге можно выбрать кружки по району, возрасту и цене.",
        "benefits": [
            "Рисование, лепка, театр, музыка и другие направления",
            "Подбор по возрасту ребенка",
            "Сравнение форматов и стоимости занятий",
        ],
        "catalog_query": "?category=ART",
        "faq": [
            ("Что дают ребенку творческие кружки?", "Они развивают креативность, мелкую моторику, коммуникацию и уверенность в себе."),
            ("Нужно ли иметь талант для начала?", "Нет, большинство кружков рассчитаны на старт с нуля и постепенное развитие."),
        ],
    },
    "programmirovanie-dlya-detey-baku": {
        "title": "Программирование для детей в Баку",
        "meta_description": "Программирование для детей в Баку: курсы Scratch, Python, робототехника и STEM-направления. Подберите курс по возрасту и району.",
        "intro": "Детские IT-курсы в Баку: визуальное программирование, основы кода и проектная работа. Сравнивайте школы по цене, району и возрасту.",
        "benefits": [
            "Курсы Scratch, Python, робототехники и STEM",
            "Программы для новичков и продолжающих",
            "Удобный поиск IT-направлений рядом",
        ],
        "catalog_query": "?category=TECH",
        "faq": [
            ("С какого возраста ребенку можно на программирование?", "Обычно с 7-8 лет, а визуальные форматы возможны и раньше."),
            ("Что выбрать первым: Scratch или Python?", "Для начала чаще выбирают Scratch, потом переходят к Python."),
        ],
    },
    },
    "az": {
        "kruzhki-v-baku": {"title": "Bakıda uşaqlar üçün dərnəklər", "meta_description": "Bakıda uşaqlar üçün idman, yaradıcılıq, musiqi və texnologiya dərnəkləri. KidsMap-da rayon, yaş və qiymətə görə müqayisə edin.", "intro": "Bakıda uşaq dərnəklərini rayon, metro, yaş və büdcəyə görə seçin. Məkan kartını açın və birbaşa əlaqə saxlayın.", "benefits": ["İdman, musiqi, yaradıcılıq və texnologiya dərnəkləri", "Rayon, metro və uşağın yaşına görə filtr", "Əlaqə saxlamazdan əvvəl qiymətləri müqayisə edin"], "catalog_query": "?district=baku", "faq": [("Bakıda uşaq üçün dərnəyi necə seçmək olar?", "Əvvəlcə məqsədi müəyyən edin: inkişaf, idman və ya məktəbə hazırlıq. Sonra rayon, yaş və qiymətə görə məkanları müqayisə edin."), ("Dərnəyə neçə yaşdan başlamaq olar?", "Çox vaxt 4-6 yaşdan başlamaq olur, amma bu istiqamətdən asılıdır. Kartlarda yaş hədlərini filtr edə bilərsiniz.")]},
        "kruzhki-v-azerbaydzhane": {"title": "Azərbaycanda uşaqlar üçün dərnəklər", "meta_description": "Azərbaycanda uşaqlar üçün idman, yaradıcılıq, musiqi və texnologiya dərnəkləri. KidsMap-da region, yaş və qiymətə görə müqayisə edin.", "intro": "Azərbaycandakı uşaq dərnəklərini region, yaş və büdcəyə görə seçin. Məkan kartını açın və birbaşa əlaqə saxlayın.", "benefits": ["İdman, musiqi, yaradıcılıq və texnologiya dərnəkləri", "Region, metro və uşağın yaşına görə filtr", "Əlaqə saxlamazdan əvvəl qiymətləri müqayisə edin"], "catalog_query": "", "faq": [("Azərbaycanda uşaq üçün dərnəyi necə seçmək olar?", "Əvvəlcə məqsədi müəyyən edin: inkişaf, idman və ya məktəbə hazırlıq. Sonra region, yaş və qiymətə görə məkanları müqayisə edin."), ("Dərnəyə neçə yaşdan başlamaq olar?", "Çox vaxt 4-6 yaşdan başlamaq olur, amma bu istiqamətdən asılıdır. Kartlarda yaş hədlərini filtr edə bilərsiniz.")]},
        "kursy-dlya-detey-v-baku": {"title": "Bakıda uşaqlar üçün kurslar", "meta_description": "Bakıda uşaqlar üçün dil, proqramlaşdırma, yaradıcılıq və məktəbə hazırlıq kursları. KidsMap-da uyğun kursu tapın.", "intro": "Məktəbəqədər və məktəbli uşaqlar üçün Bakıda kurslar. KidsMap-da qiymət, rayon və məşğələ formatına görə müqayisə edin.", "benefits": ["Təhsil, texnologiya və yaradıcılıq kursları", "Evə və ya məktəbə yaxın axtarış", "Əlaqələrə və cədvələ sürətli keçid"], "catalog_query": "?category=EDU", "faq": [("Bakıda uşaqlar üçün hansı kurslar populyardır?", "Dil kursları, məktəbə hazırlıq, proqramlaşdırma və riyaziyyat daha çox seçilir."), ("Kursun uşağa uyğun olduğunu necə anlamaq olar?", "Yaşı, proqramı, dərs formatını və yükü yoxlayın. Seçimdən əvvəl 2-3 variantı müqayisə etmək yaxşıdır.")]},
        "sportivnye-sekcii-v-baku": {"title": "Bakıda uşaqlar üçün idman bölmələri", "meta_description": "Bakıda uşaqlar üçün futbol, gimnastika, döyüş sənəti və digər idman bölmələri. Rayon və qiymətə görə seçim edin.", "intro": "Bakıda fəal uşaqlar üçün idman bölmələri: ümumi fiziki hazırlıqdan yarış istiqamətlərinə qədər. Məkanı və şərtləri müqayisə edin.", "benefits": ["Fərqli yaş və hazırlıq səviyyələri üçün bölmələr", "Rayon və məşğələ qiymətinə görə filtr", "Klubların əlaqələri bir yerdə"], "catalog_query": "?category=SPRT", "faq": [("Başlayan uşaq üçün hansı bölmə daha uyğundur?", "Başlamaq üçün adətən üzgüçülük, gimnastika və ya ümumi fiziki hazırlıq seçilir. Uşağın marağını nəzərə almaq əsasdır."), ("Həftədə neçə dəfə idmanla məşğul olmaq yaxşıdır?", "Həddindən artıq yüklənmədən irəliləyiş üçün adətən həftədə 2-3 dəfə kifayətdir.")]},
        "tvorcheskie-kruzhki-v-baku": {"title": "Bakıda uşaqlar üçün yaradıcılıq dərnəkləri", "meta_description": "Bakıda uşaqlar üçün rəsm, gil işi, teatr və musiqi dərnəkləri. Yaxınlıqdakı məşğələni KidsMap-da tapın.", "intro": "Yaradıcılıq məşğələləri uşağın təxəyyülünü, nitqini və özünə inamını inkişaf etdirir. Kataloqda yaşa, rayona və qiymətə görə seçin.", "benefits": ["Rəsm, gil işi, teatr, musiqi və digər istiqamətlər", "Uşağın yaşına görə seçim", "Format və qiymətlərin müqayisəsi"], "catalog_query": "?category=ART", "faq": [("Yaradıcılıq dərnəkləri uşağa nə verir?", "Onlar yaradıcılığı, xırda motorikanı, ünsiyyəti və özünə inamı inkişaf etdirir."), ("Başlamaq üçün istedad lazımdır?", "Xeyr, əksər dərnəklər sıfırdan başlamaq və tədricən inkişaf üçün nəzərdə tutulub.")]},
        "programmirovanie-dlya-detey-baku": {"title": "Bakıda uşaqlar üçün proqramlaşdırma", "meta_description": "Bakıda uşaqlar üçün Scratch, Python, robototexnika və STEM kursları. Yaşa və rayona görə uyğun kursu seçin.", "intro": "Bakıda uşaqlar üçün IT-kursları: vizual proqramlaşdırma, kodun əsasları və layihə işi. Məktəbləri qiymət, rayon və yaşa görə müqayisə edin.", "benefits": ["Scratch, Python, robototexnika və STEM kursları", "Yeni başlayanlar və davam edənlər üçün proqramlar", "Yaxınlıqdakı IT istiqamətlərinin rahat axtarışı"], "catalog_query": "?category=TECH", "faq": [("Uşaq neçə yaşdan proqramlaşdırmaya başlaya bilər?", "Adətən 7-8 yaşdan, vizual formatlarla isə daha erkən başlamaq mümkündür."), ("İlk olaraq Scratch, yoxsa Python seçmək lazımdır?", "Başlanğıc üçün çox vaxt Scratch, sonra isə Python seçilir.")]},
    },
    "en": {
        "kruzhki-v-baku": {"title": "Kids' clubs in Baku", "meta_description": "Kids' clubs in Baku: sports, arts, music and technology. Compare by district, age and price on KidsMap.", "intro": "Find kids' clubs in Baku using district, metro, age and budget filters. Open a listing and contact the venue directly.", "benefits": ["Sports, music, arts and technology clubs", "Filters by district, metro and child age", "Compare prices before you call or enrol"], "catalog_query": "?district=baku", "faq": [("How do I choose a club for my child in Baku?", "Start with the goal: development, sports or school preparation. Then compare venues by district, age and price."), ("What age can children start clubs?", "Many clubs start from ages 4-6, but it depends on the activity. Use the listings to filter age ranges.")]},
        "kruzhki-v-azerbaydzhane": {"title": "Kids' clubs in Azerbaijan", "meta_description": "Kids' clubs in Azerbaijan: sports, arts, music and technology. Compare by region, age and price on KidsMap.", "intro": "Find kids' clubs across Azerbaijan using region, age and budget filters. Open a listing and contact the venue directly.", "benefits": ["Sports, music, arts and technology clubs", "Filters by region, metro and child age", "Compare prices before you call or enrol"], "catalog_query": "", "faq": [("How do I choose a club for my child in Azerbaijan?", "Start with the goal: development, sports or school preparation. Then compare venues by region, age and price."), ("What age can children start clubs?", "Many clubs start from ages 4-6, but it depends on the activity. Use the listings to filter age ranges.")]},
        "kursy-dlya-detey-v-baku": {"title": "Courses for children in Baku", "meta_description": "Courses for children in Baku: languages, coding, arts and school preparation. Find the right course on KidsMap.", "intro": "Courses in Baku for preschool and school-age children. Compare them on KidsMap by price, district and class format.", "benefits": ["Education, technology and arts courses", "Search close to home or school", "Quick access to contacts and schedules"], "catalog_query": "?category=EDU", "faq": [("Which children's courses are popular in Baku?", "Language courses, school preparation, coding and maths are among the most popular choices."), ("How can I tell whether a course suits my child?", "Check the age range, programme, lesson format and workload. Compare two or three options before deciding.")]},
        "sportivnye-sekcii-v-baku": {"title": "Sports clubs for children in Baku", "meta_description": "Sports clubs for children in Baku: football, gymnastics, martial arts and more. Choose by district and price.", "intro": "Sports clubs in Baku for active children, from general fitness to competitive activities. Compare locations and conditions.", "benefits": ["Clubs for different ages and experience levels", "Filters by district and class price", "Club contacts in one place"], "catalog_query": "?category=SPRT", "faq": [("Which sport is best for a beginner?", "Swimming, gymnastics or general fitness are often good first choices. Your child's interest matters most."), ("How many sports classes a week are ideal?", "Two or three sessions a week are usually enough to make progress without overload.")]},
        "tvorcheskie-kruzhki-v-baku": {"title": "Creative clubs for children in Baku", "meta_description": "Creative clubs for children in Baku: drawing, modelling, theatre and music. Find a nearby activity on KidsMap.", "intro": "Creative activities develop a child's imagination, speech and confidence. Browse the catalogue by age, district and price.", "benefits": ["Drawing, modelling, theatre, music and more", "Choose by your child's age", "Compare formats and prices"], "catalog_query": "?category=ART", "faq": [("What do creative clubs give children?", "They develop creativity, fine motor skills, communication and confidence."), ("Does a child need talent to start?", "No. Most clubs are designed for beginners and gradual development.")]},
        "programmirovanie-dlya-detey-baku": {"title": "Programming for children in Baku", "meta_description": "Programming for children in Baku: Scratch, Python, robotics and STEM courses. Choose by age and district.", "intro": "IT courses in Baku for children: visual programming, coding basics and project work. Compare schools by price, district and age.", "benefits": ["Scratch, Python, robotics and STEM courses", "Programmes for beginners and continuing learners", "Easy search for nearby IT activities"], "catalog_query": "?category=TECH", "faq": [("What age can a child start programming?", "Children often start at ages 7-8, while visual programming can begin earlier."), ("Should a child start with Scratch or Python?", "Scratch is usually the first step, followed by Python.")]},
    },
}


def base_seo_landing_pages(language_code="az"):
    return SEO_LANDING_PAGE_COPY.get(language_code, SEO_LANDING_PAGE_COPY["az"])


def district_seo_pages(language_code="az"):
    language_code = language_code if language_code in {"az", "ru", "en"} else "az"
    from catalog.services.locations import get_location_translation

    pages = {}
    for slug, _district in AZERBAIJAN_REGION_SEO:
        district = get_location_translation(slug, language_code)
        if language_code == "az":
            title = f"{district} regionunda uşaqlar üçün dərnəklər"
            description = f"{district} regionunda uşaqlar üçün dərnək və bölmələr. KidsMap-da yaşa, qiymətə və məkana görə müqayisə edin."
            intro = f"{district} regionunda uşaqlar üçün dərnək və kurs seçimi. Yaxınlıqdakı variantı tapmaq üçün yaş, metro və qiymət filtrlərindən istifadə edin."
            benefits = [f"{district} regionunda uşaq dərnək və bölmələri", "Qiymət və yaş qruplarının müqayisəsi", "Əlaqələr və karta sürətli keçid"]
            faq = [(f"{district} regionunda hansı dərnəklər var?", "Səhifədə idman, təhsil və yaradıcılıq istiqamətləri toplanıb."), ("Evə yaxın dərnəyi necə seçmək olar?", "Region və metro filtrindən istifadə edin, sonra yaşı, qiyməti və cədvəli müqayisə edin.")]
        elif language_code == "en":
            title = f"Kids' clubs in the {district} region"
            description = f"Kids' clubs and activities in the {district} region. Compare by age, price and location on KidsMap."
            intro = f"A selection of children's clubs and courses in the {district} region. Use age, metro and price filters to find a nearby option."
            benefits = [f"Kids' clubs and activities in the {district} region", "Compare prices and age groups", "Contacts and quick access to listings"]
            faq = [(f"Which clubs are available in the {district} region?", "The page includes sports, education and creative activities."), ("How do I choose a club close to home?", "Use the region and metro filters, then compare age, price and schedule.")]
        else:
            title = f"Кружки для детей в регионе {district}"
            description = f"Кружки и секции для детей в регионе {district}. Сравнивайте по возрасту, цене и локации на KidsMap."
            intro = f"Подборка кружков и курсов для детей в регионе {district}. Используйте фильтры по возрасту, метро и цене, чтобы выбрать лучший вариант рядом."
            benefits = [f"Детские кружки и секции в регионе {district}", "Сравнение цен и возрастных групп", "Контакты и быстрый переход к карточке"]
            faq = [(f"Какие кружки есть в регионе {district}?", "На странице собраны спортивные, образовательные и творческие направления."), ("Как выбрать кружок рядом с домом?", "Используйте фильтр по региону и метро, затем сравните возраст, цену и расписание.")]
        page_slug = f"kruzhki-v-{slug}-azerbaydzhan"
        pages[page_slug] = {
            "title": title,
            "meta_description": description,
            "intro": intro,
            "benefits": benefits,
            "catalog_query": f"?district={slug}",
            "faq": faq,
        }
    return pages


def seo_landing_pages(language_code="az"):
    return {**base_seo_landing_pages(language_code), **district_seo_pages(language_code)}


SEO_LANDING_PAGES = seo_landing_pages()
