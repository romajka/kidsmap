from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.core.management.base import BaseCommand

from catalog.models import Place


@dataclass(frozen=True)
class DemoPlaceTemplate:
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


class Command(BaseCommand):
    help = "Create or refresh demo catalog places for local UI testing and pagination."

    DEMO_MARKER = "seed:catalog-demo"
    DISTRICT_CHOICES = (
        "Yasamal",
        "Nərimanov",
        "Nəsimi",
        "Səbail",
        "Xətai",
        "Binəqədi",
    )
    METRO_CHOICES = (
        "Elmlər Akademiyası",
        "Nəriman Nərimanov",
        "28 May",
        "Gənclik",
        "İnşaatçılar",
        "Sahil",
    )
    CATEGORY_LABELS = {
        "SPRT": {
            "ru": "Спортивная студия",
            "az": "İdman studiyası",
            "en": "Sports Studio",
        },
        "ART": {
            "ru": "Творческая мастерская",
            "az": "Yaradıcılıq emalatxanası",
            "en": "Creative Workshop",
        },
        "MUS": {
            "ru": "Музыкальная академия",
            "az": "Musiqi akademiyası",
            "en": "Music Academy",
        },
        "EDU": {
            "ru": "Образовательный центр",
            "az": "Təhsil mərkəzi",
            "en": "Learning Center",
        },
        "TECH": {
            "ru": "Техно-лаборатория",
            "az": "Texno laboratoriya",
            "en": "Tech Lab",
        },
        "FUN": {
            "ru": "Клуб досуга",
            "az": "Asudə klubu",
            "en": "Leisure Club",
        },
        "CAMP": {
            "ru": "Городской лагерь",
            "az": "Şəhər düşərgəsi",
            "en": "City Camp",
        },
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=30,
            help="How many demo places to seed. Default: 30.",
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

        templates = self._build_templates(count)
        created = 0
        updated = 0

        for index, template in enumerate(templates, start=1):
            slug = f"demo-place-{index:02d}"
            defaults = self._build_place_defaults(index=index, template=template)
            place, is_created = Place.objects.update_or_create(slug=slug, defaults=defaults)
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo catalog places ready. Created: {created}, Updated: {updated}, Total requested: {count}."
            )
        )

    def _build_templates(self, count: int) -> list[DemoPlaceTemplate]:
        categories = [choice[0] for choice in Place.CATEGORY_CHOICES]
        templates: list[DemoPlaceTemplate] = []
        base_lat = Decimal("40.3775")
        base_lng = Decimal("49.8470")

        for idx in range(count):
            district = self.DISTRICT_CHOICES[idx % len(self.DISTRICT_CHOICES)]
            metro = self.METRO_CHOICES[idx % len(self.METRO_CHOICES)]
            category = categories[idx % len(categories)]
            lat = float(base_lat + Decimal(idx % 10) * Decimal("0.006"))
            lng = float(base_lng + Decimal(idx // 10) * Decimal("0.008"))
            templates.append(
                DemoPlaceTemplate(
                    category=category,
                    district=district,
                    metro=metro,
                    age_from=(idx % 5) * 2 + 3,
                    age_to=((idx % 5) * 2 + 3) + 5,
                    price_from=35 + (idx % 6) * 15,
                    price_to=60 + (idx % 6) * 20,
                    lat=lat,
                    lng=lng,
                    is_verified=idx % 3 != 0,
                    rating_avg=round(4.1 + (idx % 4) * 0.2, 1),
                    rating_count=6 + (idx % 8) * 3,
                )
            )
        return templates

    def _build_place_defaults(self, *, index: int, template: DemoPlaceTemplate) -> dict:
        labels = self.CATEGORY_LABELS[template.category]
        lesson_number = (index % 4) + 1
        name_ru = f"{labels['ru']} {index}"
        name_az = f"{labels['az']} {index}"
        name_en = f"{labels['en']} {index}"
        description_ru = (
            f"{name_ru} помогает родителям быстро оценить формат занятий, возрастные группы и условия записи. "
            f"В карточке есть понятное расписание, цены, ориентир по метро {template.metro} и подробное описание программы."
        )
        description_az = (
            f"{name_az} valideynlərə proqramı, yaş qruplarını və qeydiyyat şərtlərini tez müqayisə etməyə kömək edir. "
            f"Kartda {template.metro} metrosuna yaxınlıq, aydın cədvəl, qiymətlər və məşğələ formatı göstərilir."
        )
        description_en = (
            f"{name_en} gives parents a clear overview of age groups, enrollment conditions, and the format of classes. "
            f"The card includes schedule details, price range, and quick location context near {template.metro} metro."
        )
        address = f"Bakı şəhəri, {template.district}, küçə {10 + index}"
        phone_number = f"+99450123{index:04d}"
        return {
            "name": name_ru,
            "name_ru": name_ru,
            "name_az": name_az,
            "name_en": name_en,
            "description_ru": description_ru,
            "description_az": description_az,
            "description_en": description_en,
            "category": template.category,
            "district": template.district,
            "metro": template.metro,
            "address": address,
            "phone1": phone_number,
            "instagram": f"kidsmap.demo.{index}",
            "website": f"https://example.com/demo-place-{index}",
            "schedule": (
                f"Bazar ertəsi, çərşənbə və şənbə 1{lesson_number}:00-1{lesson_number + 1}:20; "
                f"sınaq dərsi üçün öncədən qeydiyyat tələb olunur."
            ),
            "age_from": template.age_from,
            "age_to": template.age_to,
            "price_from": template.price_from,
            "price_to": template.price_to,
            "price_per_lesson": max(template.price_from - 5, 20),
            "price_per_month": template.price_to * 4,
            "lesson_duration_minutes": 60 + (index % 3) * 15,
            "lat": template.lat,
            "lng": template.lng,
            "rating_avg": template.rating_avg,
            "rating_count": template.rating_count,
            "likes_count": 4 + index,
            "is_active": True,
            "is_verified": template.is_verified,
            "status": Place.STATUS_PUBLISHED,
            "additional_info": f"{self.DEMO_MARKER}:{index:02d}",
            "extra_conditions": "İlk ziyarət zamanı administrator yaş qrupu və uyğun proqram barədə qısa məsləhət verir.",
        }
