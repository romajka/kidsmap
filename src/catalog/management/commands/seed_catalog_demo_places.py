from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from catalog.models import Place


@dataclass(frozen=True)
class DemoPlaceTemplate:
    slug: str
    category: str
    district: str
    metro: str
    age_from: int
    age_to: int
    price_from: int
    price_to: int
    lat: float
    lng: float
    is_verified: bool
    rating_avg: float
    rating_count: int
    name_ru: str
    name_az: str
    name_en: str
    description_ru: str
    description_az: str
    description_en: str
    address: str
    phone: str
    instagram: str
    website: str
    schedule: str
    extra_conditions: str
    photo_path: str


class Command(BaseCommand):
    help = "Create realistic local demo places with photos for catalog and map UI testing."

    DEMO_MARKER = "seed:catalog-demo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=18,
            help="How many demo places to keep from the curated local set. Default: 18.",
        )
        parser.add_argument(
            "--clear-old",
            action="store_true",
            help="Delete previously seeded demo places before creating a new batch.",
        )

    def handle(self, *args, **options):
        count = max(1, int(options["count"]))
        clear_old = bool(options["clear_old"])

        if clear_old:
            deleted, _ = Place.objects.filter(additional_info__startswith=self.DEMO_MARKER).delete()
            self.stdout.write(f"Removed {deleted} old demo objects.")

        templates = self._build_templates()[:count]
        created = 0
        updated = 0

        for index, template in enumerate(templates, start=1):
            place, is_created = Place.objects.get_or_create(slug=template.slug)
            self._apply_defaults(place=place, index=index, template=template)
            self._sync_photo(place=place, template=template)
            place.save()
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo catalog places ready. Created: {created}, Updated: {updated}, Total requested: {len(templates)}."
            )
        )

    def _apply_defaults(self, *, place: Place, index: int, template: DemoPlaceTemplate) -> None:
        place.name = template.name_ru
        place.name_ru = template.name_ru
        place.name_az = template.name_az
        place.name_en = template.name_en
        place.description_ru = template.description_ru
        place.description_az = template.description_az
        place.description_en = template.description_en
        place.category_id = template.category
        place.district = template.district
        place.metro = template.metro
        place.address = template.address
        place.phone1 = template.phone
        place.instagram = template.instagram
        place.website = template.website
        place.schedule = template.schedule
        place.age_from = template.age_from
        place.age_to = template.age_to
        place.price_from = template.price_from
        place.price_to = template.price_to
        place.price_per_lesson = max(template.price_from - 5, 25)
        place.price_per_month = template.price_to * 4
        place.lesson_duration_minutes = 60 + (index % 3) * 15
        place.lat = template.lat
        place.lng = template.lng
        place.rating_avg = template.rating_avg
        place.rating_count = template.rating_count
        place.likes_count = 10 + index * 3
        place.is_active = True
        place.is_verified = template.is_verified
        place.status = Place.STATUS_PUBLISHED
        place.additional_info = f"{self.DEMO_MARKER}:{index:02d}"
        place.extra_conditions = template.extra_conditions

    def _sync_photo(self, *, place: Place, template: DemoPlaceTemplate) -> None:
        source_path = self._repo_root() / template.photo_path
        if not source_path.exists():
            return

        target_name = f"demo-{template.slug}{source_path.suffix.lower()}"
        current_name = Path(place.photo.name).name if place.photo and getattr(place.photo, "name", "") else ""
        if current_name == target_name:
            return

        if place.photo and getattr(place.photo, "name", ""):
            place.photo.delete(save=False)

        with source_path.open("rb") as source_file:
            place.photo.save(target_name, File(source_file), save=False)

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    def _build_templates(self) -> list[DemoPlaceTemplate]:
        return [
            DemoPlaceTemplate(
                slug="baku-judo-training-center",
                category="SPRT",
                district="Nərimanov",
                metro="Gənclik",
                age_from=5,
                age_to=14,
                price_from=90,
                price_to=140,
                lat=40.40155,
                lng=49.85334,
                is_verified=True,
                rating_avg=4.8,
                rating_count=128,
                name_ru="Бакинский центр дзюдо",
                name_az="Bakı Cüdo Təlim Mərkəzi",
                name_en="Baku Judo Training Center",
                description_ru="Современный центр дзюдо рядом с Gənclik: детские группы по возрастам, пробная тренировка и удобное расписание после школы.",
                description_az="Gənclik yaxınlığında müasir cüdo mərkəzi: yaşa görə qruplar, sınaq məşğələsi və məktəbdən sonra rahat cədvəl.",
                description_en="A modern judo center near Gənclik with age-based groups, trial classes, and an after-school schedule.",
                address="Həsən Əliyev küç. 78, Bakı",
                phone="+994 50 321 10 10",
                instagram="bakujudo.az",
                website="https://example.com/baku-judo-training-center",
                schedule="B.e., Ç.a., C.a. 16:00-19:00; şənbə sparrinq qrupu 11:00.",
                extra_conditions="Valideynlər üçün gözləmə zonası, yeni başlayanlar üçün ayrıca qrup və aylıq irəliləyiş qeydləri var.",
                photo_path="static/img/home/photos/sports-class.jpg",
            ),
            DemoPlaceTemplate(
                slug="coderoom-kids-lab",
                category="TECH",
                district="Nəsimi",
                metro="28 May",
                age_from=7,
                age_to=15,
                price_from=110,
                price_to=180,
                lat=40.37892,
                lng=49.85571,
                is_verified=True,
                rating_avg=4.7,
                rating_count=94,
                name_ru="CodeRoom Kids Lab",
                name_az="CodeRoom Kids Lab",
                name_en="CodeRoom Kids Lab",
                description_ru="Кружок по Scratch, Python и робототехнике в центре Баку с небольшими группами и ежемесячными мини-проектами.",
                description_az="Bakının mərkəzində Scratch, Python və robototexnika dərnəyi: kiçik qruplar və aylıq mini layihələr.",
                description_en="A central Baku coding club for Scratch, Python, and robotics with small groups and monthly projects.",
                address="28 May küç. 12, Bakı",
                phone="+994 50 321 10 20",
                instagram="coderoomkids",
                website="https://example.com/coderoom-kids-lab",
                schedule="Ç.a., C.a., Ş. 17:00-19:15; həftəsonu robototexnika qrupu 12:00.",
                extra_conditions="Noutbuklar mərkəz tərəfindən verilir, dərslər layihə əsaslıdır, ayda bir açıq demo günü keçirilir.",
                photo_path="static/img/home/photos/team-hands.jpg",
            ),
            DemoPlaceTemplate(
                slug="mini-art-studio-iceri",
                category="ART",
                district="Səbail",
                metro="Sahil",
                age_from=4,
                age_to=12,
                price_from=75,
                price_to=120,
                lat=40.37014,
                lng=49.83684,
                is_verified=True,
                rating_avg=4.9,
                rating_count=76,
                name_ru="Студия Mini Art İçəri",
                name_az="Mini Art İçəri Studiyası",
                name_en="Mini Art Studio Icheri",
                description_ru="Творческая студия с рисованием, лепкой и сезонными мастер-классами рядом с набережной и İçərişəhər.",
                description_az="Rəsm, keramika və mövsümi master-klasslarla yaradıcı studiya, bulvara və İçərişəhər istiqamətinə yaxın.",
                description_en="A creative studio for drawing, clay, and seasonal workshops near the boulevard and Icherisheher.",
                address="Neftçilər prospekti 95, Bakı",
                phone="+994 50 321 10 30",
                instagram="miniarticeri",
                website="https://example.com/mini-art-studio-iceri",
                schedule="B.e., C.a., C. 15:30-18:30; bazar günü ailə workshop-u 13:00.",
                extra_conditions="Emalatxanada bütün materiallar daxildir, əsərlər ay sonunda mini sərgidə nümayiş olunur.",
                photo_path="static/img/home/photos/art-class.jpg",
            ),
            DemoPlaceTemplate(
                slug="piano-house-ganjlik",
                category="MUS",
                district="Nərimanov",
                metro="Gənclik",
                age_from=6,
                age_to=16,
                price_from=120,
                price_to=220,
                lat=40.39811,
                lng=49.85147,
                is_verified=True,
                rating_avg=4.8,
                rating_count=88,
                name_ru="Piano House Gənclik",
                name_az="Piano House Gənclik",
                name_en="Piano House Ganjlik",
                description_ru="Музыкальная студия с фортепиано, вокалом и подготовкой к отчетным концертам для детей разных возрастов.",
                description_az="Fortepiano, vokal və hesabat konsertlərinə hazırlıq təklif edən musiqi studiyası.",
                description_en="A music studio for piano, vocals, and recital preparation across multiple age groups.",
                address="Atatürk prospekti 115, Bakı",
                phone="+994 50 321 10 40",
                instagram="pianohouse.az",
                website="https://example.com/piano-house-ganjlik",
                schedule="B.e.-C. 15:00-20:00; şənbə fərdi fortepiano dərsləri.",
                extra_conditions="Səhnə təcrübəsi üçün kiçik salon, fərdi və mini qrup formatı, valideynlərə aylıq geribildirim.",
                photo_path="static/img/home/photos/music-lesson.jpg",
            ),
            DemoPlaceTemplate(
                slug="future-skills-academy",
                category="EDU",
                district="Yasamal",
                metro="Elmlər Akademiyası",
                age_from=6,
                age_to=15,
                price_from=95,
                price_to=160,
                lat=40.37561,
                lng=49.82275,
                is_verified=True,
                rating_avg=4.6,
                rating_count=102,
                name_ru="Future Skills Academy",
                name_az="Future Skills Academy",
                name_en="Future Skills Academy",
                description_ru="Центр английского, логики и soft skills рядом с Elmlər Akademiyası для детей начальной и средней школы.",
                description_az="Elmlər Akademiyası yaxınlığında ingilis dili, məntiq və soft skills mərkəzi.",
                description_en="A center near Elmlər Akademiyası for English, logic, and soft skills for school-age children.",
                address="Hüseyn Cavid prospekti 48, Bakı",
                phone="+994 50 321 10 50",
                instagram="futureskills.az",
                website="https://example.com/future-skills-academy",
                schedule="B.e., Ç.a., C.a., C. 16:00-19:30; speaking club bazar günü 11:00.",
                extra_conditions="Səviyyə testi pulsuzdur, hər ay valideyn görüşü və qısa irəliləyiş hesabatı təqdim olunur.",
                photo_path="static/img/home/photos/family-studio.jpg",
            ),
            DemoPlaceTemplate(
                slug="sea-breeze-kids-club",
                category="FUN",
                district="Xətai",
                metro="28 May",
                age_from=3,
                age_to=10,
                price_from=60,
                price_to=110,
                lat=40.36584,
                lng=49.88984,
                is_verified=False,
                rating_avg=4.5,
                rating_count=48,
                name_ru="Sea Breeze Kids Club",
                name_az="Sea Breeze Kids Club",
                name_en="Sea Breeze Kids Club",
                description_ru="Клуб досуга с настольными играми, квестами, мини-кулинарией и праздничными программами для детей.",
                description_az="Masa oyunları, kvestlər, mini-kulinariya və şənlik proqramları olan asudə klub.",
                description_en="A leisure club with board games, quests, mini cooking classes, and party activities.",
                address="Ağ Şəhər bulvarı 5, Bakı",
                phone="+994 50 321 10 60",
                instagram="seabreezekidsclub",
                website="https://example.com/sea-breeze-kids-club",
                schedule="Hər gün 11:00-20:00; həftəsonu tema günləri və ailə oyun saatı.",
                extra_conditions="Ad günü rezervasiyası, müəllim nəzarəti və yaşa görə sakit/aktiv zona mövcuddur.",
                photo_path="static/img/home/photos/family-balloons.jpg",
            ),
            DemoPlaceTemplate(
                slug="city-explorer-camp",
                category="CAMP",
                district="Binəqədi",
                metro="Nəsimi",
                age_from=7,
                age_to=15,
                price_from=160,
                price_to=280,
                lat=40.42592,
                lng=49.82423,
                is_verified=True,
                rating_avg=4.7,
                rating_count=59,
                name_ru="City Explorer Camp",
                name_az="City Explorer Camp",
                name_en="City Explorer Camp",
                description_ru="Городской лагерь с экскурсиями, спортом, STEM-активностями и насыщенной программой на каникулах.",
                description_az="Ekskursiyalar, idman və STEM fəaliyyətləri ilə şəhər düşərgəsi.",
                description_en="A city camp with excursions, sports, and STEM activities during school breaks.",
                address="8-ci mikrorayon, Cəfər Xəndan küç. 21, Bakı",
                phone="+994 50 321 10 70",
                instagram="cityexplorercamp",
                website="https://example.com/city-explorer-camp",
                schedule="Yay və qış növbələri 09:00-18:00; transfer seçimi ayrıca.",
                extra_conditions="Nahar daxildir, gündəlik foto hesabat göndərilir, qruplar yaşa görə bölünür.",
                photo_path="static/img/home/photos/family-park.jpg",
            ),
            DemoPlaceTemplate(
                slug="smart-chess-club",
                category="EDU",
                district="Nəsimi",
                metro="28 May",
                age_from=5,
                age_to=13,
                price_from=70,
                price_to=120,
                lat=40.38161,
                lng=49.84891,
                is_verified=True,
                rating_avg=4.8,
                rating_count=71,
                name_ru="Smart Chess Club",
                name_az="Smart Chess Club",
                name_en="Smart Chess Club",
                description_ru="Шахматный клуб с турнирными группами, логическими разминками и программой для начинающих.",
                description_az="Turnir qrupları, məntiq məşqləri və yeni başlayanlar üçün proqramı olan şahmat klubu.",
                description_en="A chess club with tournament groups, logic warmups, and a clear beginner pathway.",
                address="Səməd Vurğun küç. 34, Bakı",
                phone="+994 50 321 10 80",
                instagram="smartchessclub",
                website="https://example.com/smart-chess-club",
                schedule="B.e., Ç.a., C. 16:30-19:00; şənbə turnir məşqi 10:30.",
                extra_conditions="Reytinq qrupu və həvəskar qrupu ayrıdır, aylıq mini-turnirlər keçirilir.",
                photo_path="static/img/home/photos/team-hands.jpg",
            ),
            DemoPlaceTemplate(
                slug="rhythm-dance-family-studio",
                category="FUN",
                district="Yasamal",
                metro="İnşaatçılar",
                age_from=4,
                age_to=12,
                price_from=80,
                price_to=135,
                lat=40.38963,
                lng=49.80119,
                is_verified=False,
                rating_avg=4.4,
                rating_count=37,
                name_ru="Rhythm Dance Family Studio",
                name_az="Rhythm Dance Family Studio",
                name_en="Rhythm Dance Family Studio",
                description_ru="Танцевальная студия с modern kids, ритмикой и семейными открытыми уроками.",
                description_az="Modern kids, ritmika və ailə üçün açıq dərslərlə rəqs studiyası.",
                description_en="A dance studio offering modern kids, rhythm classes, and open family sessions.",
                address="Mətbuat prospekti 27, Bakı",
                phone="+994 50 321 10 90",
                instagram="rhythmdancefamily",
                website="https://example.com/rhythm-dance-family-studio",
                schedule="Ç.a., C.a., C. 17:00-19:00; şənbə mini səhnə məşqi 12:00.",
                extra_conditions="Qızlar və qarışıq qruplar var, mövsüm sonu kiçik səhnə çıxışı təşkil olunur.",
                photo_path="static/img/home/photos/family-dance.jpg",
            ),
            DemoPlaceTemplate(
                slug="little-architects-lab",
                category="TECH",
                district="Xətai",
                metro="Xətai",
                age_from=8,
                age_to=14,
                price_from=100,
                price_to=170,
                lat=40.38325,
                lng=49.87242,
                is_verified=True,
                rating_avg=4.7,
                rating_count=52,
                name_ru="Little Architects Lab",
                name_az="Little Architects Lab",
                name_en="Little Architects Lab",
                description_ru="Практический STEM-клуб по моделированию, 3D-макетам и городским проектам для детей.",
                description_az="Model qurma, 3D maket və şəhər layihələri üzrə praktik STEM dərnəyi.",
                description_en="A hands-on STEM club for modeling, 3D builds, and city design projects.",
                address="Xocalı prospekti 37A, Bakı",
                phone="+994 50 321 11 00",
                instagram="littlearchitectslab",
                website="https://example.com/little-architects-lab",
                schedule="B.e., C.a., C. 17:00-19:15; həftəsonu böyük layihə sessiyası.",
                extra_conditions="Kiçik komandalarla işlənir, materiallar daxildir, hər mövsüm sonunda təqdimat günü olur.",
                photo_path="static/img/home/photos/kids-craft.jpg",
            ),
            DemoPlaceTemplate(
                slug="vocal-kids-house",
                category="MUS",
                district="Səbail",
                metro="İçərişəhər",
                age_from=6,
                age_to=16,
                price_from=115,
                price_to=190,
                lat=40.36685,
                lng=49.83241,
                is_verified=True,
                rating_avg=4.9,
                rating_count=64,
                name_ru="Vocal Kids House",
                name_az="Vocal Kids House",
                name_en="Vocal Kids House",
                description_ru="Студия эстрадного вокала и сценического движения с подготовкой к выступлениям и записям.",
                description_az="Estrada vokalı və səhnə hərəkəti studiyası, çıxış və qeyd hazırlığı ilə.",
                description_en="A vocal and stage movement studio preparing children for performances and recordings.",
                address="Kiçik Qala küç. 8, Bakı",
                phone="+994 50 321 11 10",
                instagram="vocalkidshouse",
                website="https://example.com/vocal-kids-house",
                schedule="B.e.-C. 15:00-19:00; bazar günü duet qrupu 12:30.",
                extra_conditions="Fərdi vokal otaqları və ümumi səhnə məşq zonası var, ayda bir video çəkiliş edilir.",
                photo_path="static/img/home/photos/music-lesson.jpg",
            ),
            DemoPlaceTemplate(
                slug="brush-and-clay-academy",
                category="ART",
                district="Nərimanov",
                metro="Nəriman Nərimanov",
                age_from=5,
                age_to=13,
                price_from=85,
                price_to=145,
                lat=40.40518,
                lng=49.87112,
                is_verified=True,
                rating_avg=4.6,
                rating_count=43,
                name_ru="Brush & Clay Academy",
                name_az="Brush & Clay Academy",
                name_en="Brush and Clay Academy",
                description_ru="Академия рисунка, керамики и дизайна для детей с регулярными тематическими неделями.",
                description_az="Rəsm, keramika və dizayn akademiyası, tematik həftələrlə.",
                description_en="An academy for drawing, ceramics, and design with rotating themed weeks.",
                address="Təbriz küç. 54, Bakı",
                phone="+994 50 321 11 20",
                instagram="brushandclayacademy",
                website="https://example.com/brush-and-clay-academy",
                schedule="Ç.a., C.a., Ş. 15:00-18:30; bazar günü keramika workshop-u.",
                extra_conditions="Əsərlər qurudulub təqdim olunur, material paketi daxildir, mini sərgi divarı mövcuddur.",
                photo_path="static/img/home/photos/art-drawing.jpg",
            ),
            DemoPlaceTemplate(
                slug="active-kids-gym-park",
                category="SPRT",
                district="Binəqədi",
                metro="Azadlıq prospekti",
                age_from=4,
                age_to=11,
                price_from=70,
                price_to=125,
                lat=40.42688,
                lng=49.84171,
                is_verified=False,
                rating_avg=4.5,
                rating_count=34,
                name_ru="Active Kids Gym Park",
                name_az="Active Kids Gym Park",
                name_en="Active Kids Gym Park",
                description_ru="Спортивный центр для ОФП, гимнастики и подвижных игр с мягким залом для малышей.",
                description_az="Ümumi fiziki hazırlıq, gimnastika və hərəkətli oyunlar üçün uşaq idman mərkəzi.",
                description_en="A sports center for fitness, gymnastics, and active play with a soft gym area for younger children.",
                address="Azadlıq prospekti 189, Bakı",
                phone="+994 50 321 11 30",
                instagram="activekidsgympark",
                website="https://example.com/active-kids-gym-park",
                schedule="Hər gün 15:00-20:00; səhər məktəbəqədər qrup 10:00.",
                extra_conditions="Yumşaq təhlükəsiz zal, qısa adaptasiya proqramı və valideyn izləmə günləri var.",
                photo_path="static/img/home/photos/sports-class.jpg",
            ),
            DemoPlaceTemplate(
                slug="english-story-club",
                category="EDU",
                district="Səbail",
                metro="Sahil",
                age_from=5,
                age_to=12,
                price_from=85,
                price_to=135,
                lat=40.37274,
                lng=49.84417,
                is_verified=True,
                rating_avg=4.7,
                rating_count=57,
                name_ru="English Story Club",
                name_az="English Story Club",
                name_en="English Story Club",
                description_ru="Языковой клуб с чтением, театром и разговорными активностями для детей, которым нужен живой английский.",
                description_az="Oxu, teatr və danışıq fəaliyyəti ilə canlı ingilis dili klubu.",
                description_en="A language club combining reading, theater, and speaking activities for practical English.",
                address="Nizami küç. 90, Bakı",
                phone="+994 50 321 11 40",
                instagram="englishstoryclub.az",
                website="https://example.com/english-story-club",
                schedule="B.e., Ç.a., C. 16:00-18:15; şənbə speaking theatre 11:30.",
                extra_conditions="Kiçik kitab rəfi, rol oyunları və müəllim tərəfindən aylıq speaking feedback təqdim olunur.",
                photo_path="static/img/home/photos/family-studio.jpg",
            ),
            DemoPlaceTemplate(
                slug="maker-garage-junior",
                category="TECH",
                district="Nərimanov",
                metro="Koroğlu",
                age_from=9,
                age_to=16,
                price_from=130,
                price_to=210,
                lat=40.41942,
                lng=49.91853,
                is_verified=True,
                rating_avg=4.8,
                rating_count=46,
                name_ru="Maker Garage Junior",
                name_az="Maker Garage Junior",
                name_en="Maker Garage Junior",
                description_ru="Инженерный клуб с Arduino, макетированием и командными прототипами для подростков.",
                description_az="Arduino, maket qurma və komanda prototipləri üzrə yeniyetmələr üçün mühəndislik klubu.",
                description_en="An engineering club for teens focused on Arduino, prototyping, and team builds.",
                address="Ziya Bünyadov prospekti 1965, Bakı",
                phone="+994 50 321 11 50",
                instagram="makergaragejunior",
                website="https://example.com/maker-garage-junior",
                schedule="Ç.a., C.a., Ş. 17:30-20:00; şənbə open lab 13:00.",
                extra_conditions="Laboratoriya formatı, təhlükəsizlik brifinqi və layihə nümayişi günü mövcuddur.",
                photo_path="static/img/home/photos/team-hands.jpg",
            ),
            DemoPlaceTemplate(
                slug="little-canvas-baku",
                category="ART",
                district="Xətai",
                metro="Əhmədli",
                age_from=4,
                age_to=11,
                price_from=75,
                price_to=130,
                lat=40.38461,
                lng=49.95382,
                is_verified=False,
                rating_avg=4.4,
                rating_count=29,
                name_ru="Little Canvas Baku",
                name_az="Little Canvas Baku",
                name_en="Little Canvas Baku",
                description_ru="Уютная арт-студия для младших групп: рисунок, коллаж, поделки и семейные выходные мастер-классы.",
                description_az="Kiçik yaş qrupları üçün rahat art-studiya: rəsm, kollaj, əl işləri və ailə workshop-ları.",
                description_en="A cozy art studio for younger children with drawing, collage, crafts, and family workshops.",
                address="Məhəmməd Hadi küç. 112, Bakı",
                phone="+994 50 321 11 60",
                instagram="littlecanvasbaku",
                website="https://example.com/little-canvas-baku",
                schedule="B.e., C.a., C. 15:00-18:00; bazar günü family art 12:00.",
                extra_conditions="Təhlükəsiz materiallar, kiçik qruplar və valideynli workshop seçimləri mövcuddur.",
                photo_path="static/img/home/photos/kids-craft.jpg",
            ),
            DemoPlaceTemplate(
                slug="family-stage-musical-lab",
                category="MUS",
                district="Nəsimi",
                metro="Memar Əcəmi",
                age_from=7,
                age_to=15,
                price_from=110,
                price_to=185,
                lat=40.41453,
                lng=49.82845,
                is_verified=True,
                rating_avg=4.7,
                rating_count=41,
                name_ru="Family Stage Musical Lab",
                name_az="Family Stage Musical Lab",
                name_en="Family Stage Musical Lab",
                description_ru="Мюзикл-лаборатория с вокалом, актерским мастерством и пластикой для детей, которым нравится сцена.",
                description_az="Vokal, aktyorluq və plastika ilə səhnəni sevən uşaqlar üçün musical laboratoriyası.",
                description_en="A musical theater lab mixing vocals, acting, and movement for children who enjoy the stage.",
                address="Cavadxan küç. 41, Bakı",
                phone="+994 50 321 11 70",
                instagram="familystagemusicallab",
                website="https://example.com/family-stage-musical-lab",
                schedule="Ç.a., C.a., C. 16:30-19:30; ayda bir açıq məşq.",
                extra_conditions="Səhnə geyimi üzrə məsləhət, qrup etüdləri və açıq məşq günləri keçirilir.",
                photo_path="static/img/home/photos/music-lesson.jpg",
            ),
            DemoPlaceTemplate(
                slug="weekend-adventure-club",
                category="FUN",
                district="Sabunçu",
                metro="Koroğlu",
                age_from=6,
                age_to=13,
                price_from=65,
                price_to=120,
                lat=40.43081,
                lng=49.96364,
                is_verified=False,
                rating_avg=4.3,
                rating_count=24,
                name_ru="Weekend Adventure Club",
                name_az="Weekend Adventure Club",
                name_en="Weekend Adventure Club",
                description_ru="Клуб выходного дня с активными играми, mini quests и творческими паузами для детей и друзей.",
                description_az="Aktiv oyunlar, mini quest-lər və yaradıcı fasilələrlə həftəsonu klubu.",
                description_en="A weekend club with active games, mini quests, and creative breaks for children and friends.",
                address="Babək prospekti 76, Bakı",
                phone="+994 50 321 11 80",
                instagram="weekendadventureclub",
                website="https://example.com/weekend-adventure-club",
                schedule="Şənbə-bazar 11:00-18:00; qrup rezervasiyası mümkündür.",
                extra_conditions="Hava uyğun olduqda açıq hava hissəsi işləyir, müəllim nəzarəti və snack fasiləsi var.",
                photo_path="static/img/home/photos/family-park.jpg",
            ),
            DemoPlaceTemplate(
                slug="junior-football-academy-baku",
                category="SPRT",
                district="Sabunçu",
                metro="Koroğlu",
                age_from=5,
                age_to=15,
                price_from=85,
                price_to=150,
                lat=40.43174,
                lng=49.94722,
                is_verified=True,
                rating_avg=4.8,
                rating_count=113,
                name_ru="Junior Football Academy Baku",
                name_az="Junior Football Academy Baku",
                name_en="Junior Football Academy Baku",
                description_ru="Футбольная академия с детскими командами, координацией, вратарской группой и матчами по выходным.",
                description_az="Uşaq komandaları, koordinasiya və qapıçı qrupu olan futbol akademiyası.",
                description_en="A football academy with youth teams, coordination training, goalkeeper groups, and weekend matches.",
                address="Heydər Əliyev prospekti 109, Bakı",
                phone="+994 50 321 11 90",
                instagram="juniorfootballbaku",
                website="https://example.com/junior-football-academy-baku",
                schedule="B.e., Ç.a., C.a., C. 17:00-20:00; şənbə oyun günü 10:00.",
                extra_conditions="Açıq və qapalı məşq formatı, ilkin səviyyə qrupu və valideynlər üçün aylıq icmal var.",
                photo_path="static/img/home/photos/sports-class.jpg",
            ),
            DemoPlaceTemplate(
                slug="city-science-camp",
                category="CAMP",
                district="Nərimanov",
                metro="Nəriman Nərimanov",
                age_from=8,
                age_to=14,
                price_from=180,
                price_to=320,
                lat=40.40481,
                lng=49.86896,
                is_verified=True,
                rating_avg=4.9,
                rating_count=38,
                name_ru="City Science Camp",
                name_az="City Science Camp",
                name_en="City Science Camp",
                description_ru="Каникульный городской лагерь с наукой, прогулками, спортом и творческими проектами по неделям.",
                description_az="Elm, gəzinti, idman və yaradıcı layihələrlə həftəlik şəhər düşərgəsi.",
                description_en="A weekly city camp with science, walks, sports, and creative projects during school breaks.",
                address="Təbriz küç. 88, Bakı",
                phone="+994 50 321 12 00",
                instagram="citysciencecamp",
                website="https://example.com/city-science-camp",
                schedule="Məzuniyyət mövsümü 09:00-18:00; erkən gətirmə 08:30-dan.",
                extra_conditions="Qidalanma, ekskursiya günləri və gündəlik valideyn xülasəsi daxildir.",
                photo_path="static/img/home/photos/family-park.jpg",
            ),
        ]
