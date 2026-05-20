from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone

from catalog.models import Place


FEATURED_PLACES = {
    "Шахматная студия Preview Baku": {
        "description_ru": (
            "Шахматные занятия для детей в Баку: основы, тактика, турниры и тренировка внимания. "
            "Подходит для начинающих и для тех, кто уже играет в клубе или дома."
        ),
        "description_az": (
            "Bakıda uşaqlar üçün şahmat məşğələləri: əsaslar, taktika, turnirlər və diqqət məşqi. "
            "Başlayanlar və artıq oynayan uşaqlar üçün uyğundur."
        ),
        "description_en": (
            "Chess classes for children in Baku: fundamentals, tactics, tournaments, and focus training. "
            "Suitable for beginners and for kids who already play at home or in a club."
        ),
    },
    "Творческая студия Preview Art Lab": {
        "description_ru": (
            "Студия творчества для детей: рисование, композиция, работа с цветом и развитие воображения. "
            "Занятия помогают детям пробовать разные техники и собирать первые портфолио-работы."
        ),
        "description_az": (
            "Uşaqlar üçün yaradıcılıq studiyası: rəsm, kompozisiya, rənglə iş və təxəyyülün inkişafı. "
            "Dərslər uşaqlara fərqli texnikaları sınamağa və ilk işlərini toplamağa kömək edir."
        ),
        "description_en": (
            "Creative studio for children: drawing, composition, color work, and imagination development. "
            "Classes help kids try different techniques and build their first portfolio pieces."
        ),
    },
    "Лего-конструирование BrickLab": {
        "description_ru": (
            "Конструирование и развитие логики для детей 5-11 лет. Занятия помогают собирать модели, "
            "пробовать инженерные решения и развивать пространственное мышление. Есть группы для начинающих "
            "и для детей, которые уже собирают более сложные проекты."
        ),
        "description_az": (
            "5-11 yaşlı uşaqlar üçün lego quruculuğu və məntiq inkişafı. Dərslər modellər yığmağı, "
            "mühəndis yanaşmalarını sınamağı və məkan təfəkkürünü gücləndirməyi öyrədir. Başlayanlar "
            "və daha çətin layihələrə hazır olan uşaqlar üçün qruplar var."
        ),
        "description_en": (
            "Lego building and logic development for children aged 5-11. Classes help kids assemble models, "
            "explore simple engineering ideas, and strengthen spatial thinking. There are groups for beginners "
            "and for children ready for more advanced projects."
        ),
    },
}


class Command(BaseCommand):
    help = "Restore the three featured public clubs and make them pass the public filter."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show changes without saving them")

    def handle(self, *args, **options):
        dry_run = bool(options["dry_run"])
        restored = 0
        missing = []

        for name_ru, payload in FEATURED_PLACES.items():
            place = Place.objects.filter(name_ru=name_ru).first()
            if place is None:
                missing.append(name_ru)
                continue

            updates = {}
            for field, value in payload.items():
                current_value = getattr(place, field)
                if (current_value or "").strip() != value.strip():
                    updates[field] = value

            if place.status != Place.STATUS_PUBLISHED:
                updates["status"] = Place.STATUS_PUBLISHED
            if not place.is_active:
                updates["is_active"] = True
            if place.published_at is None:
                updates["published_at"] = timezone.now()
            if place.rejection_reason:
                updates["rejection_reason"] = ""

            if updates:
                restored += 1
                if dry_run:
                    self.stdout.write(f"[dry-run] {place.id}: {place.name_ru} -> {sorted(updates)}")
                else:
                    for field, value in updates.items():
                        setattr(place, field, value)
                    place.save(update_fields=[*sorted(updates), "updated_at"])
                    self.stdout.write(self.style.SUCCESS(f"Restored: {place.id} {place.name_ru}"))
            else:
                self.stdout.write(f"No changes needed: {place.id} {place.name_ru}")

        if missing:
            self.stdout.write(self.style.WARNING("Missing featured clubs: " + ", ".join(missing)))

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Would touch {restored} record(s)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Restore complete. Updated {restored} record(s)."))
