from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Event, Place, PlacePhoto, PlaceReview, Subcategory


@dataclass(frozen=True)
class DemoPlaceTemplate:
    slug: str
    category: str
    subcategory: str
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
    lesson_duration_minutes: int
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
    additional_info: str
    photo_path: str
    cover_photo_path: str
    gallery_photo_paths: tuple[str, ...]
    is_temporary: bool = False
    temporary_days_from_now: int | None = None
    temporary_duration_hours: int | None = None


@dataclass(frozen=True)
class DemoReviewTemplate:
    author_name: str
    rating: int
    text: str
    likes_count: int
    dislikes_count: int
    days_ago: int


@dataclass(frozen=True)
class DemoEventTemplate:
    slug: str
    name_ru: str
    name_az: str
    name_en: str
    description_ru: str
    description_az: str
    description_en: str
    start_in_days: int
    duration_hours: int
    price_text: str
    photo_path: str


class Command(BaseCommand):
    help = "Create 15 realistic demo places with full content, coordinates, photos, and gallery for catalog and map UI testing."

    DEMO_MARKER = "seed:catalog-demo"
    REVIEW_MARKER = "seed:catalog-demo-review"
    EVENT_MARKER = "seed:catalog-demo-event"
    MIN_PUBLIC_DESCRIPTION_LENGTH = 140

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=25,
            help="How many demo places to keep from the curated set. Default: 25.",
        )
        parser.add_argument(
            "--clear-old",
            action="store_true",
            help="Delete previously seeded demo places before creating a new batch.",
        )

    def handle(self, *args, **options):
        count = max(1, min(int(options["count"]), len(self._build_templates())))
        clear_old = bool(options["clear_old"])

        if clear_old:
            PlaceReview.objects.filter(session_key__startswith=self.REVIEW_MARKER).delete()
            Event.objects.filter(moderation_note__startswith=self.EVENT_MARKER).delete()
            deleted, _ = Place.objects.filter(additional_info__startswith=self.DEMO_MARKER).delete()
            self.stdout.write(f"Removed {deleted} old demo objects.")

        templates = self._build_templates()[:count]
        created = 0
        updated = 0

        for index, template in enumerate(templates, start=1):
            place = Place.objects.filter(slug=template.slug).first()
            is_created = place is None
            if place is None:
                place = Place(slug=template.slug)
            self._apply_defaults(place=place, index=index, template=template)
            place.save()
            self._sync_file_field(place=place, field_name="photo", source_relative_path=template.photo_path)
            self._sync_file_field(place=place, field_name="cover_photo", source_relative_path=template.cover_photo_path)
            place.save()
            self._sync_gallery(place=place, template=template)
            self._sync_reviews(place=place, template=template, index=index)
            self._sync_events(place=place, template=template, index=index)
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
        now = timezone.now()
        published_at = now - timedelta(days=30 - index)
        verified_at = published_at + timedelta(days=2) if template.is_verified else None
        subcategory = Subcategory.objects.filter(category_id=template.category, code=template.subcategory).first()
        temporary_start = None
        temporary_end = None
        if template.is_temporary and template.temporary_days_from_now is not None and template.temporary_duration_hours:
            temporary_start = now + timedelta(days=template.temporary_days_from_now, hours=10)
            temporary_end = temporary_start + timedelta(hours=template.temporary_duration_hours)

        place.name = template.name_ru
        place.name_ru = template.name_ru
        place.name_az = template.name_az
        place.name_en = template.name_en
        place.description_ru = self._ensure_public_description(
            template.description_ru,
            extra_text="Есть группы по возрасту, понятный формат записи, контакты для связи и достаточно деталей для проверки публичной карточки на сайте.",
        )
        place.description_az = self._ensure_public_description(
            template.description_az,
            extra_text="Yaş qrupları, qeydiyyat üçün aydın format, əlaqə məlumatları və saytda ictimai kartı yoxlamaq üçün kifayət qədər detal göstərilib.",
        )
        place.description_en = self._ensure_public_description(
            template.description_en,
            extra_text="Age-based groups, a clear enrollment flow, contact details, and enough detail to verify how the public place page renders on the site.",
        )
        place.category_id = template.category
        place.subcategory = subcategory
        place.district = template.district
        place.metro = template.metro
        place.address = template.address
        place.phone1 = template.phone
        place.instagram = template.instagram
        place.website = template.website
        place.schedule = template.schedule
        place.extra_conditions = template.extra_conditions
        place.additional_info = f"{self.DEMO_MARKER}:{index:02d}\n{template.additional_info}"
        place.age_from = template.age_from
        place.age_to = template.age_to
        place.price_from = template.price_from
        place.price_to = template.price_to
        place.price_per_lesson = max(template.price_from - 5, 30)
        place.price_per_month = template.price_to * 4
        place.price_per_8_lessons = template.price_to * 2
        place.lesson_duration_minutes = template.lesson_duration_minutes
        place.lat = template.lat
        place.lng = template.lng
        place.rating_avg = template.rating_avg
        place.rating_count = template.rating_count
        place.likes_count = 18 + index * 4
        place.is_active = True
        place.is_verified = template.is_verified
        place.status = Place.STATUS_PUBLISHED
        place.is_temporary = template.is_temporary
        place.temporary_start = temporary_start
        place.temporary_end = temporary_end
        place.rejection_reason = ""
        if place.published_at is None:
            place.published_at = published_at
        if template.is_verified and place.last_verified_at is None:
            place.last_verified_at = verified_at

    def _sync_file_field(self, *, place: Place, field_name: str, source_relative_path: str) -> None:
        source_path = self._repo_root() / source_relative_path
        if not source_path.exists():
            return

        target_name = f"demo-{place.slug}-{field_name}{source_path.suffix.lower()}"
        bound_field = getattr(place, field_name)
        current_name = Path(bound_field.name).name if bound_field and getattr(bound_field, "name", "") else ""
        if current_name == target_name:
            return

        if bound_field and getattr(bound_field, "name", ""):
            bound_field.delete(save=False)

        with source_path.open("rb") as source_file:
            getattr(place, field_name).save(target_name, File(source_file), save=False)

    def _sync_instance_file_field(self, *, instance, field_name: str, source_relative_path: str, target_name: str) -> None:
        source_path = self._repo_root() / source_relative_path
        if not source_path.exists():
            return

        bound_field = getattr(instance, field_name)
        current_name = Path(bound_field.name).name if bound_field and getattr(bound_field, "name", "") else ""
        if current_name == target_name:
            return

        if bound_field and getattr(bound_field, "name", ""):
            bound_field.delete(save=False)

        with source_path.open("rb") as source_file:
            getattr(instance, field_name).save(target_name, File(source_file), save=False)

    def _ensure_public_description(self, text: str, *, extra_text: str) -> str:
        value = (text or "").strip()
        if len(value) >= self.MIN_PUBLIC_DESCRIPTION_LENGTH:
            return value
        if value and not value.endswith((".", "!", "?")):
            value = f"{value}."
        return f"{value} {extra_text}".strip()

    def _sync_gallery(self, *, place: Place, template: DemoPlaceTemplate) -> None:
        existing_paths = [photo.image.name for photo in place.gallery.order_by("order", "id")]
        desired_names = []
        repo_root = self._repo_root()
        for index, relative_path in enumerate(template.gallery_photo_paths, start=1):
            source_path = repo_root / relative_path
            if not source_path.exists():
                continue
            desired_names.append(f"demo-{place.slug}-gallery-{index}{source_path.suffix.lower()}")

        if len(existing_paths) == len(desired_names) and all(Path(a).name == b for a, b in zip(existing_paths, desired_names)):
            return

        for gallery_item in place.gallery.all():
            if gallery_item.image and getattr(gallery_item.image, "name", ""):
                gallery_item.image.delete(save=False)
        place.gallery.all().delete()

        for index, relative_path in enumerate(template.gallery_photo_paths, start=1):
            source_path = repo_root / relative_path
            if not source_path.exists():
                continue
            target_name = f"demo-{place.slug}-gallery-{index}{source_path.suffix.lower()}"
            gallery_item = PlacePhoto(place=place, order=index, caption=f"{place.name_ru} #{index}")
            with source_path.open("rb") as source_file:
                gallery_item.image.save(target_name, File(source_file), save=False)
            gallery_item.save()

    def _sync_reviews(self, *, place: Place, template: DemoPlaceTemplate, index: int) -> None:
        PlaceReview.objects.filter(place=place, session_key__startswith=self.REVIEW_MARKER).delete()

        now = timezone.now()
        for review_index, review_template in enumerate(self._build_review_templates(template=template), start=1):
            review = PlaceReview.objects.create(
                place=place,
                author_name=review_template.author_name,
                is_anonymous=False,
                rating=review_template.rating,
                text=review_template.text,
                likes_count=review_template.likes_count,
                dislikes_count=review_template.dislikes_count,
                is_approved=True,
                status=PlaceReview.STATUS_APPROVED,
                session_key=f"{self.REVIEW_MARKER}:{place.slug}:{review_index}",
            )
            created_at = now - timedelta(days=review_template.days_ago + index)
            PlaceReview.objects.filter(pk=review.pk).update(created_at=created_at, updated_at=created_at)

        place.refresh_rating_stats()
        place.likes_count = 18 + index * 4
        place.save(update_fields=["rating_avg", "rating_count", "likes_count"])

    def _sync_events(self, *, place: Place, template: DemoPlaceTemplate, index: int) -> None:
        Event.objects.filter(related_place=place, moderation_note__startswith=self.EVENT_MARKER).delete()

        now = timezone.now()
        for event_index, event_template in enumerate(self._build_event_templates(place=place, template=template, index=index), start=1):
            start_datetime = now + timedelta(days=event_template.start_in_days, hours=11)
            end_datetime = start_datetime + timedelta(hours=event_template.duration_hours)
            event = Event(
                related_place=place,
                category_id=place.category_id,
                name=event_template.name_ru,
                slug=event_template.slug,
                name_ru=event_template.name_ru,
                name_az=event_template.name_az,
                name_en=event_template.name_en,
                description_ru=event_template.description_ru,
                description_az=event_template.description_az,
                description_en=event_template.description_en,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                age_from=place.age_from,
                age_to=place.age_to,
                price_text=event_template.price_text,
                address=place.address,
                phone=place.phone1,
                instagram=place.instagram,
                moderation_note=f"{self.EVENT_MARKER}:{place.slug}:{event_index}",
                status=Event.STATUS_PUBLISHED,
                published_at=now - timedelta(days=max(1, index // 2)),
            )
            self._sync_instance_file_field(
                instance=event,
                field_name="photo",
                source_relative_path=event_template.photo_path,
                target_name=f"demo-{place.slug}-event-{event_index}{Path(event_template.photo_path).suffix.lower()}",
            )
            event.save()

    def _build_review_templates(self, *, template: DemoPlaceTemplate) -> list[DemoReviewTemplate]:
        if template.rating_avg >= 4.8:
            ratings = (5, 5, 5)
        elif template.rating_avg >= 4.6:
            ratings = (5, 5, 4)
        elif template.rating_avg >= 4.4:
            ratings = (5, 4, 4)
        else:
            ratings = (4, 4, 5)

        return [
            DemoReviewTemplate(
                author_name="Aylin M.",
                rating=ratings[0],
                text=f"{template.name_ru} хорошо организован: ребенку понравились занятия, темп и отношение преподавателя.",
                likes_count=6,
                dislikes_count=0,
                days_ago=18,
            ),
            DemoReviewTemplate(
                author_name="Kamran A.",
                rating=ratings[1],
                text=f"Удобная локация, понятное расписание и нормальная обратная связь. Для теста карточки здесь есть полный набор данных.",
                likes_count=4,
                dislikes_count=1,
                days_ago=11,
            ),
            DemoReviewTemplate(
                author_name="Leyla R.",
                rating=ratings[2],
                text=f"Хороший демо-отзыв для проверки блока комментариев: есть текст, рейтинг и дата публикации по месту {template.name_ru}.",
                likes_count=3,
                dislikes_count=0,
                days_ago=6,
            ),
        ]

    def _build_event_templates(self, *, place: Place, template: DemoPlaceTemplate, index: int) -> list[DemoEventTemplate]:
        price_text = f"{max(template.price_from - 10, 20)} AZN"
        event_name_ru = f"{template.name_ru}: открытый день"
        event_name_az = f"{template.name_az}: açıq gün"
        event_name_en = f"{template.name_en}: Open Day"
        event_description_ru = (
            f"Открытое демо-событие от {template.name_ru}: знакомство с форматом, мини-программа для детей и ответы для родителей."
        )
        event_description_az = (
            f"{template.name_az} tərəfindən açıq demo tədbiri: formatla tanışlıq, uşaqlar üçün mini proqram və valideynlər üçün qısa təqdimat."
        )
        event_description_en = (
            f"An open demo event by {template.name_en} with a short program for children and a parent Q&A session."
        )

        templates = [
            DemoEventTemplate(
                slug=f"{place.slug}-open-day",
                name_ru=event_name_ru,
                name_az=event_name_az,
                name_en=event_name_en,
                description_ru=event_description_ru,
                description_az=event_description_az,
                description_en=event_description_en,
                start_in_days=2 + index,
                duration_hours=8 if template.category == "CAMP" else 2,
                price_text=price_text,
                photo_path=template.cover_photo_path,
            )
        ]

        if template.is_temporary:
            templates.append(
                DemoEventTemplate(
                    slug=f"{place.slug}-family-weekend",
                    name_ru=f"{template.name_ru}: семейный weekend",
                    name_az=f"{template.name_az}: ailə weekend-i",
                    name_en=f"{template.name_en}: Family Weekend",
                    description_ru="Дополнительное временное событие для проверки нескольких анонсов у одной карточки и корректной выдачи на странице событий.",
                    description_az="Bir kart üçün birdən çox elan görünüşünü və tədbir səhifəsini yoxlamaq üçün əlavə müvəqqəti tədbir.",
                    description_en="An extra temporary event to verify multiple announcements tied to the same place.",
                    start_in_days=max(template.temporary_days_from_now or 7, 7),
                    duration_hours=max(template.temporary_duration_hours or 4, 4),
                    price_text=f"{template.price_from} AZN",
                    photo_path=template.photo_path,
                )
            )

        return templates

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[4]

    def _build_templates(self) -> list[DemoPlaceTemplate]:
        return [
            DemoPlaceTemplate(
                slug="baku-boulevard-amusement-park",
                category="PARK",
                subcategory="amusement-parks",
                district="Səbail",
                metro="Sahil",
                age_from=3,
                age_to=16,
                price_from=10,
                price_to=50,
                lat=40.37000,
                lng=49.84200,
                is_verified=True,
                rating_avg=4.8,
                rating_count=150,
                lesson_duration_minutes=120,
                name_ru="Парк аттракционов на Бульваре",
                name_az="Bulvar Attraksion Parkı",
                name_en="Boulevard Amusement Park",
                description_ru="Большой семейный парк аттракционов на Приморском бульваре Баку с колесом обозрения, детскими каруселями и зонами отдыха.",
                description_az="Bakı Dənizkənarı Bulvarında yerləşən, uşaq karuselləri, attraksionlar və böyük panoram çarxı ilə ailəvi istirahət parkı.",
                description_en="A large family amusement park on Baku Seaside Boulevard featuring a ferris wheel, kids carousels, and leisure zones.",
                address="Bakı Dənizkənarı Milli Parkı, Bakı",
                phone="+994 50 321 12 10",
                instagram="bulvar.park.az",
                website="https://example.com/baku-boulevard-amusement-park",
                schedule="Hər gün 10:00-23:00; yay mövsümündə gecə yarısına qədər açıqdır.",
                extra_conditions="Касса работает до 22:30, есть семейные абонементы, отдельные зоны фудкорта и парковка.",
                additional_info="Прекрасный парк для всей семьи с широким выбором развлечений для детей любого возраста.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/family-balloons.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/family-balloons.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="caspian-family-waterpark",
                category="WATERPARK",
                subcategory="waterparks-pools",
                district="Səbail",
                metro="İçərişəhər",
                age_from=3,
                age_to=16,
                price_from=18,
                price_to=45,
                lat=40.32480,
                lng=49.82070,
                is_verified=True,
                rating_avg=4.7,
                rating_count=86,
                lesson_duration_minutes=180,
                name_ru="Caspian Family Waterpark",
                name_az="Caspian Ailə Akvaparkı",
                name_en="Caspian Family Waterpark",
                description_ru="Семейный аквапарк с открытыми бассейнами, водными горками, мелкой зоной для малышей и местами для отдыха родителей.",
                description_az="Açıq hovuzları, su sürüşkənləri, balacalar üçün dayaz zonası və valideynlər üçün istirahət yerləri olan ailəvi akvapark.",
                description_en="A family water park with outdoor pools, water slides, a shallow area for toddlers, and places for parents to relax.",
                address="Bayıl, Bakı",
                phone="+994 50 555 24 24",
                instagram="caspian.family.waterpark",
                website="https://example.com/caspian-family-waterpark",
                schedule="Hər gün 10:00-20:00",
                extra_conditions="Детям до 10 лет — только в сопровождении взрослого. На территории есть раздевалки, шкафчики и кафе.",
                additional_info="Открытый семейный аквапарк для летнего отдыха: горки, бассейны и отдельная безопасная зона для малышей.",
                photo_path="static/img/demo/waterpark-family.png",
                cover_photo_path="static/img/demo/waterpark-family.png",
                gallery_photo_paths=(
                    "static/img/demo/waterpark-family.png",
                ),
            ),
            DemoPlaceTemplate(
                slug="rope-park-shikhov-adventure",
                category="PARK",
                subcategory="rope-parks",
                district="Səbail",
                metro="",
                age_from=6,
                age_to=16,
                price_from=15,
                price_to=35,
                lat=40.30210,
                lng=49.81850,
                is_verified=True,
                rating_avg=4.7,
                rating_count=68,
                lesson_duration_minutes=90,
                name_ru="Веревочный парк Shikhov Adventure",
                name_az="Şıxov Adventure Kanat Parkı",
                name_en="Shikhov Adventure Rope Park",
                description_ru="Экстремальный веревочный парк для детей и подростков на берегу моря с трассами разной сложности и опытными инструкторами.",
                description_az="Dəniz kənarında yerləşən, müxtəlif çətinlik dərəcəli marşrutlar və peşəkar təlimatçılarla uşaqlar üçün kanat parkı.",
                description_en="An exciting rope adventure park for kids and teens near the sea with trails of varying difficulty and certified instructors.",
                address="Şıxov çimərliyi yolu, Bakı",
                phone="+994 50 321 12 20",
                instagram="shikhov.adventure",
                website="https://example.com/rope-park-shikhov-adventure",
                schedule="Ç.a. - Bazar 10:00-20:00; Bazar ertəsi profilaktika günüdür.",
                extra_conditions="Təhlükəsizlik kəməri və kaskalar verilir, 3 fərqli çətinlik səviyyəsi mövcuddur.",
                additional_info="Безопасное развлечение под присмотром инструкторов, отличный способ провести выходной день на свежем воздухе.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/team-hands.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="baku-judo-training-center-prime",
                category="SPRT",
                subcategory="judo",
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
                lesson_duration_minutes=75,
                name_ru="Baku Judo Training Center Prime",
                name_az="Baku Judo Training Center Prime",
                name_en="Baku Judo Training Center Prime",
                description_ru="Сильная детская секция дзюдо рядом с Gənclik: возрастные группы, соревнования, пробная тренировка и понятная адаптация для новичков.",
                description_az="Gənclik yaxınlığında güclü uşaq cüdo mərkəzi: yaş qrupları, yarış hazırlığı, sınaq məşğələsi və yeni başlayanlar üçün rahat adaptasiya.",
                description_en="A strong youth judo center near Ganjlik with age-based groups, competition prep, trial classes, and a clear beginner path.",
                address="Həsən Əliyev küç. 78, Bakı",
                phone="+994 50 321 10 10",
                instagram="bakujudo.prime",
                website="https://example.com/baku-judo-training-center-prime",
                schedule="B.e., Ç.a., C.a. 16:00-19:00; Ş. 11:00 sparrinq və ümumi fiziki hazırlıq.",
                extra_conditions="Valideynlər üçün gözləmə zonası, məşqə giriş səviyyəsi üzrə bölünmə, aylıq irəliləyiş qeydləri və daxili turnirlər mövcuddur.",
                additional_info="Большой светлый зал, отдельная зона разминки, шкафчики, тренерский состав с опытом детских стартов.",
                photo_path="static/img/home/photos/sports-class.jpg",
                cover_photo_path="static/img/home/photos/family-park.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/sports-class.jpg",
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/family-park.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="coderoom-junior-lab",
                category="TECH",
                subcategory="programming",
                district="Nəsimi",
                metro="28 May",
                age_from=8,
                age_to=15,
                price_from=120,
                price_to=185,
                lat=40.37892,
                lng=49.85571,
                is_verified=True,
                rating_avg=4.7,
                rating_count=94,
                lesson_duration_minutes=90,
                name_ru="CodeRoom Junior Lab",
                name_az="CodeRoom Junior Lab",
                name_en="CodeRoom Junior Lab",
                description_ru="Кружок по Scratch, Python и игровому прототипированию в центре Баку: маленькие группы, проектный формат и удобное вечернее расписание.",
                description_az="Bakının mərkəzində Scratch, Python və oyun prototipləşdirməsi üzrə dərnək: kiçik qruplar, layihə əsaslı yanaşma və rahat axşam cədvəli.",
                description_en="A central Baku coding club for Scratch, Python, and game prototyping with small groups and project-based lessons.",
                address="28 May küç. 12, Bakı",
                phone="+994 50 321 10 20",
                instagram="coderoomjuniorlab",
                website="https://example.com/coderoom-junior-lab",
                schedule="Ç.a., C.a., Ş. 17:00-19:15; Şənbə open lab 12:00-14:00.",
                extra_conditions="Noutbuklar mərkəz tərəfindən verilir, aylıq demo günü keçirilir, hər şagirdin mini portfolio-su toplanır.",
                additional_info="Есть вводный тест, отдельные группы для Scratch и Python, удобная посадка для работы за ноутбуками.",
                photo_path="static/img/home/photos/team-hands.jpg",
                cover_photo_path="static/img/home/photos/family-studio.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                    "static/img/home/photos/family-studio.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="mini-art-atelier-iceri",
                category="ART",
                subcategory="drawing-painting",
                district="Səbail",
                metro="Sahil",
                age_from=4,
                age_to=12,
                price_from=80,
                price_to=130,
                lat=40.37014,
                lng=49.83684,
                is_verified=True,
                rating_avg=4.9,
                rating_count=76,
                lesson_duration_minutes=75,
                name_ru="Mini Art Atelier İçəri",
                name_az="Mini Art Atelier İçəri",
                name_en="Mini Art Atelier Icheri",
                description_ru="Творческая студия с рисованием, аппликацией, лепкой и сезонными мастер-классами рядом с бульваром и İçərişəhər.",
                description_az="Rəsm, kollaj, gil işi və mövsümi master-klasslarla yaradıcı studiya, bulvara və İçərişəhərə yaxın yerləşir.",
                description_en="A creative studio for drawing, collage, clay, and seasonal workshops near the boulevard and Icherisheher.",
                address="Neftçilər prospekti 95, Bakı",
                phone="+994 50 321 10 30",
                instagram="miniartatelier.iceri",
                website="https://example.com/mini-art-atelier-iceri",
                schedule="B.e., C.a., C. 15:30-18:30; B. 13:00 ailə workshop-u.",
                extra_conditions="Bütün materiallar daxildir, əsərlər ay sonunda mini sərgidə nümayiş olunur, kiçik yaş qrupları üçün ayrıca masa zonası var.",
                additional_info="Хорошо подходит для первой творческой студии, спокойная атмосфера, много естественного света.",
                photo_path="static/img/home/photos/art-class.jpg",
                cover_photo_path="static/img/home/photos/art-drawing.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/art-class.jpg",
                    "static/img/home/photos/art-drawing.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="piano-house-ganjlik-studio",
                category="MUS",
                subcategory="piano",
                district="Nərimanov",
                metro="Gənclik",
                age_from=6,
                age_to=16,
                price_from=130,
                price_to=220,
                lat=40.39811,
                lng=49.85147,
                is_verified=True,
                rating_avg=4.8,
                rating_count=88,
                lesson_duration_minutes=60,
                name_ru="Piano House Gənclik Studio",
                name_az="Piano House Gənclik Studio",
                name_en="Piano House Ganjlik Studio",
                description_ru="Музыкальная студия с фортепиано, сольфеджио и подготовкой к отчетным концертам для детей разного возраста.",
                description_az="Fortepiano, solfecio və hesabat konsertlərinə hazırlıq təklif edən musiqi studiyası.",
                description_en="A music studio for piano, ear training, and recital preparation across multiple age groups.",
                address="Atatürk prospekti 115, Bakı",
                phone="+994 50 321 10 40",
                instagram="pianohouse.ganjlik",
                website="https://example.com/piano-house-ganjlik-studio",
                schedule="B.e.-C. 15:00-20:00; Ş. fərdi fortepiano və duet dərsləri.",
                extra_conditions="Fərdi və mini qrup dərsləri, aylıq valideyn geribildirimi və səhnə təcrübəsi üçün kiçik salon mövcuddur.",
                additional_info="Есть отдельные кабинеты, удобный вход, камерные отчётные концерты и базовый курс сольфеджио.",
                photo_path="static/img/home/photos/music-lesson.jpg",
                cover_photo_path="static/img/home/photos/family-portrait.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/music-lesson.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                    "static/img/home/photos/family-studio.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="future-skills-academy-hub",
                category="EDU",
                subcategory="language-en",
                district="Yasamal",
                metro="Elmlər Akademiyası",
                age_from=6,
                age_to=15,
                price_from=95,
                price_to=165,
                lat=40.37561,
                lng=49.82275,
                is_verified=True,
                rating_avg=4.6,
                rating_count=102,
                lesson_duration_minutes=80,
                name_ru="Future Skills Academy Hub",
                name_az="Future Skills Academy Hub",
                name_en="Future Skills Academy Hub",
                description_ru="Центр английского, логики и soft skills рядом с Elmlər Akademiyası для детей начальной и средней школы.",
                description_az="Elmlər Akademiyası yaxınlığında ingilis dili, məntiq və soft skills mərkəzi.",
                description_en="A center near Elmlar Akademiyasi for English, logic, and soft skills for school-age children.",
                address="Hüseyn Cavid prospekti 48, Bakı",
                phone="+994 50 321 10 50",
                instagram="futureskills.hub",
                website="https://example.com/future-skills-academy-hub",
                schedule="B.e., Ç.a., C.a., C. 16:00-19:30; Bazar 11:00 speaking club.",
                extra_conditions="Səviyyə testi pulsuzdur, aylıq inkişaf hesabatı təqdim olunur, speaking və reading qrupları ayrıdır.",
                additional_info="Плотное расписание после школы, есть группы по уровню, можно смотреть карточку для типового заполнения education-секции.",
                photo_path="static/img/home/photos/family-studio.jpg",
                cover_photo_path="static/img/home/photos/family-birthday.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-studio.jpg",
                    "static/img/home/photos/family-birthday.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="sea-breeze-kids-club-playhouse",
                category="FUN",
                subcategory="kids-play-centers",
                district="Xətai",
                metro="Ağ Şəhər",
                age_from=3,
                age_to=10,
                price_from=60,
                price_to=110,
                lat=40.36584,
                lng=49.88984,
                is_verified=False,
                rating_avg=4.5,
                rating_count=48,
                lesson_duration_minutes=90,
                name_ru="Sea Breeze Kids Club Playhouse",
                name_az="Sea Breeze Kids Club Playhouse",
                name_en="Sea Breeze Kids Club Playhouse",
                description_ru="Клуб досуга с игровыми зонами, настольными играми, мини-кулинарией и праздничными программами для детей.",
                description_az="Oyun zonaları, masa oyunları, mini-kulinariya və şənlik proqramları olan asudə klub.",
                description_en="A leisure club with play zones, board games, mini cooking classes, and party activities.",
                address="Ağ Şəhər bulvarı 5, Bakı",
                phone="+994 50 321 10 60",
                instagram="seabreezekidsplayhouse",
                website="https://example.com/sea-breeze-kids-club-playhouse",
                schedule="Hər gün 11:00-20:00; həftəsonu tema günləri və family game hour.",
                extra_conditions="Ad günü rezervasiyası, yaşa görə sakit və aktiv zona, müəllim nəzarəti və snack fasiləsi var.",
                additional_info="Подходит для проверки карточки семейного leisure-формата: расписание свободного посещения, описание зон, много фото.",
                photo_path="static/img/home/photos/family-balloons.jpg",
                cover_photo_path="static/img/home/photos/family-birthday.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-balloons.jpg",
                    "static/img/home/photos/family-birthday.jpg",
                    "static/img/home/photos/family-park.jpg",
                ),
                is_temporary=True,
                temporary_days_from_now=9,
                temporary_duration_hours=5,
            ),
            DemoPlaceTemplate(
                slug="city-explorer-day-camp",
                category="CAMP",
                subcategory="city-day-camp",
                district="Binəqədi",
                metro="Nəsimi",
                age_from=7,
                age_to=15,
                price_from=180,
                price_to=320,
                lat=40.42592,
                lng=49.82423,
                is_verified=True,
                rating_avg=4.7,
                rating_count=59,
                lesson_duration_minutes=480,
                name_ru="City Explorer Day Camp",
                name_az="City Explorer Day Camp",
                name_en="City Explorer Day Camp",
                description_ru="Городской дневной лагерь с экскурсиями, спортом, STEM-активностями и насыщенной программой во время каникул.",
                description_az="Ekskursiyalar, idman və STEM fəaliyyətləri ilə şəhər gündüz düşərgəsi.",
                description_en="A city day camp with excursions, sports, and STEM activities during school breaks.",
                address="8-ci mikrorayon, Cəfər Xəndan küç. 21, Bakı",
                phone="+994 50 321 10 70",
                instagram="cityexplorerdaycamp",
                website="https://example.com/city-explorer-day-camp",
                schedule="Yay və qış növbələri 09:00-18:00; erkən qəbul 08:30-dan, transfer seçimi ayrıca.",
                extra_conditions="Nahar daxildir, qruplar yaşa görə bölünür, gündəlik foto hesabat və həftəlik mövzu proqramı təqdim olunur.",
                additional_info="Полезно для проверки длинных описаний и лагерь-специфики: полный день, питание, смены, группы по возрасту.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/team-hands.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/family-balloons.jpg",
                ),
                is_temporary=True,
                temporary_days_from_now=16,
                temporary_duration_hours=8,
            ),
            DemoPlaceTemplate(
                slug="smart-chess-club-pro",
                category="intellect-skills",
                subcategory="chess",
                district="Nəsimi",
                metro="28 May",
                age_from=5,
                age_to=13,
                price_from=75,
                price_to=125,
                lat=40.38161,
                lng=49.84891,
                is_verified=True,
                rating_avg=4.8,
                rating_count=71,
                lesson_duration_minutes=75,
                name_ru="Smart Chess Club Pro",
                name_az="Smart Chess Club Pro",
                name_en="Smart Chess Club Pro",
                description_ru="Шахматный клуб с турнирными группами, логическими разминками и ясной программой для начинающих.",
                description_az="Turnir qrupları, məntiq məşqləri və yeni başlayanlar üçün aydın proqramı olan şahmat klubu.",
                description_en="A chess club with tournament groups, logic warmups, and a clear beginner pathway.",
                address="Səməd Vurğun küç. 34, Bakı",
                phone="+994 50 321 10 80",
                instagram="smartchessclubpro",
                website="https://example.com/smart-chess-club-pro",
                schedule="B.e., Ç.a., C. 16:30-19:00; Ş. turnir məşqi 10:30.",
                extra_conditions="Reytinq qrupu və həvəskar qrupu ayrıdır, aylıq mini-turnirlər və analiz sessiyaları keçirilir.",
                additional_info="Хороший пример карточки интеллектуального кружка: ясное расписание, рейтинг, турниры, сильный текстовый контент.",
                photo_path="static/img/home/photos/team-hands.jpg",
                cover_photo_path="static/img/home/photos/family-studio.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/family-studio.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="rhythm-dance-family-studio-plus",
                category="dance",
                subcategory="modern-choreography",
                district="Yasamal",
                metro="İnşaatçılar",
                age_from=4,
                age_to=12,
                price_from=85,
                price_to=140,
                lat=40.38963,
                lng=49.80119,
                is_verified=False,
                rating_avg=4.4,
                rating_count=37,
                lesson_duration_minutes=60,
                name_ru="Rhythm Dance Family Studio Plus",
                name_az="Rhythm Dance Family Studio Plus",
                name_en="Rhythm Dance Family Studio Plus",
                description_ru="Танцевальная студия с modern kids, ритмикой и открытыми семейными уроками для младших и средних групп.",
                description_az="Modern kids, ritmika və ailə üçün açıq dərslərlə rəqs studiyası.",
                description_en="A dance studio with modern kids, rhythm classes, and open family sessions.",
                address="Mətbuat prospekti 27, Bakı",
                phone="+994 50 321 10 90",
                instagram="rhythmdancefamilystudio",
                website="https://example.com/rhythm-dance-family-studio-plus",
                schedule="Ç.a., C.a., C. 17:00-19:00; Ş. mini səhnə məşqi 12:00.",
                extra_conditions="Mövsüm sonu kiçik səhnə çıxışı, qızlar və qarışıq qruplar, ailə üçün açıq dərslər və video hesabatlar mövcuddur.",
                additional_info="Нужна для проверки dance/visual карточек: яркие фото, семейный контекст, живой leisure-тон текста.",
                photo_path="static/img/home/photos/family-dance.jpg",
                cover_photo_path="static/img/home/photos/family-portrait.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-dance.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                    "static/img/home/photos/family-birthday.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="little-architects-makers-lab",
                category="TECH",
                subcategory="3d-modeling",
                district="Xətai",
                metro="Xətai",
                age_from=8,
                age_to=14,
                price_from=110,
                price_to=175,
                lat=40.38325,
                lng=49.87242,
                is_verified=True,
                rating_avg=4.7,
                rating_count=52,
                lesson_duration_minutes=90,
                name_ru="Little Architects Makers Lab",
                name_az="Little Architects Makers Lab",
                name_en="Little Architects Makers Lab",
                description_ru="Практический STEM-клуб по моделированию, 3D-макетам и городским проектам для детей и подростков.",
                description_az="Model qurma, 3D maket və şəhər layihələri üzrə praktik STEM dərnəyi.",
                description_en="A hands-on STEM club for modeling, 3D builds, and city design projects.",
                address="Xocalı prospekti 37A, Bakı",
                phone="+994 50 321 11 00",
                instagram="littlearchitectsmakerslab",
                website="https://example.com/little-architects-makers-lab",
                schedule="B.e., C.a., C. 17:00-19:15; Ş. böyük layihə sessiyası 13:00.",
                extra_conditions="Materiallar daxildir, kiçik komandalarla işlənir, hər mövsüm sonunda təqdimat günü keçirilir.",
                additional_info="Здесь удобно смотреть, как на сайте выглядят tech/STEM карточки с длинными дополнительными условиями.",
                photo_path="static/img/home/photos/kids-craft.jpg",
                cover_photo_path="static/img/home/photos/art-drawing.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/kids-craft.jpg",
                    "static/img/home/photos/art-drawing.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="vocal-kids-house-stage",
                category="MUS",
                subcategory="vocal",
                district="Səbail",
                metro="İçərişəhər",
                age_from=6,
                age_to=16,
                price_from=120,
                price_to=195,
                lat=40.36685,
                lng=49.83241,
                is_verified=True,
                rating_avg=4.9,
                rating_count=64,
                lesson_duration_minutes=60,
                name_ru="Vocal Kids House Stage",
                name_az="Vocal Kids House Stage",
                name_en="Vocal Kids House Stage",
                description_ru="Студия эстрадного вокала и сценического движения с подготовкой к выступлениям, записям и дуэтным номерам.",
                description_az="Estrada vokalı və səhnə hərəkəti studiyası, çıxış, duet və qeyd hazırlığı ilə.",
                description_en="A vocal and stage movement studio preparing children for performances, recordings, and duet work.",
                address="Kiçik Qala küç. 8, Bakı",
                phone="+994 50 321 11 10",
                instagram="vocalkidshousestage",
                website="https://example.com/vocal-kids-house-stage",
                schedule="B.e.-C. 15:00-19:00; B. duet qrupu 12:30.",
                extra_conditions="Fərdi vokal otaqları və ümumi səhnə məşq zonası var, ayda bir video çəkiliş edilir.",
                additional_info="Хорошая карточка для проверки vocal/theatre контента, нескольких фото и общего визуального качества детальной страницы.",
                photo_path="static/img/home/photos/music-lesson.jpg",
                cover_photo_path="static/img/home/photos/family-portrait.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/music-lesson.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                    "static/img/home/photos/family-dance.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="brush-and-clay-atelier",
                category="ART",
                subcategory="clay-sculpture",
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
                lesson_duration_minutes=75,
                name_ru="Brush and Clay Atelier",
                name_az="Brush and Clay Atelier",
                name_en="Brush and Clay Atelier",
                description_ru="Академия рисунка, керамики и дизайна для детей с тематическими неделями и выставкой работ.",
                description_az="Rəsm, keramika və dizayn dərsləri olan studiya, tematik həftələr və iş sərgisi ilə.",
                description_en="An academy for drawing, ceramics, and design with themed weeks and a student showcase.",
                address="Təbriz küç. 54, Bakı",
                phone="+994 50 321 11 20",
                instagram="brushandclayatelier",
                website="https://example.com/brush-and-clay-atelier",
                schedule="Ç.a., C.a., Ş. 15:00-18:30; B. keramika workshop-u.",
                extra_conditions="Material paketi daxildir, əsərlər qurudulub təqdim olunur, mini sərgi divarı mövcuddur.",
                additional_info="Подходит для проверки gallery/cover/media на художественной карточке: хорошо смотрятся вертикальные и горизонтальные фото.",
                photo_path="static/img/home/photos/art-drawing.jpg",
                cover_photo_path="static/img/home/photos/art-class.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/art-drawing.jpg",
                    "static/img/home/photos/art-class.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="active-kids-gym-park-plus",
                category="SPRT",
                subcategory="kids-fitness",
                district="Binəqədi",
                metro="Azadlıq prospekti",
                age_from=4,
                age_to=11,
                price_from=75,
                price_to=130,
                lat=40.42688,
                lng=49.84171,
                is_verified=False,
                rating_avg=4.5,
                rating_count=34,
                lesson_duration_minutes=60,
                name_ru="Active Kids Gym Park Plus",
                name_az="Active Kids Gym Park Plus",
                name_en="Active Kids Gym Park Plus",
                description_ru="Спортивный центр для ОФП, детского фитнеса, гимнастики и подвижных игр с мягким залом для малышей.",
                description_az="Ümumi fiziki hazırlıq, uşaq fitnesi, gimnastika və hərəkətli oyunlar üçün mərkəz.",
                description_en="A sports center for fitness, kids conditioning, gymnastics, and active play with a soft gym area.",
                address="Azadlıq prospekti 189, Bakı",
                phone="+994 50 321 11 30",
                instagram="activekidsgymparkplus",
                website="https://example.com/active-kids-gym-park-plus",
                schedule="Hər gün 15:00-20:00; səhər məktəbəqədər qrup 10:00.",
                extra_conditions="Yumşaq təhlükəsiz zal, qısa adaptasiya proqramı və valideyn izləmə günləri var.",
                additional_info="Можно использовать для проверки пинов на карте и спортивных карточек с простым, но полным набором данных.",
                photo_path="static/img/home/photos/sports-class.jpg",
                cover_photo_path="static/img/home/photos/family-park.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/sports-class.jpg",
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="english-story-club-riverside",
                category="EDU",
                subcategory="reading-literacy",
                district="Səbail",
                metro="Sahil",
                age_from=5,
                age_to=12,
                price_from=90,
                price_to=140,
                lat=40.37274,
                lng=49.84417,
                is_verified=True,
                rating_avg=4.7,
                rating_count=57,
                lesson_duration_minutes=70,
                name_ru="English Story Club Riverside",
                name_az="English Story Club Riverside",
                name_en="English Story Club Riverside",
                description_ru="Языковой клуб с чтением, театром и разговорными активностями для детей, которым нужен живой английский.",
                description_az="Oxu, teatr və danışıq fəaliyyəti ilə canlı ingilis dili klubu.",
                description_en="A language club combining reading, theater, and speaking activities for practical English.",
                address="Nizami küç. 90, Bakı",
                phone="+994 50 321 11 40",
                instagram="englishstoryclubriverside",
                website="https://example.com/english-story-club-riverside",
                schedule="B.e., Ç.a., C. 16:00-18:15; Ş. speaking theatre 11:30.",
                extra_conditions="Kiçik kitab rəfi, rol oyunları və müəllim tərəfindən aylıq speaking feedback təqdim olunur.",
                additional_info="Хорошая демонстрационная карточка education/reading-клуба с очень понятным текстовым контентом.",
                photo_path="static/img/home/photos/family-studio.jpg",
                cover_photo_path="static/img/home/photos/family-birthday.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-studio.jpg",
                    "static/img/home/photos/family-birthday.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="maker-garage-junior-prototyping",
                category="TECH",
                subcategory="robotics",
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
                lesson_duration_minutes=95,
                name_ru="Maker Garage Junior Prototyping",
                name_az="Maker Garage Junior Prototyping",
                name_en="Maker Garage Junior Prototyping",
                description_ru="Инженерный клуб с Arduino, робототехникой, макетированием и командными прототипами для подростков.",
                description_az="Arduino, robototexnika, maket qurma və komanda prototipləri üzrə yeniyetmələr üçün mühəndislik klubu.",
                description_en="An engineering club for teens focused on Arduino, robotics, prototyping, and team builds.",
                address="Ziya Bünyadov prospekti 1965, Bakı",
                phone="+994 50 321 11 50",
                instagram="makergaragejunior.pro",
                website="https://example.com/maker-garage-junior-prototyping",
                schedule="Ç.a., C.a., Ş. 17:30-20:00; Şənbə open lab 13:00.",
                extra_conditions="Laboratoriya formatı, təhlükəsizlik brifinqi, layihə nümayişi günü və ayrıca robotics starter qrupu var.",
                additional_info="Подходит для проверки длинной tech-карточки: много контента, галерея, точные координаты, насыщенная информационная панель.",
                photo_path="static/img/home/photos/team-hands.jpg",
                cover_photo_path="static/img/home/photos/kids-craft.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                    "static/img/home/photos/family-studio.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="family-stage-musical-lab-live",
                category="MUS",
                subcategory="musical-theater",
                district="Nəsimi",
                metro="Memar Əcəmi",
                age_from=7,
                age_to=15,
                price_from=115,
                price_to=190,
                lat=40.41453,
                lng=49.82845,
                is_verified=True,
                rating_avg=4.7,
                rating_count=41,
                lesson_duration_minutes=80,
                name_ru="Family Stage Musical Lab Live",
                name_az="Family Stage Musical Lab Live",
                name_en="Family Stage Musical Lab Live",
                description_ru="Мюзикл-лаборатория с вокалом, актерским мастерством и пластикой для детей, которым нравится сцена.",
                description_az="Vokal, aktyorluq və plastika ilə səhnəni sevən uşaqlar üçün musical laboratoriyası.",
                description_en="A musical theater lab mixing vocals, acting, and movement for children who enjoy the stage.",
                address="Cavadxan küç. 41, Bakı",
                phone="+994 50 321 11 70",
                instagram="familystagemusicallablive",
                website="https://example.com/family-stage-musical-lab-live",
                schedule="Ç.a., C.a., C. 16:30-19:30; ayda bir açıq məşq və səhnə etüdü.",
                extra_conditions="Qrup etüdləri, səhnə geyimi üzrə məsləhət və açıq məşq günləri keçirilir.",
                additional_info="Нужна для проверки карточек с театральным уклоном и сильной визуальной подачей на детальной странице.",
                photo_path="static/img/home/photos/music-lesson.jpg",
                cover_photo_path="static/img/home/photos/family-dance.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/music-lesson.jpg",
                    "static/img/home/photos/family-dance.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="weekend-adventure-club-festival",
                category="FUN",
                subcategory="master-classes",
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
                lesson_duration_minutes=180,
                name_ru="Weekend Adventure Club Festival",
                name_az="Weekend Adventure Club Festival",
                name_en="Weekend Adventure Club Festival",
                description_ru="Клуб выходного дня с активными играми, мини-квестами, творческими паузами и воскресными семейными программами.",
                description_az="Aktiv oyunlar, mini quest-lər, yaradıcı fasilələr və ailə proqramları ilə həftəsonu klubu.",
                description_en="A weekend club with active games, mini quests, creative breaks, and family sessions.",
                address="Babək prospekti 76, Bakı",
                phone="+994 50 321 11 80",
                instagram="weekendadventurefestival",
                website="https://example.com/weekend-adventure-club-festival",
                schedule="Şənbə-bazar 11:00-18:00; qrup rezervasiyası və açıq hava sessiyası mümkündür.",
                extra_conditions="Hava uyğun olduqda açıq hava hissəsi işləyir, müəllim nəzarəti, snack fasiləsi və mini craft zona var.",
                additional_info="Карточка leisure-формата для проверки family/quest контента и фотографий на карте и в каталоге.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/family-balloons.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/family-balloons.jpg",
                    "static/img/home/photos/family-birthday.jpg",
                ),
                is_temporary=True,
                temporary_days_from_now=12,
                temporary_duration_hours=6,
            ),
            DemoPlaceTemplate(
                slug="city-science-camp-pop-up",
                category="CAMP",
                subcategory="tech-stem-camp",
                district="Nərimanov",
                metro="Nəriman Nərimanov",
                age_from=8,
                age_to=14,
                price_from=200,
                price_to=340,
                lat=40.40481,
                lng=49.86896,
                is_verified=True,
                rating_avg=4.9,
                rating_count=38,
                lesson_duration_minutes=480,
                name_ru="City Science Camp Pop-up",
                name_az="City Science Camp Pop-up",
                name_en="City Science Camp Pop-up",
                description_ru="Каникульный городской STEM-лагерь с наукой, прогулками, проектами и активностями по неделям.",
                description_az="Elm, gəzinti, layihə işi və müxtəlif fəaliyyətlərlə şəhər STEM düşərgəsi.",
                description_en="A city STEM camp with science, walks, projects, and themed weekly activities.",
                address="Təbriz küç. 88, Bakı",
                phone="+994 50 321 12 00",
                instagram="citysciencecamppopup",
                website="https://example.com/city-science-camp-pop-up",
                schedule="Tətil mövsümündə 09:00-18:00; erkən gətirmə 08:30-dan mümkündür.",
                extra_conditions="Qidalanma, ekskursiya günləri, gündəlik valideyn xülasəsi və təhlükəsizlik brifinqi daxildir.",
                additional_info="Хороший временный demo-объект, чтобы проверить бейджи временного размещения, карту и длинные описания на детальной.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/team-hands.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                ),
                is_temporary=True,
                temporary_days_from_now=20,
                temporary_duration_hours=8,
            ),
            DemoPlaceTemplate(
                slug="ganja-sport-school-wrestling",
                category="SPRT",
                subcategory="wrestling",
                district="ganja",
                metro="",
                age_from=6,
                age_to=16,
                price_from=60,
                price_to=100,
                lat=40.6828,
                lng=46.3606,
                is_verified=True,
                rating_avg=4.7,
                rating_count=54,
                lesson_duration_minutes=90,
                name_ru="Gəncə Güləş Məktəbi",
                name_az="Gəncə Güləş Məktəbi",
                name_en="Ganja Wrestling School",
                description_ru="Спортивная школа борьбы в Гяндже с опытными тренерами, соревновательными группами и программой для начинающих детей.",
                description_az="Gəncədə təcrübəli məşqçilər, yarış qrupları və yeni başlayanlar üçün proqramı olan güləş məktəbi.",
                description_en="A wrestling school in Ganja with experienced coaches, competition groups, and a beginner program for children.",
                address="İstiqlaliyyət küç. 12, Gəncə",
                phone="+994 22 265 10 10",
                instagram="ganja.gules.mekteb",
                website="https://example.com/ganja-sport-school-wrestling",
                schedule="B.e., Ç.a., C.a. 15:00-19:00; Ş. 10:00 turnir məşqi.",
                extra_conditions="Yaş qruplarına görə bölünmə, aylıq rayon daxili yarışlar, müəllim nəzarəti mövcuddur.",
                additional_info="Спортивная школа для демонстрации пинов по городу Гянджа на карте.",
                photo_path="static/img/home/photos/sports-class.jpg",
                cover_photo_path="static/img/home/photos/team-hands.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/sports-class.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="gabala-chess-logic-center",
                category="intellect-skills",
                subcategory="chess",
                district="gabala",
                metro="",
                age_from=7,
                age_to=15,
                price_from=50,
                price_to=90,
                lat=40.9961,
                lng=47.8521,
                is_verified=True,
                rating_avg=4.8,
                rating_count=31,
                lesson_duration_minutes=60,
                name_ru="Qəbələ Şahmat Mərkəzi",
                name_az="Qəbələ Şahmat Mərkəzi",
                name_en="Gabala Chess and Logic Center",
                description_ru="Шахматный и логический центр в Габале с турнирными группами и специальной программой для школьников.",
                description_az="Qəbələdə turnir qrupları və şagirdlər üçün xüsusi proqramı olan şahmat və məntiq mərkəzi.",
                description_en="A chess and logic center in Gabala with tournament groups and a program tailored for school-age children.",
                address="M.Ə.Rəsulzadə küç. 5, Qəbələ",
                phone="+994 23 552 10 20",
                instagram="gabala.chess.center",
                website="https://example.com/gabala-chess-logic-center",
                schedule="B.e.-C. 16:00-19:00; Şənbə turnir günü.",
                extra_conditions="Başlanğıc testi pulsuz, aylıq rayon çempionatı keçirilir.",
                additional_info="Центр для демонстрации пина в Гяндже (Gabala) на карте.",
                photo_path="static/img/home/photos/team-hands.jpg",
                cover_photo_path="static/img/home/photos/family-studio.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/family-studio.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="sumgait-art-kids-studio",
                category="ART",
                subcategory="drawing-painting",
                district="sumgait",
                metro="",
                age_from=5,
                age_to=13,
                price_from=55,
                price_to=95,
                lat=40.5897,
                lng=49.6685,
                is_verified=False,
                rating_avg=4.5,
                rating_count=28,
                lesson_duration_minutes=75,
                name_ru="Sumqayıt Uşaq Rəsm Studiyası",
                name_az="Sumqayıt Uşaq Rəsm Studiyası",
                name_en="Sumgait Kids Art Studio",
                description_ru="Детская художественная студия в Сумгаите с рисованием, аппликацией и сезонными мастер-классами для разных возрастов.",
                description_az="Sumqayıtda rəsm, kollaj və mövsümi master-klasslarla uşaq rəsm studiyası.",
                description_en="A children's art studio in Sumgait with drawing, collage, and seasonal workshops for all ages.",
                address="Rəşid Behbudov küç. 27, Sumqayıt",
                phone="+994 18 654 10 30",
                instagram="sumgait.art.kids",
                website="https://example.com/sumgait-art-kids-studio",
                schedule="Ç.a., C.a., C. 15:30-18:30; B. ailə workshop-u.",
                extra_conditions="Bütün materiallar daxildir, ay sonunda mini sərgi keçirilir.",
                additional_info="Карточка для демонстрации пина в Сумгаите на карте.",
                photo_path="static/img/home/photos/art-class.jpg",
                cover_photo_path="static/img/home/photos/art-drawing.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/art-class.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="mingachevir-swimming-school",
                category="SPRT",
                subcategory="swimming",
                district="mingachevir",
                metro="",
                age_from=4,
                age_to=14,
                price_from=70,
                price_to=120,
                lat=40.7704,
                lng=47.0554,
                is_verified=True,
                rating_avg=4.6,
                rating_count=42,
                lesson_duration_minutes=60,
                name_ru="Mingəçevir Üzgüçülük Məktəbi",
                name_az="Mingəçevir Üzgüçülük Məktəbi",
                name_en="Mingachevir Swimming School",
                description_ru="Школа плавания в Мингячевире с отдельными группами для малышей, детей и подростков, опытными тренерами.",
                description_az="Mingəçevirdə körpələr, uşaqlar və yeniyetmələr üçün ayrı qrupları olan üzgüçülük məktəbi.",
                description_en="A swimming school in Mingachevir with separate groups for toddlers, children, and teens.",
                address="Gənclər küç. 8, Mingəçevir",
                phone="+994 22 457 10 40",
                instagram="mingachevir.swim",
                website="https://example.com/mingachevir-swimming-school",
                schedule="Hər gün 09:00-20:00; qrup seçimi yaşa görə.",
                extra_conditions="Sınaq dərsi pulsuz, öyrənmə sürəti fərdi olaraq izlənilir.",
                additional_info="Школа для демонстрации пина в Мингячевире на карте.",
                photo_path="static/img/home/photos/sports-class.jpg",
                cover_photo_path="static/img/home/photos/family-park.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/sports-class.jpg",
                    "static/img/home/photos/family-park.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="sheki-music-culture-center",
                category="MUS",
                subcategory="folk-music",
                district="sheki",
                metro="",
                age_from=6,
                age_to=16,
                price_from=65,
                price_to=110,
                lat=41.1987,
                lng=47.1706,
                is_verified=True,
                rating_avg=4.9,
                rating_count=36,
                lesson_duration_minutes=60,
                name_ru="Şəki Musiqi Mədəniyyət Mərkəzi",
                name_az="Şəki Musiqi Mədəniyyət Mərkəzi",
                name_en="Sheki Music and Culture Center",
                description_ru="Музыкальный и культурный центр в Шеки с традиционной и современной музыкой, концертами и мастер-классами для детей.",
                description_az="Şəkidə ənənəvi və müasir musiqi, konsertlər və uşaqlar üçün master-klasslarla musiqi mədəniyyət mərkəzi.",
                description_en="A music and culture center in Sheki with traditional and modern music, concerts, and workshops for children.",
                address="Əlipaşa Həsənov küç. 3, Şəki",
                phone="+994 25 444 10 50",
                instagram="sheki.music.center",
                website="https://example.com/sheki-music-culture-center",
                schedule="B.e.-C.a. 15:00-19:30; aylıq konsertlər.",
                extra_conditions="Milli alətlər üzrə ayrı qruplar, uşaq xoru, konsert hazırlığı.",
                additional_info="Центр для демонстрации пина в Шеки на карте.",
                photo_path="static/img/home/photos/music-lesson.jpg",
                cover_photo_path="static/img/home/photos/family-portrait.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/music-lesson.jpg",
                    "static/img/home/photos/family-portrait.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="lankaran-eco-kids-camp",
                category="CAMP",
                subcategory="nature-eco-camp",
                district="lankaran",
                metro="",
                age_from=8,
                age_to=15,
                price_from=150,
                price_to=280,
                lat=38.7529,
                lng=48.8516,
                is_verified=True,
                rating_avg=4.8,
                rating_count=29,
                lesson_duration_minutes=480,
                name_ru="Lənkəran Eko Uşaq Düşərgəsi",
                name_az="Lənkəran Eko Uşaq Düşərgəsi",
                name_en="Lankaran Eco Kids Camp",
                description_ru="Экологический детский лагерь в Ленкорани с природными маршрутами, ботаническими экскурсиями и STEM-активностями на свежем воздухе.",
                description_az="Lənkəranda təbiət marşrutları, botanika ekskursiyaları və açıq havada STEM fəaliyyətləri olan eko uşaq düşərgəsi.",
                description_en="An eco children's camp in Lankaran with nature trails, botanical excursions, and outdoor STEM activities.",
                address="Hüseyn Cavid küç. 17, Lənkəran",
                phone="+994 25 552 10 60",
                instagram="lankaran.eco.camp",
                website="https://example.com/lankaran-eco-kids-camp",
                schedule="Yay mövsümü 09:00-18:00; həftəlik tematik marşrutlar.",
                extra_conditions="Nahar daxildir, ekskursiya avtobusu var, botanika dəftərçəsi hər uşağa verilir.",
                additional_info="Лагерь для демонстрации пина в Ленкорани на карте.",
                photo_path="static/img/home/photos/family-park.jpg",
                cover_photo_path="static/img/home/photos/team-hands.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/family-park.jpg",
                    "static/img/home/photos/team-hands.jpg",
                ),
                is_temporary=True,
                temporary_days_from_now=5,
                temporary_duration_hours=8,
            ),
            DemoPlaceTemplate(
                slug="shirvan-coding-junior-hub",
                category="TECH",
                subcategory="programming",
                district="shirvan",
                metro="",
                age_from=9,
                age_to=16,
                price_from=80,
                price_to=140,
                lat=39.9353,
                lng=48.9202,
                is_verified=False,
                rating_avg=4.5,
                rating_count=18,
                lesson_duration_minutes=90,
                name_ru="Şirvan Coding Junior Hub",
                name_az="Şirvan Coding Junior Hub",
                name_en="Shirvan Coding Junior Hub",
                description_ru="Клуб программирования для подростков в Ширване со Scratch, Python и первыми веб-проектами.",
                description_az="Şirvanda Scratch, Python və ilk veb layihələri üzrə yeniyetmələr üçün proqramlaşdırma klubu.",
                description_en="A coding club for teens in Shirvan covering Scratch, Python, and first web projects.",
                address="Nizami küç. 45, Şirvan",
                phone="+994 25 333 10 70",
                instagram="shirvan.coding.junior",
                website="https://example.com/shirvan-coding-junior-hub",
                schedule="Ç.a., C.a., Ş. 16:00-18:30; aylıq demo günü.",
                extra_conditions="Noutbuklar mərkəz tərəfindən verilir, sınaq dərsi pulsuz.",
                additional_info="Клуб для демонстрации пина в Ширване на карте.",
                photo_path="static/img/home/photos/team-hands.jpg",
                cover_photo_path="static/img/home/photos/family-studio.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/team-hands.jpg",
                    "static/img/home/photos/kids-craft.jpg",
                ),
            ),
            DemoPlaceTemplate(
                slug="gakh-nature-kids-workshop",
                category="ART",
                subcategory="clay-sculpture",
                district="gakh",
                metro="",
                age_from=6,
                age_to=14,
                price_from=45,
                price_to=80,
                lat=41.4221,
                lng=46.9319,
                is_verified=False,
                rating_avg=4.6,
                rating_count=14,
                lesson_duration_minutes=75,
                name_ru="Qax Uşaq Yaradıcılıq Atelyesi",
                name_az="Qax Uşaq Yaradıcılıq Atelyesi",
                name_en="Gakh Kids Nature Workshop",
                description_ru="Творческое ателье в Гахе с гончарным делом, природными материалами и сезонными детскими мастер-классами.",
                description_az="Qaxda dulusçuluq, təbii materiallar və mövsümi uşaq master-klassları ilə yaradıcılıq atelyesi.",
                description_en="A creative workshop in Gakh with pottery, natural materials, and seasonal children's workshops.",
                address="Heydər Əliyev küç. 2, Qax",
                phone="+994 25 666 10 80",
                instagram="gakh.kids.workshop",
                website="https://example.com/gakh-nature-kids-workshop",
                schedule="Ç.a., C.a., Ş. 14:00-17:30; B. açıq workshop.",
                extra_conditions="Bütün təbii materiallar daxildir, ailə ilə birlikdə gəlmək mümkündür.",
                additional_info="Мастерская для демонстрации пина в Гахе на карте.",
                photo_path="static/img/home/photos/kids-craft.jpg",
                cover_photo_path="static/img/home/photos/art-class.jpg",
                gallery_photo_paths=(
                    "static/img/home/photos/kids-craft.jpg",
                    "static/img/home/photos/art-drawing.jpg",
                ),
            ),
        ]
