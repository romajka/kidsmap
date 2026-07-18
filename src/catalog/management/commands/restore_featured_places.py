from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from catalog.models import Place


TEMPORARY_PREVIEW_NAMES = (
    "Шахматная студия Preview Baku",
    "Творческая студия Preview Art Lab",
    "Лего-конструирование BrickLab",
)

FEATURED_PLACES = {
    2: {
        "name": "Sonic Athletics Club",
        "name_ru": "Sonic Athletics Club",
        "name_en": "Sonic Athletics Club",
        "name_az": "Sonic Athletics Club",
        "description_ru": (
            "Правильное начало спорта для вашего ребёнка: скорость, выносливость, сила и здоровый образ жизни. "
            "Тренировки проходят в группах по возрасту и уровню подготовки, помогают детям развивать "
            "координацию, дисциплину и любовь к спорту."
        ),
        "description_az": (
            "Uşağınız üçün düzgün idman başlanğıcı: sürət, dözümlülük, güc və sağlam həyat tərzi. "
            "Məşqlər yaşa və hazırlıq səviyyəsinə uyğun qruplarda keçirilir, uşaqlarda koordinasiya, "
            "intizam və idmana maraq yaradır."
        ),
        "description_en": (
            "The right sports start for your child: speed, endurance, strength, and a healthy lifestyle. "
            "Training takes place in groups by age and level, helping children develop coordination, "
            "discipline, and interest in sport."
        ),
    },
    3: {
        "name": "Farid Rzayev ART Studio",
        "name_ru": "Farid Rzayev ART Studio",
        "name_en": "Farid Rzayev ART Studio",
        "name_az": "Farid Rzayev ART Studio",
        "description_ru": (
            "Художественная студия Farid Rzayev ART Studio для детей и взрослых: рисунок, живопись, "
            "композиция и развитие творческого мышления. Занятия подходят для начинающих и тех, кто хочет "
            "улучшить технику и собрать портфолио."
        ),
        "description_az": (
            "Farid Rzayev ART Studio uşaqlar və böyüklər üçün rəsm, boyakarlıq, kompozisiya və yaradıcı "
            "düşüncənin inkişafı üzrə məşğələlər keçirir. Dərslər həm başlayanlar, həm də texnikasını "
            "inkişaf etdirmək istəyənlər üçün uyğundur."
        ),
        "description_en": (
            "Farid Rzayev ART Studio offers drawing, painting, composition, and creative development classes "
            "for children and adults. Lessons suit beginners and students who want to improve technique and "
            "build a portfolio."
        ),
        "schedule": "Расписание уточняйте у студии",
    },
    4: {
        "name": "Bakı Cüdo Təlim Mərkəzi",
        "name_ru": "Бакинский центр обучения дзюдо",
        "name_en": "Baku Judo Training Center",
        "name_az": "Bakı Cüdo Təlim Mərkəzi",
        "description_ru": (
            "Центр обучения дзюдо в Баку для детей и подростков. Тренировки помогают развивать силу, "
            "гибкость, координацию, дисциплину и уверенность. Занятия проходят в спортивном зале "
            "Морского колледжа."
        ),
        "description_az": (
            "Bakıda uşaqlar və yeniyetmələr üçün cüdo təlim mərkəzi. Məşqlər güc, elastiklik, koordinasiya, "
            "intizam və özünəinamı inkişaf etdirməyə kömək edir. Dərslər Dənizçilik kollecinin idman "
            "zalında keçirilir."
        ),
        "description_en": (
            "Baku judo training center for children and teenagers. Training helps develop strength, "
            "flexibility, coordination, discipline, and confidence. Classes take place in the sports hall "
            "of the Maritime College."
        ),
        "schedule": (
            "Bazar ertəsi 17:00-19:00; Çərşənbə axşamı 19:00-21:00; Çərşənbə 17:00-19:00; "
            "Cümə axşamı 19:00-21:00; Cümə 17:00-19:00; Şənbə 10:30-12:30"
        ),
    },
}


class Command(BaseCommand):
    help = "Explicitly restore the original featured clubs. This can override manual hiding."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Show changes without saving them")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Confirm restoring and republishing featured clubs, including manually hidden ones.",
        )

    def handle(self, *args, **options):
        if not options["force"]:
            raise CommandError(
                "Refusing to restore featured clubs without --force because this can republish manually hidden places."
            )

        dry_run = bool(options["dry_run"])
        restored = 0
        missing = []

        temporary_qs = Place.objects.filter(name_ru__in=TEMPORARY_PREVIEW_NAMES)
        temporary_count = temporary_qs.count()
        if temporary_count:
            if dry_run:
                self.stdout.write(f"[dry-run] Would delete {temporary_count} temporary preview record(s).")
            else:
                temporary_qs.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {temporary_count} temporary preview record(s)."))

        for place_id, payload in FEATURED_PLACES.items():
            place = Place.objects.filter(id=place_id).first()
            if place is None:
                missing.append(str(place_id))
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
                    self.stdout.write(f"[dry-run] {place.id}: {place.name} -> {sorted(updates)}")
                else:
                    for field, value in updates.items():
                        setattr(place, field, value)
                    place.save(update_fields=[*sorted(updates), "updated_at"])
                    self.stdout.write(self.style.SUCCESS(f"Restored: {place.id} {place.name}"))
            else:
                self.stdout.write(f"No changes needed: {place.id} {place.name}")

        if missing:
            self.stdout.write(self.style.WARNING("Missing featured club ids: " + ", ".join(missing)))

        if dry_run:
            self.stdout.write(self.style.WARNING(f"Dry run complete. Would touch {restored} record(s)."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Restore complete. Updated {restored} record(s)."))
