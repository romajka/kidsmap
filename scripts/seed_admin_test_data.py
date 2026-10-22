"""Seed rich and realistic test data for the admin panel.

Runs only in the disposable QA04 database; never against production.
"""
import os
import sys
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import F, Q

from catalog.models import (
    Category,
    Subcategory,
    Place,
    Organization,
    Program,
    Activity,
    OfferingGroup,
    Event,
    Specialist,
    SpecialistSpecialization,
    PlaceReview,
    PlaceOwnershipRequest,
    OrganizationGrant,
    District,
)

from catalog.services.catalog_conversion import _require_isolated_database

def run():
    _require_isolated_database()
    print("=== SEEDING ADMIN TEST DATA ===")
    now = timezone.now()
    User = get_user_model()

    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin', 'admin@kidsmap.az', 'admin')
        print(f"Created superuser: {admin_user.username}")
    else:
        print(f"Using superuser: {admin_user.username}")

    test_user, _ = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@kidsmap.az', 'is_active': True}
    )

    # ---------------------------------------------------------
    # 1. ORGANIZATIONS
    # ---------------------------------------------------------
    orgs_data = [
        {
            'name_az': 'Bakı Uşaq Akademiyası',
            'name_ru': 'Бакинская Детская Академия',
            'name_en': 'Baku Kids Academy',
            'description_az': 'Uşaqların intellektual və yaradıcı inkişafı üzrə qabaqcıl təhsil şəbəkəsi. Məktəbəqədər hazırlıq, STEAM və dillər.',
            'description_ru': 'Ведущая сеть образовательных центров для интеллектуального и творческого развития детей. Подготовка к школе, STEAM и языки.',
            'description_en': 'Leading educational network for intellectual and creative development of children. Preschool prep, STEAM and languages.',
            'phone': '+994 12 493 00 11',
            'whatsapp': '+994 50 200 11 22',
            'website': 'https://bakukidsacademy.az',
            'status': 'published',
            'owner': admin_user,
            'ownership_verified_at': now,
        },
        {
            'name_az': 'Junior İdman Klubu Bakı',
            'name_ru': 'Юниор Спорт Клуб Баку',
            'name_en': 'Junior Sport Club Baku',
            'description_az': '4-16 yaşlı uşaqlar üçün peşəkar idman bölmələri şəbəkəsi: cüdo, üzgüçülük, gimnastika və futbol.',
            'description_ru': 'Сеть профессиональных спортивных секций для детей 4-16 лет: дзюдо, плавание, гимнастика и футбол.',
            'description_en': 'Network of professional sports sections for kids aged 4-16: judo, swimming, gymnastics and football.',
            'phone': '+994 12 564 33 44',
            'whatsapp': '+994 55 300 44 55',
            'website': 'https://juniorsport.az',
            'status': 'published',
            'owner': admin_user,
            'ownership_verified_at': now,
        },
        {
            'name_az': 'Harmoniya İncəsənət və Musiqi Studiyası',
            'name_ru': 'Студия искусств и музыки Гармония',
            'name_en': 'Harmoniya Art & Music Studio',
            'description_az': 'Rəsm, keramika, vokal və fortepiano üzrə uşaq və yeniyetmələr üçün yaradıcılıq emalatxanası.',
            'description_ru': 'Творческая мастерская живописи, керамики, вокала и фортепиано для детей и подростков.',
            'description_en': 'Creative workshop for painting, ceramics, vocals and piano for kids and teens.',
            'phone': '+994 12 498 77 88',
            'whatsapp': '+994 70 400 77 88',
            'website': 'https://harmoniya-art.az',
            'status': 'published',
            'owner': test_user,
            'ownership_verified_at': now,
        },
        {
            'name_az': 'Smart Şahmat və Məntiq Klubu',
            'name_ru': 'Шахматный клуб Смарт Чесс',
            'name_en': 'Smart Chess & Logic Club',
            'description_az': 'FIDE ustaları tərəfindən uşaqlar üçün şahmat və məntiq dərsləri. Bakı və beynəlxalq turnirlərə hazırlıq.',
            'description_ru': 'Обучение шахматам и логике для детей от мастеров FIDE. Подготовка к городским и международным турнирам.',
            'description_en': 'Chess and logic training for kids by FIDE masters. Preparing for local and international tournaments.',
            'phone': '+994 12 510 22 33',
            'whatsapp': '+994 51 500 22 33',
            'website': 'https://smartchess.az',
            'status': 'published',
            'owner': test_user,
            'ownership_verified_at': now,
        },
        {
            'name_az': 'Baby Land Montessori Mərkəzi',
            'name_ru': 'Центр раннего развития Монтессори',
            'name_en': 'Baby Land Montessori Center',
            'description_az': '1.5 - 6 yaşlı uşaqlar üçün beynəlxalq standartlı Montessori inkişaf mühiti və ingilis dilli qruplar.',
            'description_ru': 'Международная среда Монтессори для гармоничного развития малышей от 1.5 до 6 лет и билингвальные группы.',
            'description_en': 'International Montessori environment for toddlers aged 1.5 to 6 and bilingual groups.',
            'phone': '+994 12 437 88 99',
            'whatsapp': '+994 50 600 88 99',
            'website': 'https://babyland.az',
            'status': 'pending',  # Moderation test
            'owner': test_user,
            'ownership_verified_at': None,
        },
    ]

    orgs = {}
    for data in orgs_data:
        org = Organization.objects.filter(name_az=data['name_az']).first()
        if not org:
            org = Organization.objects.create(
                created_by=admin_user,
                **data
            )
            print(f"Created Organization: {org.name_ru} [{org.status}]")
        else:
            for k, v in data.items():
                setattr(org, k, v)
            org.save()
            print(f"Updated Organization: {org.name_ru} [{org.status}]")
        orgs[data['name_az']] = org

    # ---------------------------------------------------------
    # 2. LINK EXISTING PLACES TO ORGANIZATIONS
    # ---------------------------------------------------------
    # Link sports places to Junior Sport Club
    sport_org = orgs['Junior İdman Klubu Bakı']
    judo_places = Place.objects.filter(
        Q(name_ru__icontains='дзюдо') | Q(name_az__icontains='cüdo') | Q(category_id='SPRT'),
        deleted_at__isnull=True
    )[:3]
    for p in judo_places:
        Place.objects.filter(pk=p.pk).update(
            organization=sport_org,
            organization_relationship_kind='business',
            organization_join_org_ownership_version=sport_org.ownership_version,
            organization_join_place_ownership_version=p.ownership_version,
        )
        print(f"Linked Place #{p.pk} ({p.name_ru or p.name}) -> {sport_org.name_ru}")

    # Link art/dance places to Harmoniya
    harmoniya_org = orgs['Harmoniya İncəsənət və Musiqi Studiyası']
    art_places = Place.objects.filter(
        Q(name_ru__icontains='танцы') | Q(name_az__icontains='İnkişaf') | Q(category_id='dance'),
        deleted_at__isnull=True
    )[:2]
    for p in art_places:
        Place.objects.filter(pk=p.pk).update(
            organization=harmoniya_org,
            organization_relationship_kind='business',
            organization_join_org_ownership_version=harmoniya_org.ownership_version,
            organization_join_place_ownership_version=p.ownership_version,
        )
        print(f"Linked Place #{p.pk} ({p.name_ru or p.name}) -> {harmoniya_org.name_ru}")

    # Link entertainment places to Baku Kids Academy if not linked
    edu_org = orgs['Bakı Uşaq Akademiyası']
    other_places = Place.objects.filter(
        deleted_at__isnull=True,
        organization__isnull=True
    )[:2]
    for p in other_places:
        Place.objects.filter(pk=p.pk).update(
            organization=edu_org,
            organization_relationship_kind='business',
            organization_join_org_ownership_version=edu_org.ownership_version,
            organization_join_place_ownership_version=p.ownership_version,
        )
        print(f"Linked Place #{p.pk} ({p.name_ru or p.name}) -> {edu_org.name_ru}")

    # ---------------------------------------------------------
    # 3. PROGRAMS
    # ---------------------------------------------------------
    tech_cat = Category.objects.filter(code='TECH').first() or Category.objects.filter(code='intellect-skills').first()
    edu_cat = Category.objects.filter(code='EDU').first() or Category.objects.filter(code='early-development').first()
    sprt_cat = Category.objects.filter(code='SPRT').first()
    art_cat = Category.objects.filter(code='ART').first() or Category.objects.filter(code='dance').first()

    programs_data = [
        {
            'organization': orgs['Bakı Uşaq Akademiyası'],
            'category': tech_cat,
            'name_az': 'STEAM və Robototexnika',
            'name_ru': 'STEAM и Робототехника',
            'name_en': 'STEAM & Robotics',
            'description_az': 'Lego Spike və Arduino əsasında mühəndislik və proqramlaşdırma əsasları.',
            'description_ru': 'Основы конструирования, схемотехники и программирования на базе Lego Spike и Arduino.',
            'description_en': 'Foundations of engineering and programming based on Lego Spike and Arduino.',
            'status': 'published',
        },
        {
            'organization': orgs['Bakı Uşaq Akademiyası'],
            'category': edu_cat,
            'name_az': 'Məktəbəqədər intensiv hazırlıq',
            'name_ru': 'Интенсивная подготовка к школе',
            'name_en': 'Intensive Preschool Preparation',
            'description_az': 'Oxu, yazı, riyaziyyat və məntiqin kompleks inkişaf proqramı (5-7 yaş).',
            'description_ru': 'Комплексная программа подготовки: чтение, письмо, математика и логика (5-7 лет).',
            'description_en': 'Comprehensive preparation program: reading, writing, mathematics and logic (5-7 yrs).',
            'status': 'published',
        },
        {
            'organization': orgs['Junior İdman Klubu Bakı'],
            'category': sprt_cat,
            'name_az': 'Uşaq cüdo bölməsi',
            'name_ru': 'Секция детского дзюдо',
            'name_en': 'Junior Judo Section',
            'description_az': 'Yapon texnikası əsasında intizam, güc və dözümlülüyün inkişafı (4-15 yaş).',
            'description_ru': 'Развитие силы, координации, гибкости и самодисциплины по японской методике (4-15 лет).',
            'description_en': 'Developing strength, coordination and discipline through traditional Japanese methods.',
            'status': 'published',
        },
        {
            'organization': orgs['Junior İdman Klubu Bakı'],
            'category': sprt_cat,
            'name_az': 'Gənc üzgüçülər məktəbi',
            'name_ru': 'Школа юных пловцов',
            'name_en': 'Young Swimmers Academy',
            'description_az': 'Sudan qorxunun aradan qaldırılması, təməl üzmə texnikası və fiziki inkişaf.',
            'description_ru': 'Обучение плаванию с нуля, постановка правильного дыхания и стилей плавания.',
            'description_en': 'Swimming lessons from beginner to advanced styles with breath control.',
            'status': 'published',
        },
        {
            'organization': orgs['Harmoniya İncəsənət və Musiqi Studiyası'],
            'category': art_cat,
            'name_az': 'Akademik rəsm və yaradıcılıq',
            'name_ru': 'Академический рисунок и творчество',
            'name_en': 'Academic Drawing & Fine Arts',
            'description_az': 'Akvarel, quaş, qrafika və kompozisiya əsasları.',
            'description_ru': 'Обучение академическому рисунку, акварели, композиции и цветоведению.',
            'description_en': 'Teaching academic drawing, watercolor, composition and color theory.',
            'status': 'published',
        },
        {
            'organization': orgs['Smart Şahmat və Məntiq Klubu'],
            'category': tech_cat,
            'name_az': 'Şahmat ustalığı və taktika',
            'name_ru': 'Шахматное мастерство и тактика',
            'name_en': 'Chess Mastery & Tactics',
            'description_az': 'Dərəcəli şahmatçıların yetişdirilməsi, kombinasional görmə və oyun analizi.',
            'description_ru': 'Подготовка шахматистов-разрядников, развитие стратегического и логического мышления.',
            'description_en': 'Developing strategic thinking, tactical vision and tournament analysis.',
            'status': 'published',
        },
    ]

    programs = []
    for data in programs_data:
        prog = Program.objects.filter(
            organization=data['organization'],
            name_az=data['name_az']
        ).first()
        if not prog:
            prog = Program.objects.create(
                created_by=admin_user,
                **data
            )
            print(f"Created Program: {prog.name_ru} ({prog.organization.name_ru})")
        else:
            for k, v in data.items():
                setattr(prog, k, v)
            prog.save()
            print(f"Updated Program: {prog.name_ru}")
        programs.append(prog)

    # ---------------------------------------------------------
    # 4. ACTIVITIES & OFFERING GROUPS
    # ---------------------------------------------------------
    for prog in programs:
        # Find places belonging to this organization
        org_places = Place.objects.filter(organization=prog.organization, deleted_at__isnull=True)
        if not org_places.exists():
            continue
        for place in org_places[:2]:
            act = Activity.objects.filter(place=place, program=prog).first()
            if not act:
                act = Activity.objects.create(
                    place=place,
                    program=prog,
                    category=prog.category,
                    name_az=prog.name_az,
                    name_ru=prog.name_ru,
                    name_en=prog.name_en,
                    description_az=prog.description_az,
                    description_ru=prog.description_ru,
                    description_en=prog.description_en,
                    status='published'
                )
                print(f"Created Activity: {act.name_ru} at place #{place.pk}")

            # Offering groups
            grp1 = OfferingGroup.objects.filter(activity=act, name_ru='Младшая группа').first()
            if not grp1:
                OfferingGroup.objects.create(
                    activity=act,
                    name_az='Kiçik qrup',
                    name_ru='Младшая группа',
                    name_en='Junior Group',
                    age_from=4,
                    age_to=6,
                    lesson_format='group',
                    language='Azərbaycan, Rus',
                    schedule_text='Çərşənbə axşamı, Cümə axşamı 16:00 - 17:00',
                    teachers_text='Ali təhsilli təcrübəli mütəxəssislər',
                )
            grp2 = OfferingGroup.objects.filter(activity=act, name_ru='Основная группа').first()
            if not grp2:
                OfferingGroup.objects.create(
                    activity=act,
                    name_az='Əsas qrup',
                    name_ru='Основная группа',
                    name_en='Standard Group',
                    age_from=7,
                    age_to=12,
                    lesson_format='group',
                    language='Azərbaycan, Rus, İngilis',
                    schedule_text='Bazar ertəsi, Çərşənbə, Cümə 17:30 - 19:00',
                    teachers_text='Baş məşqçi və beynəlxalq dərəcəli pedaqoqlar',
                )
            grp3 = OfferingGroup.objects.filter(activity=act, name_ru='Индивидуальные занятия').first()
            if not grp3:
                OfferingGroup.objects.create(
                    activity=act,
                    name_az='Fərdi dərslər',
                    name_ru='Индивидуальные занятия',
                    name_en='Private Lessons',
                    age_from=4,
                    age_to=16,
                    lesson_format='individual',
                    language='İstənilən',
                    schedule_text='Fərdi cədvəl üzrə razılaşma ilə',
                    teachers_text='Fərdi mentor',
                )

    # ---------------------------------------------------------
    # 5. ORGANIZATION GRANTS
    # ---------------------------------------------------------
    for org in [orgs['Bakı Uşaq Akademiyası'], orgs['Junior İdman Klubu Bakı']]:
        grant, created = OrganizationGrant.objects.get_or_create(
            organization=org,
            member=test_user,
            defaults={
                'owner': org.owner,
                'role': 'EDITOR',
                'actions': ['organization.view', 'organization.edit', 'program.manage'],
                'scope': 'all_network',
                'is_active': True,
                'base_ownership_version': org.ownership_version,
            }
        )
        if created:
            print(f"Created Grant: testuser -> {org.name_ru}")

    # ---------------------------------------------------------
    # 6. EVENTS
    # ---------------------------------------------------------
    active_pub_places = list(Place.objects.filter(deleted_at__isnull=True, is_active=True, status='published'))
    venue_place = active_pub_places[0] if active_pub_places else None

    events_data = [
        {
            'slug': 'baku-autumn-chess-cup-2026',
            'organizer_organization': orgs['Smart Şahmat və Məntiq Klubu'],
            'organizer_resolution': 'resolved',
            'event_format': 'physical',
            'occurrence_state': 'scheduled',
            'status': 'published',
            'name_az': 'Bakı Uşaq Şahmat Kuboku — Payız 2026',
            'name_ru': 'Бакинский детский шахматный кубок — Осень 2026',
            'name_en': 'Baku Youth Chess Cup — Autumn 2026',
            'description_az': '6-14 yaşlı uşaqlar arasında rapid şahmat turniri. Medallar, diplomlar və dəyərli hədiyyələr.',
            'description_ru': 'Турнир по быстрым шахматам среди детей 6-14 лет. Медали, дипломы и ценные призы.',
            'description_en': 'Rapid chess tournament among kids aged 6-14. Medals, certificates and valuable prizes.',
            'category': tech_cat,
            'start_datetime': now + timedelta(days=4, hours=11),
            'end_datetime': now + timedelta(days=4, hours=16),
            'related_place': venue_place,
            'price_text': '25 AZN',
            'age_from': 6,
            'age_to': 14,
            'owner': admin_user,
        },
        {
            'slug': 'robotics-ai-open-masterclass-2026',
            'organizer_organization': orgs['Bakı Uşaq Akademiyası'],
            'organizer_resolution': 'resolved',
            'event_format': 'physical',
            'occurrence_state': 'scheduled',
            'status': 'published',
            'name_az': 'Robototexnika və süni intellekt üzrə ustad dərsi',
            'name_ru': 'Мастер-класс по робототехнике и ИИ',
            'name_en': 'Robotics & AI Masterclass for Kids',
            'description_az': 'Uşaqlar ilk robotlarını yığacaq və süni intellektin tətbiqi ilə tanış olacaqlar.',
            'description_ru': 'Дети соберут своего первого робота и познакомятся с основами машинного зрения и ИИ.',
            'description_en': 'Children will build their first robot and explore AI fundamentals.',
            'category': tech_cat,
            'start_datetime': now + timedelta(days=8, hours=14),
            'end_datetime': now + timedelta(days=8, hours=16),
            'related_place': venue_place,
            'price_text': 'Ödənişsiz / Бесплатно',
            'age_from': 7,
            'age_to': 13,
            'owner': admin_user,
        },
        {
            'slug': 'junior-judo-championship-baku-2026',
            'organizer_organization': orgs['Junior İdman Klubu Bakı'],
            'organizer_resolution': 'resolved',
            'event_format': 'physical',
            'occurrence_state': 'scheduled',
            'status': 'published',
            'name_az': 'Junior Cüdo Açıq Birinciliyi',
            'name_ru': 'Открытое первенство по дзюдо Junior Baku',
            'name_en': 'Junior Baku Judo Open Championship',
            'description_az': 'Klublararası açıq cüdo çempionatı. Bütün çəki dərəcələri üzrə mübarizə.',
            'description_ru': 'Межклубные соревнования по дзюдо. Борьба во всех весовых категориях.',
            'description_en': 'Inter-club judo competitions across all weight classes.',
            'category': sprt_cat,
            'start_datetime': now + timedelta(days=12, hours=10),
            'end_datetime': now + timedelta(days=12, hours=17),
            'related_place': venue_place,
            'price_text': 'Giriş sərbəstdir / Вход свободный',
            'age_from': 5,
            'age_to': 16,
            'owner': admin_user,
        },
        {
            'slug': 'clay-ceramics-autumn-workshop-2026',
            'organizer_organization': orgs['Harmoniya İncəsənət və Musiqi Studiyası'],
            'organizer_resolution': 'resolved',
            'event_format': 'physical',
            'occurrence_state': 'scheduled',
            'status': 'published',
            'name_az': 'Gil və keramika yaradıcılıq dərsi',
            'name_ru': 'Творческий воркшоп по гончарному делу и керамике',
            'name_en': 'Creative Pottery & Ceramics Workshop',
            'description_az': 'Dulus çarxında iş, gil fiqurların hazırlanması və boyanması.',
            'description_ru': 'Работа на гончарном круге, создание глиняной посуды и роспись ангобами.',
            'description_en': 'Pottery wheel experience, clay shaping and colorful ceramic painting.',
            'category': art_cat,
            'start_datetime': now + timedelta(days=15, hours=12),
            'end_datetime': now + timedelta(days=15, hours=14),
            'related_place': venue_place,
            'price_text': '20 AZN',
            'age_from': 4,
            'age_to': 15,
            'owner': admin_user,
        },
        {
            'slug': 'adhd-parent-seminar-baku-2026',
            'organizer_organization': orgs['Bakı Uşaq Akademiyası'],
            'organizer_resolution': 'resolved',
            'event_format': 'physical',
            'occurrence_state': 'scheduled',
            'status': 'pending',  # Moderation test
            'name_az': 'Valideynlər üçün seminar: Uşaqlarda diqqət və konsentrasiya',
            'name_ru': 'Семинар для родителей: Внимание и концентрация у детей',
            'name_en': 'Parenting Seminar: Focus and Attention in Kids',
            'description_az': 'Uşaq psixoloqu ilə açıq görüş və praktik tövsiyələr.',
            'description_ru': 'Практические рекомендации от детского нейропсихолога по развитию усидчивости и внимания.',
            'description_en': 'Practical recommendations from a child neuropsychologist on focus and patience.',
            'category': edu_cat,
            'start_datetime': now + timedelta(days=6, hours=18),
            'end_datetime': now + timedelta(days=6, hours=20),
            'related_place': venue_place,
            'price_text': 'Pulsuz qeydiyyat / Бесплатная регистрация',
            'age_from': 3,
            'age_to': 10,
            'owner': test_user,
        },
    ]

    for data in events_data:
        event = Event.objects.filter(slug=data['slug']).first()
        if not event:
            event = Event.objects.create(**data)
            print(f"Created Event: {event.name_ru} [{event.status}]")
        else:
            event._allow_occurrence_change = True
            for k, v in data.items():
                setattr(event, k, v)
            event.save()
            print(f"Updated Event: {event.name_ru} [{event.status}]")

    # ---------------------------------------------------------
    # 7. SPECIALISTS
    # ---------------------------------------------------------
    specialists_data = [
        {
            'slug': 'aysel-mammadova-logoped',
            'name': 'Айсель Мамедова',
            'name_alt': 'Aysel Məmmədova',
            'status': 'published',
            'is_active': True,
            'is_verified': True,
            'consultation_format': 'both',
            'experience_years': 8,
            'age_from': 3,
            'age_to': 10,
            'language_az': True,
            'language_ru': True,
            'language_en': False,
            'price_from': 40,
            'price_to': 60,
            'duration_minutes': 45,
            'phone': '+994 50 312 44 55',
            'whatsapp': '+994 50 312 44 55',
            'bio_ru': 'Детский логопед-дефектолог высшей категории. Запуск речи, коррекция звукопроизношения, дизартрия, заикание. Авторские игровые методики.',
            'bio_az': 'Ali dərəcəli uşaq loqoped-defektoloqu. Nitqin ləngiməsi, səs qüsurlarının korreksiyası, kəkələmənin aradan qaldırılması.',
            'bio_en': 'Senior pediatric speech therapist. Speech launch, pronunciation correction and fluency therapy.',
            'education_ru': 'БГУ, Факультет психологии и дефектологии. Магистратура МГПУ.',
            'specializations': ['speech_therapist', 'pathologist'],
        },
        {
            'slug': 'rauf-aliyev-judo-coach',
            'name': 'Рауф Алиев',
            'name_alt': 'Rauf Əliyev',
            'status': 'published',
            'is_active': True,
            'is_verified': True,
            'consultation_format': 'in_person',
            'experience_years': 12,
            'age_from': 5,
            'age_to': 16,
            'language_az': True,
            'language_ru': True,
            'language_en': True,
            'price_from': 50,
            'price_to': 80,
            'duration_minutes': 60,
            'phone': '+994 55 777 22 33',
            'whatsapp': '+994 55 777 22 33',
            'bio_ru': 'Мастер спорта по дзюдо, черный пояс II дан. Многократный призер чемпионатов Азербайджана. Воспитал чемпионов молодежных первенств.',
            'bio_az': 'Cüdo üzrə idman ustası, qara kəmər II dan. Azərbaycan çempionatlarının mükafatçısı. Gənclər arasında çempionlar yetişdirib.',
            'bio_en': 'Master of sports in judo, 2nd dan black belt. Trained multiple youth champions.',
            'education_ru': 'Азербайджанская государственная академия физической культуры и спорта.',
            'specializations': ['sports_coach', 'personal_trainer'],
        },
        {
            'slug': 'leyla-hasanova-neuropsychologist',
            'name': 'Лейла Гасанова',
            'name_alt': 'Leyla Həsənova',
            'status': 'published',
            'is_active': True,
            'is_verified': True,
            'consultation_format': 'both',
            'experience_years': 10,
            'age_from': 4,
            'age_to': 14,
            'language_az': True,
            'language_ru': True,
            'language_en': True,
            'price_from': 60,
            'price_to': 90,
            'duration_minutes': 50,
            'phone': '+994 70 888 11 22',
            'whatsapp': '+994 70 888 11 22',
            'bio_ru': 'Клинический детский нейропсихолог, специалист по сенсорной интеграции. Диагностика готовности к школе, коррекция СДВГ.',
            'bio_az': 'Klinik uşaq neyropsixoloqu, sensor inteqrasiya mütəxəssisi. Diqqət çatışmazlığı və hiperaktivlik korreksiyası.',
            'bio_en': 'Clinical child neuropsychologist, sensory integration specialist.',
            'education_ru': 'МГУ им. Ломоносова, клиническая психология. Сертификация Ayres Sensory Integration.',
            'specializations': ['child_psychologist', 'sensory_integration'],
        },
        {
            'slug': 'narmin-ismayilova-montessori-pedagogue',
            'name': 'Нармин Исмаилова',
            'name_alt': 'Nərmin İsmayılova',
            'status': 'pending',  # Moderation test
            'is_active': True,
            'is_verified': False,
            'consultation_format': 'in_person',
            'experience_years': 5,
            'age_from': 2,
            'age_to': 6,
            'language_az': True,
            'language_ru': True,
            'language_en': False,
            'price_from': 35,
            'price_to': 50,
            'duration_minutes': 45,
            'phone': '+994 51 444 33 22',
            'whatsapp': '+994 51 444 33 22',
            'bio_ru': 'Монтессори-педагог AMI (0-3, 3-6). Адаптация малышей к детскому саду, развитие самостоятельности и моторики.',
            'bio_az': 'AMI sertifikatlı Montessori pedaqoqu. Uşaqların bağçaya adaptasiyası, müstəqillik və xırda motorikanın inkişafı.',
            'bio_en': 'AMI certified Montessori educator for early childhood.',
            'education_ru': 'АГПУ, Дошкольное образование.',
            'specializations': ['early_development_specialist', 'primary_teacher'],
        },
    ]

    for data in specialists_data:
        specs_codes = data.pop('specializations', [])
        spec = Specialist.objects.filter(slug=data['slug']).first()
        if not spec:
            spec = Specialist.objects.create(
                created_by=admin_user,
                **data
            )
            print(f"Created Specialist: {spec.name} [{spec.status}]")
        else:
            for k, v in data.items():
                setattr(spec, k, v)
            spec.save()
            print(f"Updated Specialist: {spec.name} [{spec.status}]")

        for code in specs_codes:
            sp_obj = SpecialistSpecialization.objects.filter(code=code).first()
            if sp_obj:
                spec.specializations.add(sp_obj)

    # ---------------------------------------------------------
    # 8. REVIEWS
    # ---------------------------------------------------------
    review_places = Place.objects.filter(deleted_at__isnull=True)[:5]
    reviews_sample = [
        {
            'author_name': 'Нигяр Мамедова',
            'rating': 5,
            'text': 'Замечательный центр! Чисто, светло, педагоги внимательные и профессиональные. Ребенок идет на занятия с огромным удовольствием.',
            'status': 'published',
            'is_approved': True,
        },
        {
            'author_name': 'Эльмир Гусейнов',
            'rating': 5,
            'text': 'Отличные тренеры и дисциплина на высоте. Сын занимается дзюдо уже полгода, заметно окреп и стал более уверенным в себе.',
            'status': 'published',
            'is_approved': True,
        },
        {
            'author_name': 'Kamran Əliyev',
            'rating': 4,
            'text': 'Məkan çox rahatdır, müəllimlər mehribandır. Sadəcə parkinq tapmaq bəzən çətin olur, qalan hər şey əladır.',
            'status': 'published',
            'is_approved': True,
        },
        {
            'author_name': 'Sevinc Qasımova',
            'rating': 5,
            'text': 'Uşağımın nitqində qısa müddətdə böyük irəliləyiş oldu. Loqopedə dərin təşəkkürümüzü bildiririk!',
            'status': 'published',
            'is_approved': True,
        },
        {
            'author_name': 'Дмитрий Смирнов',
            'rating': 4,
            'text': 'Хорошая атмосфера, интересная программа по робототехнике. Рекомендую родителям.',
            'status': 'pending',  # Pending moderation review!
            'is_approved': False,
        },
        {
            'author_name': 'Leyla Rəhimova',
            'rating': 5,
            'text': 'İlk dərsimiz çox maraqlı keçdi, uşaq çox razı qaldı. Abunəlik götürdük.',
            'status': 'pending',  # Pending moderation review!
            'is_approved': False,
        },
    ]

    for i, rdata in enumerate(reviews_sample):
        place = review_places[i % len(review_places)]
        rev = PlaceReview.objects.filter(place=place, author_name=rdata['author_name']).first()
        if not rev:
            PlaceReview.objects.create(
                place=place,
                submitted_at=now - timedelta(days=i),
                is_current=True,
                **rdata
            )
            print(f"Created Review by {rdata['author_name']} for Place #{place.pk} [{rdata['status']}]")

    # ---------------------------------------------------------
    # 9. PLACE OWNERSHIP REQUEST (MODERATION)
    # ---------------------------------------------------------
    if review_places.exists():
        target_place = review_places[0]
        req = PlaceOwnershipRequest.objects.filter(place=target_place, status='PENDING').first()
        if not req:
            PlaceOwnershipRequest.objects.create(
                place=target_place,
                applicant=test_user,
                status='PENDING',
                request_kind='CLAIM',
                base_ownership_version=target_place.ownership_version,
                base_owner_id=target_place.owner_id,
                base_content_version=target_place.content_version,
                note='Я являюсь руководителем данного филиала, прошу подтвердить владение организацией.',
            )
            print(f"Created pending PlaceOwnershipRequest for Place #{target_place.pk}")

    print("=== SEEDING COMPLETED SUCCESSFULLY ===")

run()

