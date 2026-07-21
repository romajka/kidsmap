from django.core.management.base import BaseCommand
from django.db import transaction
from catalog.models import Category, Subcategory
from catalog.models.category import NEUTRAL_BG_VALUES, NEUTRAL_TEXT_VALUES

class Command(BaseCommand):
    help = (
        "Seeds catalog taxonomy: Categories and Subcategories. "
        "By default, skips seeding if data already exists (idempotent). "
        "Use --force to overwrite. NEVER run without --force on a live production database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-icons',
            action='store_true',
            help='Force update icons for existing categories, overwriting custom ones',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help=(
                'Run even if categories already exist. '
                'WARNING: updates names/icons/colors but NEVER touches is_active of existing records.'
            ),
        )

    def handle(self, *args, **options):
        update_icons = options['update_icons']
        force = options['force']

        # Safety guard: skip if data already exists and --force is not given.
        # This prevents accidentally overwriting production admin changes on every deploy.
        if not force and Category.objects.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Categories already exist. Skipping seed to protect production data.\n"
                    "Use --force to seed anyway (does NOT restore archived categories)."
                )
            )
            return


        categories_data = [
            {
                "code": "early-development",
                "name": "Раннее развитие",
                "name_az": "Erkən inkişaf",
                "name_ru": "Раннее развитие",
                "name_en": "Early development",
                "icon": "icons/categories/early-development.svg",
                "color_bg": "#DCFCE7",
                "color_text": "#15803D",
                "is_active": True,
                "order": 1,
            },
            {
                "code": "EDU",
                "name": "Образование",
                "name_az": "Təhsil",
                "name_ru": "Образование",
                "name_en": "Education",
                "icon": "img/icon/cooliocns SVG/Interface/Book_Open.svg",
                "color_bg": "#E0E7FF",
                "color_text": "#4338CA",
                "is_active": True,
                "order": 2,
            },
            {
                "code": "SPRT",
                "name": "Спорт",
                "name_az": "İdman",
                "name_ru": "Спорт",
                "name_en": "Sports",
                "icon": "icons/categories/sports.svg",
                "color_bg": "#E0F2FE",
                "color_text": "#0284C7",
                "is_active": True,
                "order": 3,
            },
            {
                "code": "dance",
                "name": "Танцы",
                "name_az": "Rəqs",
                "name_ru": "Танцы",
                "name_en": "Dance",
                "icon": "icons/categories/dance.svg",
                "color_bg": "#FFE4E6",
                "color_text": "#E11D48",
                "is_active": True,
                "order": 4,
            },
            {
                "code": "MUS",
                "name": "Музыка и сцена",
                "name_az": "Musiqi və səhnə",
                "name_ru": "Музыка и сцена",
                "name_en": "Music & stage",
                "icon": "icons/categories/music.svg",
                "color_bg": "#FAE8FF",
                "color_text": "#A21CAF",
                "is_active": True,
                "order": 5,
            },
            {
                "code": "TECH",
                "name": "Технологии",
                "name_az": "Texnologiya",
                "name_ru": "Технологии",
                "name_en": "Technology",
                "icon": "img/icon/cooliocns SVG/System/Code.svg",
                "color_bg": "#F3E8FF",
                "color_text": "#7E22CE",
                "is_active": True,
                "order": 6,
            },
            {
                "code": "ART",
                "name": "Творчество",
                "name_az": "Yaradıcılıq",
                "name_ru": "Творчество",
                "name_en": "Creativity",
                "icon": "img/icon/cooliocns SVG/Edit/Swatches_Palette.svg",
                "color_bg": "#FCE7F3",
                "color_text": "#BE185D",
                "is_active": True,
                "order": 7,
            },
            {
                "code": "intellect-skills",
                "name": "Интеллект и навыки",
                "name_az": "İntellekt və bacarıqlar",
                "name_ru": "Интеллект и навыки",
                "name_en": "Intellect & skills",
                "icon": "img/icon/cooliocns SVG/Environment/Puzzle.svg",
                "color_bg": "#FEF3C7",
                "color_text": "#B45309",
                "is_active": True,
                "order": 8,
            },
            {
                "code": "development-support",
                "name": "Развитие и поддержка",
                "name_az": "İnkişaf və dəstək",
                "name_ru": "Развитие и поддержка",
                "name_en": "Development & support",
                "icon": "img/icon/cooliocns SVG/Interface/Heart_01.svg",
                "color_bg": "#F3F4F6",
                "color_text": "#6B7280",
                "is_active": False,
                "order": 9,
            },
            {
                "code": "FUN",
                "name": "Развлечения и досуг",
                "name_az": "Əyləncə və asudə",
                "name_ru": "Развлечения и досуг",
                "name_en": "Entertainment & leisure",
                "icon": "img/icon/cooliocns SVG/Interface/Ticket_Voucher.svg",
                "color_bg": "#FFEDD5",
                "color_text": "#C2410C",
                "is_active": True,
                "order": 10,
            },
            {
                "code": "CAMP",
                "name": "Лагеря",
                "name_az": "Düşərgələr",
                "name_ru": "Лагеря",
                "name_en": "Camps",
                "icon": "icons/categories/camp.svg",
                "color_bg": "#FFF3DF",
                "color_text": "#9A6700",
                "is_active": True,
                "order": 11,
            },
            {
                "code": "PARK",
                "name": "Парки",
                "name_az": "Parklar",
                "name_ru": "Парки",
                "name_en": "Parks",
                "icon": "",
                "color_bg": "#E8F5EE",
                "color_text": "#0C7A47",
                "is_active": True,
                "order": 12,
            },
            {
                "code": "BEACH",
                "name": "Пляжи",
                "name_az": "Çimərliklər",
                "name_ru": "Пляжи",
                "name_en": "Beaches",
                "icon": "icons/categories/beach.svg",
                "color_bg": "#CCFBF1",
                "color_text": "#0F766E",
                "is_active": True,
                "order": 13,
            },
            {
                "code": "WATERPARK",
                "name": "Аквапарки и бассейны",
                "name_az": "Akvaparklar və hovuzlar",
                "name_ru": "Аквапарки и бассейны",
                "name_en": "Waterparks & pools",
                "icon": "icons/categories/waterparks.svg",
                "color_bg": "#DBEAFE",
                "color_text": "#2563EB",
                "is_active": True,
                "order": 14,
            },
            {
                "code": "ZOO",
                "name": "Зоопарки и аквариумы",
                "name_az": "Zooparklar və akvariumlar",
                "name_ru": "Зоопарки и аквариумы",
                "name_en": "Zoos & aquariums",
                "icon": "icons/categories/zoo.svg",
                "color_bg": "#ECFCCB",
                "color_text": "#4D7C0F",
                "is_active": True,
                "order": 15,
            },
        ]

        subcategories_data = [
            # Раннее развитие
            {"cat": "early-development", "code": "parent-and-child", "az": "Valideyn və körpə", "ru": "Родитель и малыш", "en": "Parent and child", "order": 1},
            {"cat": "early-development", "code": "montessori", "az": "Montessori", "ru": "Монтессори", "en": "Montessori", "order": 2},
            {"cat": "early-development", "code": "sensory-development", "az": "Sensor inkişaf", "ru": "Сенсорное развитие", "en": "Sensory development", "order": 3},
            {"cat": "early-development", "code": "early-learning", "az": "Erkən öyrənmə", "ru": "Раннее обучение", "en": "Early learning", "order": 4},
            {"cat": "early-development", "code": "speech-development", "az": "Nitq inkişafı", "ru": "Развитие речи", "en": "Speech development", "order": 5},
            {"cat": "early-development", "code": "kindergarten-prep", "az": "Uşaq bağçasına hazırlıq", "ru": "Подготовка к детскому саду", "en": "Kindergarten prep", "order": 6},
            {"cat": "early-development", "code": "school-prep", "az": "Məktəbəqədər hazırlıq", "ru": "Подготовка к школе", "en": "School prep", "order": 7},
            {"cat": "early-development", "code": "educational-games", "az": "Öyrədici oyunlar", "ru": "Развивающие игры", "en": "Educational games", "order": 8},
            {"cat": "early-development", "code": "mini-kindergarten", "az": "Mini-bağça və gündüz qrupları", "ru": "Мини-сад и дневные группы", "en": "Mini-kindergarten & day groups", "order": 9},

            # Образование
            {"cat": "EDU", "code": "language-az", "az": "Azərbaycan dili", "ru": "Азербайджанский язык", "en": "Azerbaijani language", "order": 1},
            {"cat": "EDU", "code": "language-ru", "az": "Rus dili", "ru": "Русский язык", "en": "Russian language", "order": 2},
            {"cat": "EDU", "code": "language-en", "az": "İngilis dili", "ru": "Английский язык", "en": "English language", "order": 3},
            {"cat": "EDU", "code": "language-other", "az": "Digər xarici dillər", "ru": "Другие иностранные языки", "en": "Other foreign languages", "order": 4},
            {"cat": "EDU", "code": "mathematics", "az": "Riyaziyyat", "ru": "Математика", "en": "Mathematics", "order": 5},
            {"cat": "EDU", "code": "reading-literacy", "az": "Oxu və savadlılıq", "ru": "Чтение и грамотность", "en": "Reading & literacy", "order": 6},
            {"cat": "EDU", "code": "school-subjects", "az": "Məktəb fənləri", "ru": "Школьные предметы", "en": "School subjects", "order": 7},
            {"cat": "EDU", "code": "after-school", "az": "Günüuzadılmış qrup və ev tapşırıqları", "ru": "Продлёнка и домашние задания", "en": "After-school & homework", "order": 8},
            {"cat": "EDU", "code": "exam-prep", "az": "İmtahanlara hazırlıq", "ru": "Подготовка к экзаменам", "en": "Exam prep", "order": 9},
            {"cat": "EDU", "code": "tutoring", "az": "Fərdi dərslər və repetitorluq", "ru": "Индивидуальные занятия и репетиторство", "en": "Tutoring", "order": 10},

            # Спорт
            {"cat": "SPRT", "code": "football", "az": "Futbol", "ru": "Футбол", "en": "Football", "order": 1},
            {"cat": "SPRT", "code": "basketball", "az": "Basketbol", "ru": "Баскетбол", "en": "Basketball", "order": 2},
            {"cat": "SPRT", "code": "volleyball", "az": "Voleybol", "ru": "Волейбол", "en": "Volleyball", "order": 3},
            {"cat": "SPRT", "code": "swimming", "az": "Üzgüçülük", "ru": "Плавание", "en": "Swimming", "order": 4},
            {"cat": "SPRT", "code": "gymnastics-artistic", "az": "İdman gimnastikası", "ru": "Спортивная гимнастика", "en": "Artistic gymnastics", "order": 5},
            {"cat": "SPRT", "code": "gymnastics-rhythmic", "az": "Bədii gimnastika", "ru": "Художественная гимнастика", "en": "Rhythmic gymnastics", "order": 6},
            {"cat": "SPRT", "code": "acrobatics-trampoline", "az": "Akrobatika və batut", "ru": "Акробатика и батут", "en": "Acrobatics & trampoline", "order": 7},
            {"cat": "SPRT", "code": "athletics", "az": "Yüngül atletika və qaçış", "ru": "Лёгкая атлетика и бег", "en": "Athletics & running", "order": 8},
            {"cat": "SPRT", "code": "kids-fitness", "az": "Uşaq fitnesi və funksional hazırlıq", "ru": "Детский фитнес и функциональная подготовка", "en": "Kids fitness & functional training", "order": 9},
            {"cat": "SPRT", "code": "tennis", "az": "Tennis", "ru": "Теннис", "en": "Tennis", "order": 10},
            {"cat": "SPRT", "code": "table-tennis-badminton", "az": "Stolüstü tennis və badminton", "ru": "Настольный теннис и бадминтон", "en": "Table tennis & badminton", "order": 11},
            {"cat": "SPRT", "code": "judo", "az": "Cüdo", "ru": "Дзюдо", "en": "Judo", "order": 12},
            {"cat": "SPRT", "code": "karate-taekwondo", "az": "Karate və taekvondo", "ru": "Карате и тхэквондо", "en": "Karate & taekwondo", "order": 13},
            {"cat": "SPRT", "code": "boxing-kickboxing", "az": "Boks və kikboksinq", "ru": "Бокс и кикбоксинг", "en": "Boxing & kickboxing", "order": 14},
            {"cat": "SPRT", "code": "wrestling-mma", "az": "Güləş, sambo, BJJ və MMA", "ru": "Борьба, самбо, BJJ и MMA", "en": "Wrestling, sambo, BJJ & MMA", "order": 15},
            {"cat": "SPRT", "code": "roller-skating", "az": "Rolik və konkisürmə", "ru": "Ролики и коньки", "en": "Roller skating & ice skating", "order": 16},
            {"cat": "SPRT", "code": "climbing", "az": "Qayaya dırmanma", "ru": "Скалолазание", "en": "Climbing", "order": 17},
            {"cat": "SPRT", "code": "equestrian", "az": "Atçılıq idmanı", "ru": "Конный спорт", "en": "Equestrian sports", "order": 18},

            # Танцы
            {"cat": "dance", "code": "ballet", "az": "Balet", "ru": "Балет", "en": "Balet", "order": 1},
            {"cat": "dance", "code": "az-national-dance", "az": "Azərbaycan milli rəqsləri", "ru": "Азербайджанские народные танцы", "en": "Azerbaijani national dances", "order": 2},
            {"cat": "dance", "code": "world-national-dance", "az": "Digər ölkələrin milli rəqsləri", "ru": "Народные танцы других стран", "en": "World national dances", "order": 3},
            {"cat": "dance", "code": "ballroom-dance", "az": "Balo rəqsləri", "ru": "Бальные танцы", "en": "Ballroom dances", "order": 4},
            {"cat": "dance", "code": "modern-choreography", "az": "Müasir xoreoqrafiya", "ru": "Современная хореография", "en": "Modern choreography", "order": 5},
            {"cat": "dance", "code": "hip-hop-street", "az": "Hip-hop və street dance", "ru": "Hip-hop и street dance", "en": "Hip-hop & street dance", "order": 6},
            {"cat": "dance", "code": "breakdance", "az": "Breakdance", "ru": "Breakdance", "en": "Breakdance", "order": 7},
            {"cat": "dance", "code": "latin-dance", "az": "Latın Amerika rəqsləri", "ru": "Латиноамериканские танцы", "en": "Latin dances", "order": 8},
            {"cat": "dance", "code": "preschool-choreography", "az": "Məktəbəqədərlər üçün xoreoqrafiya", "ru": "Хореография для дошкольников", "en": "Preschool choreography", "order": 9},
            {"cat": "dance", "code": "dance-fitness", "az": "Rəqs fitnesi", "ru": "Танцевальный фитнес", "en": "Dance fitness", "order": 10},

            # Музыка и сцена
            {"cat": "MUS", "code": "vocal", "az": "Vokal", "ru": "Вокал", "en": "Vocal", "order": 1},
            {"cat": "MUS", "code": "piano", "az": "Fortepiano", "ru": "Фортепиано", "en": "Piano", "order": 2},
            {"cat": "MUS", "code": "guitar", "az": "Gitara", "ru": "Гитара", "en": "Guitar", "order": 3},
            {"cat": "MUS", "code": "violin-strings", "az": "Skripka və simli alətlər", "ru": "Скрипка и струнные инструменты", "en": "Violin & strings", "order": 4},
            {"cat": "MUS", "code": "drums-percussion", "az": "Nağara və zərb alətləri", "ru": "Барабаны и ударные инструменты", "en": "Drums & percussion", "order": 5},
            {"cat": "MUS", "code": "other-instruments", "az": "Digər musiqi alətləri", "ru": "Другие музыкальные инструменты", "en": "Other musical instruments", "order": 6},
            {"cat": "MUS", "code": "choir", "az": "Xor", "ru": "Хор", "en": "Choir", "order": 7},
            {"cat": "MUS", "code": "theater-acting", "az": "Teatr və aktyorluq", "ru": "Театр и актёрское мастерство", "en": "Theater & acting", "order": 8},
            {"cat": "MUS", "code": "public-speaking", "az": "Səhnə danışığı və natiqlik", "ru": "Сценическая речь и ораторское искусство", "en": "Public speaking", "order": 9},
            {"cat": "MUS", "code": "musical-theater", "az": "Musiqili teatr", "ru": "Музыкальный театр", "en": "Musical theater", "order": 10},

            # Технологии
            {"cat": "TECH", "code": "programming", "az": "Proqramlaşdırma", "ru": "Программирование", "en": "Programming", "order": 1},
            {"cat": "TECH", "code": "robotics", "az": "Robototexnika", "ru": "Робототехника", "en": "Robotics", "order": 2},
            {"cat": "TECH", "code": "game-dev", "az": "Oyun inkişafı", "ru": "Разработка игр", "en": "Game development", "order": 3},
            {"cat": "TECH", "code": "web-design", "az": "Veb-dizayn və saytların yaradılması", "ru": "Веб-дизайн и создание сайтов", "en": "Web design & development", "order": 4},
            {"cat": "TECH", "code": "artificial-intelligence", "az": "Süni intellekt", "ru": "Искусственный интеллект", "en": "Artificial intelligence", "order": 5},
            {"cat": "TECH", "code": "cybersecurity", "az": "Kiber təhlükəsizlik", "ru": "Кибербезопасность", "en": "Cybersecurity", "order": 6},
            {"cat": "TECH", "code": "3d-modeling", "az": "3D-modelləşdirmə və 3D-çap", "ru": "3D-моделирование и 3D-печать", "en": "3D modeling & printing", "order": 7},
            {"cat": "TECH", "code": "engineering-electronics", "az": "Mühəndislik və elektronika", "ru": "Инженерия и электроника", "en": "Engineering & electronics", "order": 8},
            {"cat": "TECH", "code": "lego-construction", "az": "LEGO-konstruksiya", "ru": "LEGO-конструирование", "en": "LEGO construction", "order": 9},
            {"cat": "TECH", "code": "science-experiments", "az": "Elmi təcrübələr", "ru": "Научные эксперименты", "en": "Science experiments", "order": 10},
            {"cat": "TECH", "code": "digital-literacy", "az": "Rəqəmsal savadlılıq", "ru": "Цифровая грамотность", "en": "Digital literacy", "order": 11},

            # Творчество
            {"cat": "ART", "code": "drawing-painting", "az": "Rəsm və rəngkarlıq", "ru": "Рисование и живопись", "en": "Drawing & painting", "order": 1},
            {"cat": "ART", "code": "arts-crafts", "az": "Dekorativ-tətbiqi sənət", "ru": "Декоративно-прикладное творчество", "en": "Arts & crafts", "order": 2},
            {"cat": "ART", "code": "clay-sculpture", "az": "Gil, keramika və heykəltəraşlıq", "ru": "Лепка, керамика и скульптура", "en": "Clay, ceramics & sculpture", "order": 3},
            {"cat": "ART", "code": "sewing-fashion", "az": "Tikiş və geyim dizaynı", "ru": "Шитьё и дизайн одежды", "en": "Sewing & fashion design", "order": 4},
            {"cat": "ART", "code": "architecture-design", "az": "Memarlıq və dizayn", "ru": "Архитектура и дизайн", "en": "Architecture & design", "order": 5},
            {"cat": "ART", "code": "photography", "az": "Fotoqrafiya", "ru": "Фотография", "en": "Photography", "order": 6},
            {"cat": "ART", "code": "videography-vlogging", "az": "Videoçəkiliş və bloqçuluq", "ru": "Видеосъёмка и блогинг", "en": "Videography & vlogging", "order": 7},
            {"cat": "ART", "code": "animation-comics", "az": "Animasiya, illüstrasiya və komikslər", "ru": "Анимация, иллюстрация и комиксы", "en": "Animation, illustration & comics", "order": 8},
            {"cat": "ART", "code": "culinary-classes", "az": "Kulinariya dərsləri", "ru": "Кулинарные занятия", "en": "Culinary classes", "order": 9},
            {"cat": "ART", "code": "woodwork-modeling", "az": "Modelləşdirmə və ağac işi", "ru": "Моделирование и работа с деревом", "en": "Woodwork & modeling", "order": 10},
            {"cat": "ART", "code": "calligraphy", "az": "Xəttatlıq", "ru": "Каллиграфия", "en": "Calligraphy", "order": 11},

            # Интеллект и навыки
            {"cat": "intellect-skills", "code": "chess", "az": "Şahmat", "ru": "Шахматы", "en": "Chess", "order": 1},
            {"cat": "intellect-skills", "code": "logic-puzzles", "az": "Məntiq və tapmacalar", "ru": "Логика и головоломки", "en": "Logic & puzzles", "order": 2},
            {"cat": "intellect-skills", "code": "mental-arithmetic", "az": "Mental aritmetika", "ru": "Ментальная арифметика", "en": "Mental arithmetic", "order": 3},
            {"cat": "intellect-skills", "code": "speed-reading", "az": "Sürətli oxuma", "ru": "Скорочтение", "en": "Speed reading", "order": 4},
            {"cat": "intellect-skills", "code": "memory-concentration", "az": "Yaddaş və konsentrasiya", "ru": "Память и концентрация", "en": "Memory & concentration", "order": 5},
            {"cat": "intellect-skills", "code": "financial-literacy", "az": "Maliyyə savadlılığı", "ru": "Финансовая грамотность", "en": "Financial literacy", "order": 6},
            {"cat": "intellect-skills", "code": "entrepreneurship", "az": "Sahibkarlıq", "ru": "Предпринимательство", "en": "Entrepreneurship", "order": 7},
            {"cat": "intellect-skills", "code": "leadership-teamwork", "az": "Liderlik və komanda işi", "ru": "Лидерство и командная работа", "en": "Leadership & teamwork", "order": 8},
            {"cat": "intellect-skills", "code": "debates", "az": "Debatlar", "ru": "Дебаты", "en": "Debates", "order": 9},
            {"cat": "intellect-skills", "code": "etiquette", "az": "Etiket", "ru": "Этикет", "en": "Etiquette", "order": 10},
            {"cat": "intellect-skills", "code": "career-guidance", "az": "Yeniyetmələr üçün peşə yönümü", "ru": "Профориентация для подростков", "en": "Career guidance for teens", "order": 11},

            # Развитие и поддержка (Inactive category)
            {"cat": "development-support", "code": "speech-therapist", "az": "Loqoped", "ru": "Логопед", "en": "Speech therapist", "order": 1, "is_active": False},
            {"cat": "development-support", "code": "child-psychologist", "az": "Uşaq psixoloqu", "ru": "Детский психолог", "en": "Child psychologist", "order": 2, "is_active": False},
            {"cat": "development-support", "code": "neuropsychologist", "az": "Neyropsixoloq", "ru": "Нейропсихолог", "en": "Neuropsychologist", "order": 3, "is_active": False},
            {"cat": "development-support", "code": "special-educator", "az": "Xüsusi pedaqoq", "ru": "Специальный педагог", "en": "Special educator", "order": 4, "is_active": False},
            {"cat": "development-support", "code": "sensory-integration", "az": "Sensor inteqrasiya", "ru": "Сенсорная интеграция", "en": "Sensory integration", "order": 5, "is_active": False},
            {"cat": "development-support", "code": "occupational-therapy", "az": "Ergoterapiya", "ru": "Эрготерапия", "en": "Occupational therapy", "order": 6, "is_active": False},
            {"cat": "development-support", "code": "social-skills", "az": "Sosial bacarıqların inkişafı", "ru": "Развитие социальных навыков", "en": "Social skills development", "order": 7, "is_active": False},
            {"cat": "development-support", "code": "inclusive-adaptive", "az": "İnklüziv və adaptiv proqramlar", "ru": "Инклюзивные и адаптивные программы", "en": "Inclusive & adaptive programs", "order": 8, "is_active": False},
            {"cat": "development-support", "code": "behavioral-support", "az": "Davranış dəstəyi", "ru": "Поведенческая поддержка", "en": "Behavioral support", "order": 9, "is_active": False},
            {"cat": "development-support", "code": "adaptive-physical-education", "az": "Adaptiv fiziki tərbiyə və LFK", "ru": "Адаптивная физкультура и ЛФК", "en": "Adaptive physical education", "order": 10, "is_active": False},
            {"cat": "development-support", "code": "parents-consultation", "az": "Valideynlər üçün məsləhətlər", "ru": "Консультации для родителей", "en": "Parents consultation", "order": 11, "is_active": False},

            # Развлечения и досуг
            {"cat": "FUN", "code": "kids-play-centers", "az": "Uşaq oyun mərkəzləri", "ru": "Детские игровые центры", "en": "Kids play centers", "order": 1},
            {"cat": "FUN", "code": "trampoline-activity-parks", "az": "Batut və aktiviti parklar", "ru": "Батутные и активити-парки", "en": "Trampoline & activity parks", "order": 2},
            {"cat": "FUN", "code": "quests", "az": "Kvestlər", "ru": "Квесты", "en": "Quests", "order": 3},
            {"cat": "FUN", "code": "museums-science-centers", "az": "Muzeylər və elm mərkəzləri", "ru": "Музеи и научные центры", "en": "Museums & science centers", "order": 4},
            {"cat": "FUN", "code": "master-classes", "az": "Master-klaslar", "ru": "Мастер-классы", "en": "Master classes", "order": 5},
            {"cat": "FUN", "code": "birthday-parties", "az": "Ad günlərinin keçirilməsi", "ru": "Проведение дней рождения", "en": "Birthday parties", "order": 6},
            {"cat": "FUN", "code": "family-cafes-kids-zones", "az": "Ailə kafeləri və uşaq zonaları", "ru": "Семейные кафе и детские зоны", "en": "Family cafes & kids zones", "order": 7},
            {"cat": "FUN", "code": "excursions-tours", "az": "Ekskursiyalar və idraki turlar", "ru": "Экскурсии и познавательные туры", "en": "Excursions & educational tours", "order": 8},
            {"cat": "FUN", "code": "nature-outdoor-activities", "az": "Təbiət və küçə fəaliyyətləri", "ru": "Природные и уличные активности", "en": "Nature & outdoor activities", "order": 9},
            {"cat": "FUN", "code": "kids-theaters-cinema", "az": "Uşaq teatrları, kino və tamaşalar", "ru": "Детские театры, кино и представления", "en": "Kids theaters, cinema & shows", "order": 10},

            # Аквапарки и бассейны
            {"cat": "WATERPARK", "code": "waterparks-pools", "az": "Akvaparklar və istirahət hovuzları", "ru": "Аквапарки и бассейны для отдыха", "en": "Waterparks & pools", "order": 1},

            # Зоопарки и аквариумы
            {"cat": "ZOO", "code": "zoos-aquariums", "az": "Zooparklar və akvariumlar", "ru": "Зоопарки и аквариумы", "en": "Zoos & aquariums", "order": 1},

            # Лагеря
            {"cat": "CAMP", "code": "city-day-camp", "az": "Şəhər gündüz düşərgəsi", "ru": "Городской дневной лагерь", "en": "City day camp", "order": 1},
            {"cat": "CAMP", "code": "summer-camp", "az": "Yay düşərgəsi", "ru": "Летний лагерь", "en": "Summer camp", "order": 2},
            {"cat": "CAMP", "code": "winter-camp", "az": "Qış düşərgəsi", "ru": "Зимний лагерь", "en": "Winter camp", "order": 3},
            {"cat": "CAMP", "code": "sports-camp", "az": "İdman düşərgəsi", "ru": "Спортивный лагерь", "en": "Sports camp", "order": 4},
            {"cat": "CAMP", "code": "language-camp", "az": "Dil düşərgəsi", "ru": "Языковой лагерь", "en": "Language camp", "order": 5},
            {"cat": "CAMP", "code": "creative-camp", "az": "Yaradıcılıq düşərgəsi", "ru": "Творческий лагерь", "en": "Creative camp", "order": 6},
            {"cat": "CAMP", "code": "tech-stem-camp", "az": "Texnoloji və STEM düşərgəsi", "ru": "Технологический и STEM-лагерь", "en": "Tech & STEM camp", "order": 7},
            {"cat": "CAMP", "code": "nature-camp", "az": "Turizm və təbiət düşərgəsi", "ru": "Туристический и природный лагерь", "en": "Nature camp", "order": 8},
            {"cat": "CAMP", "code": "weekend-program", "az": "Həftəsonu proqramı", "ru": "Программа выходного дня", "en": "Weekend program", "order": 9},
            {"cat": "CAMP", "code": "summer-school", "az": "Yay məktəbi", "ru": "Летняя школа", "en": "Summer school", "order": 10},
            {"cat": "CAMP", "code": "international-camp", "az": "Xaricdə və beynəlxalq düşərgə", "ru": "Выездной и международный лагерь", "en": "International camp", "order": 11},

            # Парки
            {"cat": "PARK", "code": "amusement-parks", "az": "Attraksionlar", "ru": "Аттракционы", "en": "Amusement parks", "order": 1},
            {"cat": "PARK", "code": "public-parks", "az": "Milli parklar", "ru": "Городские парки", "en": "Public parks", "order": 2},
            {"cat": "PARK", "code": "rope-parks", "az": "Kanat parkları", "ru": "Веревочные парки", "en": "Rope parks", "order": 3},
        ]

        with transaction.atomic():
            self.stdout.write("Seeding categories...")
            for cat_data in categories_data:
                existing_cat = Category.objects.filter(code=cat_data["code"]).first()

                defaults = {
                    "name": cat_data["name"],
                    "name_az": cat_data["name_az"],
                    "name_ru": cat_data["name_ru"],
                    "name_en": cat_data["name_en"],
                    "order": cat_data["order"],
                }

                # CRITICAL: Never overwrite is_active of an existing category.
                # Admin changes (archive/restore) must be preserved across deploys.
                if not existing_cat:
                    defaults["is_active"] = cat_data.get("is_active", True)

                should_update_icon = False
                if not existing_cat:
                    should_update_icon = True
                elif update_icons:
                    should_update_icon = True
                elif not existing_cat.icon or existing_cat.icon.startswith("fas fa-"):
                    should_update_icon = True

                if should_update_icon:
                    defaults["icon"] = cat_data.get("icon", "")

                if (
                    not existing_cat
                    or str((existing_cat.color_bg or "")).strip().lower() in NEUTRAL_BG_VALUES
                    or cat_data["code"] in {"ZOO", "WATERPARK"}
                ):
                    defaults["color_bg"] = cat_data.get("color_bg", "#F3F4F6")

                if (
                    not existing_cat
                    or str((existing_cat.color_text or "")).strip().lower() in NEUTRAL_TEXT_VALUES
                    or cat_data["code"] in {"ZOO", "WATERPARK"}
                ):
                    defaults["color_text"] = cat_data.get("color_text", "#6B7280")

                category, created = Category.objects.update_or_create(
                    code=cat_data["code"],
                    defaults=defaults
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"  [{action}] Category: {category.code} - {category.name}")

            self.stdout.write("Seeding subcategories...")
            for sub_data in subcategories_data:
                try:
                    category = Category.objects.get(code=sub_data["cat"])
                except Category.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  Category '{sub_data['cat']}' not found for subcategory '{sub_data['code']}'"))
                    continue

                existing_sub = Subcategory.objects.filter(code=sub_data["code"]).first()

                sub_defaults = {
                    "category": category,
                    "name": sub_data["ru"],
                    "name_az": sub_data["az"],
                    "name_ru": sub_data["ru"],
                    "name_en": sub_data["en"],
                    "order": sub_data["order"],
                }
                # CRITICAL: Never overwrite is_active of an existing subcategory.
                if not existing_sub:
                    sub_defaults["is_active"] = sub_data.get("is_active", True)

                subcategory, created = Subcategory.objects.update_or_create(
                    code=sub_data["code"],
                    defaults=sub_defaults,
                )
                action = "Created" if created else "Updated"
                self.stdout.write(f"  [{action}] Subcategory: {subcategory.code} - {subcategory.name}")

        self.stdout.write(self.style.SUCCESS("Taxonomy seeding completed successfully!"))
