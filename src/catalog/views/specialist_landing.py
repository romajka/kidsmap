"""Public landing page that invites teachers and child specialists to KidsMap.

Content lives here in AZ/RU/EN, like the /add-place/ page. Numbers on the
page come from the database only; nothing is invented. The page follows the
specialists section switch, because its call to action leads into the
specialist workspace, which is unavailable while the section is off.
"""
import json

from django.shortcuts import render
from django.templatetags.static import static
from django.urls import reverse

from ..controllers.specialist_workspace import SPECIALIZATION_GROUPS
from ..models import Place, Specialist
from ..services.content_quality import public_place_queryset
from ..services.features import require_specialists_section_enabled
from ..services.public_urls import build_public_absolute_uri

# Show the specialists count only once it is large enough to read as social proof.
SPECIALISTS_COUNT_MIN = 20

TILES = [
    # (image, specialization code used by the public specialists filter)
    ("02-tutor", "tutor"),
    ("02-speech", "speech_therapist"),
    ("02-psychologist", "child_psychologist"),
    ("02-sport", "sports_coach"),
    ("02-music", "music_teacher"),
    ("02-art", "drawing_teacher"),
]

CONTENT = {
    "ru": {
        "seo_title": "Для репетиторов и детских специалистов Баку — бесплатная карточка",
        "meta": "Репетиторы, логопеды, психологи, тренеры и педагоги: создайте бесплатную карточку на KidsMap. Родители Баку находят вас и связываются напрямую.",
        "crumb": "Для специалистов",
        "eyebrow": "Для педагогов и специалистов",
        "title": "Вас ищут родители Баку",
        "lead": "Создайте карточку на KidsMap — и семьи, которые выбирают репетитора, логопеда или тренера, увидят именно вас. С фото, опытом, ценами и отзывами.",
        "badge_free": "Базовая карточка бесплатна",
        "badge_check": "Проверка модерацией",
        "cta": "Создать карточку",
        "cta_more": "Как это работает",
        "sample": "Пример карточки",
        "sample_name": "Ваше имя",
        "sample_role": "Логопед · 8 лет опыта",
        "sample_chips": ["Онлайн", "Выезд к семье", "AZ · RU"],
        "sample_price": "от 25 ₼",
        "sample_reviews": "Отзывы родителей",
        "sample_btn": "Написать в WhatsApp",
        "stat_places": "мест и кружков уже в каталоге",
        "stat_specialists": "специалистов на сайте",
        "stat_directions": "направлений для специалистов",
        "stat_languages": "языка сайта: AZ, RU, EN",
        "who_title": "Для кого эта страница",
        "who_lead": "Если вы занимаетесь с детьми — индивидуально или в центре — KidsMap поможет родителям найти вас.",
        "tiles": [
            ("Репетиторы", "Математика, языки, подготовка к школе и экзаменам."),
            ("Логопеды", "Постановка звуков, запуск речи, дефектология."),
            ("Психологи", "Детские и семейные психологи, раннее развитие."),
            ("Тренеры", "Спорт, персональные тренировки, ЛФК."),
            ("Музыка", "Фортепиано, вокал, гитара и другие инструменты."),
            ("Рисование и творчество", "Рисование, актёрское мастерство, робототехника."),
        ],
        "tile_link": "Смотреть специалистов",
        "who_more": "И ещё {n} направлений: от педиатра и физиотерапевта до программирования.",
        "steps_title": "Как это работает",
        "steps": [
            ("Заполните карточку", "Фото, специальность, опыт, форматы занятий, цены и контакты. Всё — в личном кабинете."),
            ("Пройдите проверку", "Модерация проверяет, что данные полные и понятные. Можно приложить дипломы и сертификаты."),
            ("Родители связываются с вами", "Карточка появляется в каталоге. Семьи звонят и пишут вам напрямую — без посредников."),
        ],
        "get_title": "Что будет в вашей карточке",
        "benefits": [
            ("07-profile", "Профиль на трёх языках", "Фото, рассказ о себе, образование и опыт — на AZ, RU и EN."),
            ("07-certificate", "Дипломы и сертификаты", "Загрузите документы — это помогает пройти проверку и повышает доверие родителей."),
            ("07-reviews", "Отзывы родителей", "Рейтинг и отзывы семей, с которыми вы уже занимались."),
            ("07-schedule", "Форматы и цены", "Онлайн, у вас или с выездом к семье. Стоимость, длительность и возраст детей."),
            ("07-direct", "Прямой контакт", "Телефон, WhatsApp и Instagram. Мы не посредники: родители пишут вам напрямую."),
            ("07-workplace", "Места работы", "Укажите центры и школы, где вы ведёте занятия, — карточки будут связаны."),
        ],
        "faq_title": "Частые вопросы",
        "faq": [
            ("Сколько стоит размещение?", "Создание карточки и размещение основной информации в каталоге бесплатны."),
            ("Когда карточка появится на сайте?", "После проверки модерацией. Мы смотрим, что обязательные данные заполнены, информация понятна и соответствует правилам KidsMap."),
            ("Обязательно ли загружать дипломы и сертификаты?", "Не обязательно, но документы помогают пройти проверку и показывают родителям вашу квалификацию."),
            ("Я работаю в нескольких центрах. Как это показать?", "В карточке можно указать несколько мест работы, а также занятия онлайн и с выездом к семье."),
            ("Можно ли потом изменить данные?", "Да. Откройте карточку в личном кабинете, измените нужные поля и отправьте на проверку. Изменения могут повторно пройти модерацию."),
            ("На каких языках будет карточка?", "Сайт работает на азербайджанском, русском и английском. Рассказ о себе можно заполнить на каждом из них."),
        ],
        "final_title": "Начните сегодня — родители уже ищут",
        "final_lead": "Карточку можно заполнить за один вечер, а изменить в любой момент.",
        "final_note": "Нужен аккаунт KidsMap — вход или короткая регистрация.",
        "rules": "Правила размещения",
    },
    "az": {
        "seo_title": "Bakıda repetitor və uşaq mütəxəssisləri üçün pulsuz kart",
        "meta": "Repetitorlar, loqopedlər, psixoloqlar, məşqçilər və müəllimlər: KidsMap-də pulsuz kart yaradın. Bakı valideynləri sizi tapır və birbaşa əlaqə saxlayır.",
        "crumb": "Mütəxəssislər üçün",
        "eyebrow": "Müəllim və mütəxəssislər üçün",
        "title": "Bakı valideynləri sizi axtarır",
        "lead": "KidsMap-də kart yaradın — repetitor, loqoped və ya məşqçi seçən ailələr məhz sizi görəcək. Foto, təcrübə, qiymətlər və rəylərlə.",
        "badge_free": "Əsas kart pulsuzdur",
        "badge_check": "Moderasiya yoxlaması",
        "cta": "Kart yarat",
        "cta_more": "Necə işləyir",
        "sample": "Kart nümunəsi",
        "sample_name": "Adınız",
        "sample_role": "Loqoped · 8 il təcrübə",
        "sample_chips": ["Onlayn", "Evə gəliş", "AZ · RU"],
        "sample_price": "25 ₼-dan",
        "sample_reviews": "Valideyn rəyləri",
        "sample_btn": "WhatsApp-a yaz",
        "stat_places": "məkan və dərnək artıq kataloqdadır",
        "stat_specialists": "mütəxəssis saytdadır",
        "stat_directions": "mütəxəssis istiqaməti",
        "stat_languages": "dildə sayt: AZ, RU, EN",
        "who_title": "Bu səhifə kimin üçündür",
        "who_lead": "Uşaqlarla fərdi və ya mərkəzdə məşğul olursunuzsa, KidsMap valideynlərin sizi tapmasına kömək edəcək.",
        "tiles": [
            ("Repetitorlar", "Riyaziyyat, dillər, məktəbə və imtahanlara hazırlıq."),
            ("Loqopedlər", "Səslərin qoyuluşu, nitqin inkişafı, defektologiya."),
            ("Psixoloqlar", "Uşaq və ailə psixoloqları, erkən inkişaf."),
            ("Məşqçilər", "İdman, fərdi məşqlər, müalicəvi bədən tərbiyəsi."),
            ("Musiqi", "Fortepiano, vokal, gitara və digər alətlər."),
            ("Rəsm və yaradıcılıq", "Rəsm, aktyorluq, robototexnika."),
        ],
        "tile_link": "Mütəxəssislərə bax",
        "who_more": "Və daha {n} istiqamət: pediatr və fizioterapevtdən proqramlaşdırmaya qədər.",
        "steps_title": "Necə işləyir",
        "steps": [
            ("Kartı doldurun", "Foto, ixtisas, təcrübə, məşğələ formatları, qiymətlər və əlaqə. Hamısı şəxsi kabinetdə."),
            ("Yoxlamadan keçin", "Moderasiya məlumatların tam və aydın olduğunu yoxlayır. Diplom və sertifikatlar əlavə edə bilərsiniz."),
            ("Valideynlər sizinlə əlaqə saxlayır", "Kart kataloqda görünür. Ailələr sizə birbaşa zəng edir və yazır — vasitəçisiz."),
        ],
        "get_title": "Kartınızda nələr olacaq",
        "benefits": [
            ("07-profile", "Üç dildə profil", "Foto, özünüz haqqında, təhsil və təcrübə — AZ, RU və EN dillərində."),
            ("07-certificate", "Diplom və sertifikatlar", "Sənədləri yükləyin — bu, yoxlamadan keçməyə kömək edir və valideynlərin etibarını artırır."),
            ("07-reviews", "Valideyn rəyləri", "Artıq məşğul olduğunuz ailələrin reytinqi və rəyləri."),
            ("07-schedule", "Formatlar və qiymətlər", "Onlayn, sizdə və ya ailəyə gəlişlə. Qiymət, müddət və uşaqların yaşı."),
            ("07-direct", "Birbaşa əlaqə", "Telefon, WhatsApp və Instagram. Biz vasitəçi deyilik: valideynlər sizə birbaşa yazır."),
            ("07-workplace", "İş yerləri", "Dərs keçdiyiniz mərkəz və məktəbləri göstərin — kartlar əlaqələndiriləcək."),
        ],
        "faq_title": "Tez-tez verilən suallar",
        "faq": [
            ("Yerləşdirmə nə qədərdir?", "Kartın yaradılması və əsas məlumatın kataloqda yerləşdirilməsi pulsuzdur."),
            ("Kart saytda nə vaxt görünəcək?", "Moderasiya yoxlamasından sonra. Vacib məlumatların doldurulduğunu, aydın olduğunu və KidsMap qaydalarına uyğun olduğunu yoxlayırıq."),
            ("Diplom və sertifikat yükləmək mütləqdirmi?", "Mütləq deyil, amma sənədlər yoxlamadan keçməyə kömək edir və valideynlərə ixtisasınızı göstərir."),
            ("Bir neçə mərkəzdə işləyirəm. Bunu necə göstərim?", "Kartda bir neçə iş yeri, həmçinin onlayn və evə gəlişlə məşğələlər göstərə bilərsiniz."),
            ("Məlumatları sonra dəyişmək olarmı?", "Bəli. Kartı şəxsi kabinetdə açın, lazımi sahələri dəyişin və yoxlamaya göndərin. Dəyişikliklər yenidən moderasiyadan keçə bilər."),
            ("Kart hansı dillərdə olacaq?", "Sayt Azərbaycan, rus və ingilis dillərində işləyir. Özünüz haqqında mətni hər birində doldura bilərsiniz."),
        ],
        "final_title": "Bu gün başlayın — valideynlər artıq axtarır",
        "final_lead": "Kartı bir axşamda doldurmaq, istənilən vaxt dəyişmək olar.",
        "final_note": "KidsMap hesabı lazımdır — giriş və ya qısa qeydiyyat.",
        "rules": "Yerləşdirmə qaydaları",
    },
    "en": {
        "seo_title": "For tutors and child specialists in Baku — a free profile",
        "meta": "Tutors, speech therapists, psychologists, coaches and teachers: create a free profile on KidsMap. Parents in Baku find you and contact you directly.",
        "crumb": "For specialists",
        "eyebrow": "For teachers and specialists",
        "title": "Parents in Baku are looking for you",
        "lead": "Create a profile on KidsMap and families choosing a tutor, speech therapist or coach will see you — with your photo, experience, prices and reviews.",
        "badge_free": "Basic profile is free",
        "badge_check": "Checked by moderation",
        "cta": "Create a profile",
        "cta_more": "How it works",
        "sample": "Example profile",
        "sample_name": "Your name",
        "sample_role": "Speech therapist · 8 years",
        "sample_chips": ["Online", "Home visits", "AZ · RU"],
        "sample_price": "from 25 ₼",
        "sample_reviews": "Parent reviews",
        "sample_btn": "Message on WhatsApp",
        "stat_places": "places and clubs already listed",
        "stat_specialists": "specialists on the site",
        "stat_directions": "specialist fields",
        "stat_languages": "site languages: AZ, RU, EN",
        "who_title": "Who this is for",
        "who_lead": "If you work with children — on your own or at a centre — KidsMap helps parents find you.",
        "tiles": [
            ("Tutors", "Maths, languages, school and exam preparation."),
            ("Speech therapists", "Sound correction, speech development, defectology."),
            ("Psychologists", "Child and family psychologists, early development."),
            ("Coaches", "Sports, personal training, physical therapy."),
            ("Music", "Piano, voice, guitar and other instruments."),
            ("Art and creativity", "Drawing, acting, robotics."),
        ],
        "tile_link": "See specialists",
        "who_more": "And {n} more fields, from paediatrics and physiotherapy to programming.",
        "steps_title": "How it works",
        "steps": [
            ("Fill in your profile", "Photo, speciality, experience, session formats, prices and contacts — all in your account."),
            ("Pass the check", "Moderation checks that the information is complete and clear. You can attach diplomas and certificates."),
            ("Parents contact you", "Your profile appears in the catalog. Families call and message you directly — no middlemen."),
        ],
        "get_title": "What your profile includes",
        "benefits": [
            ("07-profile", "A profile in three languages", "Photo, about you, education and experience — in AZ, RU and EN."),
            ("07-certificate", "Diplomas and certificates", "Upload documents — it helps you pass the check and builds parents’ trust."),
            ("07-reviews", "Parent reviews", "Ratings and reviews from families you have worked with."),
            ("07-schedule", "Formats and prices", "Online, at your place or home visits. Price, duration and children’s ages."),
            ("07-direct", "Direct contact", "Phone, WhatsApp and Instagram. We are not a middleman: parents contact you directly."),
            ("07-workplace", "Where you work", "Add the centres and schools where you teach, and the profiles are linked."),
        ],
        "faq_title": "Frequently asked questions",
        "faq": [
            ("How much does it cost?", "Creating a profile and publishing its essential information in the catalog is free."),
            ("When will my profile appear?", "After moderation. We check that the required information is provided, clear and follows the KidsMap rules."),
            ("Do I have to upload diplomas and certificates?", "No, but documents help you pass the check and show parents your qualifications."),
            ("I work at several centres. How do I show that?", "You can add several places of work, as well as online sessions and home visits."),
            ("Can I change my details later?", "Yes. Open the profile in your account, edit the fields and send it for review. Changes may be moderated again."),
            ("Which languages will my profile be in?", "The site works in Azerbaijani, Russian and English. You can write about yourself in each of them."),
        ],
        "final_title": "Start today — parents are already searching",
        "final_lead": "You can fill in your profile in one evening and change it at any time.",
        "final_note": "You need a KidsMap account — sign in or a short registration.",
        "rules": "Listing rules",
    },
}


def _directions_count():
    return sum(len(group.get("codes", [])) for group in SPECIALIZATION_GROUPS)


def _faq_schema(request, content):
    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in content["faq"]
        ],
    }
    # Escape "</" so the JSON can never close the surrounding <script>.
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def _webpage_schema(request, content, language):
    payload = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": content["seo_title"],
        "description": content["meta"],
        "inLanguage": language,
        "url": build_public_absolute_uri(request, request.path),
        "audience": {"@type": "Audience", "audienceType": content["eyebrow"]},
        "isPartOf": {"@type": "WebSite", "name": "KidsMap", "url": build_public_absolute_uri(request, "/")},
    }
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def specialist_landing(request):
    require_specialists_section_enabled()
    language = request.LANGUAGE_CODE if request.LANGUAGE_CODE in CONTENT else "az"
    content = CONTENT[language]
    directions = _directions_count()
    specialists_count = Specialist.objects.filter(status=Specialist.STATUS_PUBLISHED, is_active=True).count()
    places_count = public_place_queryset(Place.objects.all()).count()
    list_url = reverse("specialist_list")
    tiles = [
        {"image": image, "title": title, "text": text, "url": f"{list_url}?specialization={code}"}
        for (image, code), (title, text) in zip(TILES, content["tiles"])
    ]
    context = {
        "content": content,
        "tiles": tiles,
        "who_more": content["who_more"].format(n=max(directions - len(TILES), 0)),
        "stats": {
            "places": places_count,
            "specialists": specialists_count if specialists_count >= SPECIALISTS_COUNT_MIN else None,
            "directions": directions,
        },
        "seo_title": f"{content['seo_title']} | KidsMap",
        "meta_description": content["meta"],
        "faq_schema_json": _faq_schema(request, content),
        "webpage_schema_json": _webpage_schema(request, content, language),
        "social_share_image": {
            "url": build_public_absolute_uri(request, static(f"img/specialist-landing/share-{language}.jpg")),
            "alt": f"KidsMap — {content['title']}",
            "type": "image/jpeg",
            "width": 1200,
            "height": 630,
        },
    }
    return render(request, "pages/specialist_landing.html", context)
