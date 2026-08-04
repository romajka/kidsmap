"""Canonical public taxonomy used by the seed command and data migrations."""

CATEGORIES = [
    {"code": "SPRT", "ru": "Спорт", "az": "İdman", "en": "Sports", "icon": "icons/categories/sports.svg", "bg": "#E0F2FE", "text": "#0284C7"},
    {"code": "water-leisure", "ru": "Водный отдых", "az": "Su istirahəti", "en": "Water leisure", "icon": "icons/categories/waterparks.svg", "bg": "#DBEAFE", "text": "#2563EB"},
    {"code": "parks-playgrounds", "ru": "Парки и детские площадки", "az": "Parklar və uşaq meydançaları", "en": "Parks & playgrounds", "icon": "img/icon/cooliocns SVG/Environment/Leaf.svg", "bg": "#E8F5EE", "text": "#0C7A47"},
    {"code": "FUN", "ru": "Развлечения и досуг", "az": "Əyləncə və asudə vaxt", "en": "Entertainment & leisure", "icon": "img/icon/cooliocns SVG/Interface/Ticket_Voucher.svg", "bg": "#FFEDD5", "text": "#C2410C"},
    {"code": "ZOO", "ru": "Зоопарки", "az": "Zooparklar", "en": "Zoos", "icon": "icons/categories/zoo.svg", "bg": "#ECFCCB", "text": "#4D7C0F"},
    {"code": "museums-culture", "ru": "Музеи и культура", "az": "Muzeylər və mədəniyyət", "en": "Museums & culture", "icon": "img/icon/cooliocns SVG/Navigation/Building_04.svg", "bg": "#FEF3C7", "text": "#A16207"},
    {"code": "dance", "ru": "Танцульки", "az": "Rəqslər", "en": "Dance", "icon": "icons/categories/dance.svg", "bg": "#FFE4E6", "text": "#E11D48"},
    {"code": "EDU", "ru": "Образование", "az": "Təhsil", "en": "Education", "icon": "img/icon/cooliocns SVG/Interface/Book_Open.svg", "bg": "#E0E7FF", "text": "#4338CA"},
    {"code": "early-development", "ru": "Дошкольное развитие", "az": "Məktəbəqədər inkişaf", "en": "Preschool development", "icon": "icons/categories/early-development.svg", "bg": "#DCFCE7", "text": "#15803D"},
    {"code": "ART", "ru": "Творчество", "az": "Yaradıcılıq", "en": "Creativity", "icon": "img/icon/cooliocns SVG/Edit/Swatches_Palette.svg", "bg": "#FCE7F3", "text": "#BE185D"},
    {"code": "theater-stage", "ru": "Театр и сцена", "az": "Teatr və səhnə", "en": "Theater & stage", "icon": "img/icon/cooliocns SVG/User/User_Voice.svg", "bg": "#FCE7F3", "text": "#9D174D"},
    {"code": "MUS", "ru": "Музыка", "az": "Musiqi", "en": "Music", "icon": "icons/categories/music.svg", "bg": "#FAE8FF", "text": "#A21CAF"},
    {"code": "intellect-skills", "ru": "Интеллект и навыки", "az": "İntellekt və bacarıqlar", "en": "Intellect & skills", "icon": "img/icon/cooliocns SVG/Environment/Puzzle.svg", "bg": "#FEF3C7", "text": "#B45309"},
    {"code": "TECH", "ru": "Наука и технологии", "az": "Elm və texnologiyalar", "en": "Science & technology", "icon": "img/icon/cooliocns SVG/System/Code.svg", "bg": "#F3E8FF", "text": "#7E22CE"},
    {"code": "development-support", "ru": "Развитие и поддержка", "az": "İnkişaf və dəstək", "en": "Development & support", "icon": "img/icon/cooliocns SVG/Interface/Heart_01.svg", "bg": "#F3F4F6", "text": "#4B5563"},
    {"code": "CAMP", "ru": "Лагеря", "az": "Düşərgələr", "en": "Camps", "icon": "icons/categories/camp.svg", "bg": "#FFF3DF", "text": "#9A6700"},
    {"code": "excursions-tours", "ru": "Экскурсии и туры", "az": "Ekskursiyalar və turlar", "en": "Excursions & tours", "icon": "img/icon/cooliocns SVG/Navigation/Compass.svg", "bg": "#E0F2FE", "text": "#0369A1"},
]


SUBCATEGORIES = [
    # Спорт
    ("SPRT", "acrobatics", "Акробатика", "Akrobatika", "Acrobatics"),
    ("SPRT", "badminton", "Бадминтон", "Badminton", "Badminton"),
    ("SPRT", "basketball", "Баскетбол", "Basketbol", "Basketball"),
    ("SPRT", "boxing", "Бокс", "Boks", "Boxing"),
    ("SPRT", "cycling", "Велоспорт", "Velosiped idmanı", "Cycling"),
    ("SPRT", "volleyball", "Волейбол", "Voleybol", "Volleyball"),
    ("SPRT", "freestyle-wrestling", "Вольная борьба", "Sərbəst güləş", "Freestyle wrestling"),
    ("SPRT", "greco-roman-wrestling", "Греко-римская борьба", "Yunan-Roma güləşi", "Greco-Roman wrestling"),
    ("SPRT", "judo", "Дзюдо", "Cüdo", "Judo"),
    ("SPRT", "yoga", "Йога", "Yoqa", "Yoga"),
    ("SPRT", "karate", "Карате", "Karate", "Karate"),
    ("SPRT", "kickboxing", "Кикбоксинг", "Kikboksinq", "Kickboxing"),
    ("SPRT", "athletics", "Лёгкая атлетика", "Yüngül atletika", "Athletics"),
    ("SPRT", "table-tennis", "Настольный теннис", "Stolüstü tennis", "Table tennis"),
    ("SPRT", "kids-fitness-gpp", "Детский фитнес и ОФП", "Uşaq fitnesi və ümumi fiziki hazırlıq", "Kids fitness & general physical training"),
    ("SPRT", "swimming", "Плавание", "Üzgüçülük", "Swimming"),
    ("SPRT", "sambo", "Самбо", "Sambo", "Sambo"),
    ("SPRT", "artistic-gymnastics", "Спортивная гимнастика", "İdman gimnastikası", "Artistic gymnastics"),
    ("SPRT", "archery", "Стрельба из лука", "Oxatma", "Archery"),
    ("SPRT", "tennis", "Теннис", "Tennis", "Tennis"),
    ("SPRT", "taekwondo", "Тхэквондо", "Taekvondo", "Taekwondo"),
    ("SPRT", "weightlifting", "Тяжёлая атлетика", "Ağır atletika", "Weightlifting"),
    ("SPRT", "fencing", "Фехтование", "Qılıncoynatma", "Fencing"),
    ("SPRT", "figure-skating", "Фигурное катание", "Fiqurlu konkisürmə", "Figure skating"),
    ("SPRT", "football", "Футбол", "Futbol", "Football"),
    ("SPRT", "futsal", "Футзал", "Futzal", "Futsal"),
    ("SPRT", "rhythmic-gymnastics", "Художественная гимнастика", "Bədii gimnastika", "Rhythmic gymnastics"),
    # Водный отдых
    ("water-leisure", "waterparks", "Аквапарки", "Akvaparklar", "Waterparks"),
    ("water-leisure", "pools", "Бассейны", "Hovuzlar", "Pools"),
    ("water-leisure", "beaches-beach-clubs", "Пляжи и пляжные клубы", "Çimərliklər və çimərlik klubları", "Beaches & beach clubs"),
    ("water-leisure", "boat-trips", "Прогулки на лодках и катерах", "Qayıq və kater gəzintiləri", "Boat trips"),
    # Парки и площадки
    ("parks-playgrounds", "parks-boulevards", "Парки и бульвары", "Parklar və bulvarlar", "Parks & boulevards"),
    ("parks-playgrounds", "playgrounds", "Детские площадки", "Uşaq meydançaları", "Playgrounds"),
    ("parks-playgrounds", "botanical-gardens", "Ботанические сады", "Botanika bağları", "Botanical gardens"),
    ("parks-playgrounds", "national-parks", "Национальные парки", "Milli parklar", "National parks"),
    # Развлечения
    ("FUN", "amusement-parks", "Парки аттракционов", "Əyləncə parkları", "Amusement parks"),
    ("FUN", "kids-play-centers", "Детские игровые центры", "Uşaq oyun mərkəzləri", "Kids play centers"),
    ("FUN", "quests", "Квесты", "Kvestlər", "Quests"),
    ("FUN", "karting", "Картинг", "Kartinq", "Karting"),
    ("FUN", "laser-tag-paintball", "Лазертаг и пейнтбол", "Lazertaq və peyntbol", "Laser tag & paintball"),
    ("FUN", "cafes-kids-zone", "Кафе с детской зоной", "Uşaq zonalı kafelər", "Cafes with kids zones"),
    # Животные
    ("ZOO", "zoos", "Зоопарки", "Zooparklar", "Zoos"),
    ("ZOO", "petting-zoos", "Контактные зоопарки", "Təmas zooparkları", "Petting zoos"),
    ("ZOO", "safari-parks", "Сафари-парки", "Safari parkları", "Safari parks"),
    ("ZOO", "animal-farms", "Фермы с животными", "Heyvan fermaları", "Animal farms"),
    ("ZOO", "aquariums-oceanariums", "Аквариумы и океанариумы", "Akvariumlar və okeanariumlar", "Aquariums & oceanariums"),
    # Музеи
    ("museums-culture", "house-museums", "Дома-музеи", "Ev-muzeyləri", "House museums"),
    ("museums-culture", "historical-complexes-fortresses", "Исторические комплексы и крепости", "Tarixi komplekslər və qalalar", "Historical complexes & fortresses"),
    ("museums-culture", "history-museums", "Исторические музеи", "Tarix muzeyləri", "History museums"),
    ("museums-culture", "science-interactive-museums", "Научные и интерактивные музеи", "Elm və interaktiv muzeylər", "Science & interactive museums"),
    ("museums-culture", "planetariums-observatories", "Планетарии и обсерватории", "Planetariumlar və rəsədxanalar", "Planetariums & observatories"),
    ("museums-culture", "art-museums-galleries", "Художественные музеи и галереи", "İncəsənət muzeyləri və qalereyalar", "Art museums & galleries"),
    # Танцы
    ("dance", "ballet", "Балет", "Balet", "Ballet"),
    ("dance", "ballroom-dance", "Бальные танцы", "Balo rəqsləri", "Ballroom dance"),
    ("dance", "kids-choreography", "Детская хореография", "Uşaq xoreoqrafiyası", "Kids choreography"),
    ("dance", "folk-dance", "Народные танцы", "Xalq rəqsləri", "Folk dance"),
    ("dance", "modern-dance", "Современные танцы", "Müasir rəqslər", "Modern dance"),
    # Образование
    ("EDU", "language-az", "Азербайджанский язык", "Azərbaycan dili", "Azerbaijani language"),
    ("EDU", "language-en", "Английский язык", "İngilis dili", "English language"),
    ("EDU", "language-ru", "Русский язык", "Rus dili", "Russian language"),
    ("EDU", "other-foreign-languages", "Другие иностранные языки", "Digər xarici dillər", "Other foreign languages"),
    ("EDU", "school-subjects", "Школьные предметы", "Məktəb fənləri", "School subjects"),
    ("EDU", "exam-preparation", "Подготовка к экзаменам", "İmtahanlara hazırlıq", "Exam preparation"),
    ("EDU", "after-school-homework", "Продлёнка и домашние задания", "Günü uzadılmış qrup və ev tapşırıqları", "After-school care & homework"),
    # Дошкольное развитие
    ("early-development", "kindergartens", "Детские сады", "Uşaq bağçaları", "Kindergartens"),
    ("early-development", "montessori", "Монтессори", "Montessori", "Montessori"),
    ("early-development", "sensory-development", "Сенсорное развитие", "Sensor inkişaf", "Sensory development"),
    ("early-development", "school-prep", "Подготовка к школе", "Məktəbə hazırlıq", "School preparation"),
    # Творчество
    ("ART", "drawing-painting", "Рисование и живопись", "Rəsm və rəngkarlıq", "Drawing & painting"),
    ("ART", "clay-sculpture", "Лепка, керамика и скульптура", "Gil, keramika və heykəltəraşlıq", "Clay, ceramics & sculpture"),
    ("ART", "handicrafts", "Рукоделие", "Əl işləri", "Handicrafts"),
    ("ART", "design-modeling", "Дизайн и моделирование", "Dizayn və modelləşdirmə", "Design & modeling"),
    # Театр
    ("theater-stage", "theater-acting", "Театр и актёрское мастерство", "Teatr və aktyor sənəti", "Theater & acting"),
    ("theater-stage", "stage-speech", "Сценическая речь", "Səhnə nitqi", "Stage speech"),
    # Музыка
    ("MUS", "vocal", "Вокал", "Vokal", "Vocal"),
    ("MUS", "keyboards", "Клавишные инструменты", "Klavişli alətlər", "Keyboard instruments"),
    ("MUS", "string-instruments", "Струнные инструменты", "Simli alətlər", "String instruments"),
    ("MUS", "wind-instruments", "Духовые инструменты", "Nəfəs alətləri", "Wind instruments"),
    ("MUS", "percussion-instruments", "Ударные инструменты", "Zərb alətləri", "Percussion instruments"),
    # Интеллект
    ("intellect-skills", "chess-checkers", "Шахматы и шашки", "Şahmat və dama", "Chess & checkers"),
    ("intellect-skills", "mental-arithmetic", "Ментальная арифметика", "Mental arifmetika", "Mental arithmetic"),
    ("intellect-skills", "speed-reading", "Скорочтение", "Sürətli oxu", "Speed reading"),
    ("intellect-skills", "logic-puzzles", "Логика и головоломки", "Məntiq və tapmacalar", "Logic & puzzles"),
    ("intellect-skills", "memory-concentration", "Память и концентрация", "Yaddaş və diqqət", "Memory & concentration"),
    ("intellect-skills", "debates-public-speaking", "Дебаты и ораторское мастерство", "Debatlar və natiqlik", "Debates & public speaking"),
    # Наука и технологии
    ("TECH", "programming", "Программирование", "Proqramlaşdırma", "Programming"),
    ("TECH", "robotics", "Робототехника", "Robototexnika", "Robotics"),
    ("TECH", "lego-construction", "LEGO-конструирование", "LEGO konstruksiyası", "LEGO construction"),
    ("TECH", "3d-modeling", "3D-моделирование и 3D-печать", "3D modelləşdirmə və 3D çap", "3D modeling & printing"),
    ("TECH", "science-experiments", "Научные эксперименты", "Elmi təcrübələr", "Science experiments"),
    # Поддержка
    ("development-support", "speech-therapist", "Логопед", "Loqoped", "Speech therapist"),
    ("development-support", "child-psychologist", "Детский психолог", "Uşaq psixoloqu", "Child psychologist"),
    ("development-support", "neuropsychologist", "Нейропсихолог", "Neyropsixoloq", "Neuropsychologist"),
    ("development-support", "defectologist", "Дефектолог", "Defektoloq", "Special education therapist"),
    ("development-support", "occupational-therapy", "Эрготерапия", "Erqoterapiya", "Occupational therapy"),
    ("development-support", "aba-therapy", "ABA-терапия", "ABA terapiyası", "ABA therapy"),
    ("development-support", "sensory-integration", "Сенсорная интеграция", "Sensor inteqrasiyası", "Sensory integration"),
    ("development-support", "adaptive-physical-education", "Адаптивная физкультура", "Adaptiv bədən tərbiyəsi", "Adaptive physical education"),
    ("development-support", "pediatric-physical-rehabilitation", "Детская физическая реабилитация", "Uşaq fiziki reabilitasiyası", "Pediatric physical rehabilitation"),
    # Лагеря
    ("CAMP", "day-camps", "Дневные лагеря", "Gündüz düşərgələri", "Day camps"),
    ("CAMP", "residential-camps", "Лагеря с проживанием", "Yaşayışlı düşərgələr", "Residential camps"),
    # Экскурсии
    ("excursions-tours", "excursions", "Экскурсии", "Ekskursiyalar", "Excursions"),
    ("excursions-tours", "tours", "Туры", "Turlar", "Tours"),
    ("excursions-tours", "outdoor-adventures", "Приключения на природе", "Təbiət macəraları", "Outdoor adventures"),
]


def category_seed_rows():
    return [
        {
            "code": item["code"],
            "name": item["ru"],
            "name_ru": item["ru"],
            "name_az": item["az"],
            "name_en": item["en"],
            "icon": item["icon"],
            "color_bg": item["bg"],
            "color_text": item["text"],
            "is_active": True,
            "order": order,
        }
        for order, item in enumerate(CATEGORIES, start=1)
    ]


def subcategory_seed_rows():
    counters = {}
    rows = []
    for category, code, ru, az, en in SUBCATEGORIES:
        counters[category] = counters.get(category, 0) + 1
        rows.append(
            {
                "cat": category,
                "code": code,
                "ru": ru,
                "az": az,
                "en": en,
                "order": counters[category],
                "is_active": True,
            }
        )
    return rows


PUBLIC_CATEGORY_CODES = tuple(item["code"] for item in CATEGORIES)
