from pathlib import Path
import shutil

from django.conf import settings
from django.db import migrations


HOME_HERO_GALLERY_ITEMS = (
    {
        "filename": "family-studio.jpg",
        "category": "",
        "title_ru": "Семья",
        "title_en": "Family",
        "title_az": "Ailə",
    },
    {
        "filename": "kids-craft.jpg",
        "category": "ART",
        "title_ru": "Творчество",
        "title_en": "Creativity",
        "title_az": "Yaradıcılıq",
    },
    {
        "filename": "music-lesson.jpg",
        "category": "MUS",
        "title_ru": "Музыка",
        "title_en": "Music",
        "title_az": "Musiqi",
    },
    {
        "filename": "family-balloons.jpg",
        "category": "FUN",
        "title_ru": "Семейный досуг",
        "title_en": "Family time",
        "title_az": "Ailə istirahəti",
    },
    {
        "filename": "art-class.jpg",
        "category": "ART",
        "title_ru": "Творчество",
        "title_en": "Creativity",
        "title_az": "Yaradıcılıq",
    },
    {
        "filename": "sports-class.jpg",
        "category": "SPRT",
        "title_ru": "Спорт",
        "title_en": "Sport",
        "title_az": "İdman",
    },
    {
        "filename": "family-park.jpg",
        "category": "FUN",
        "title_ru": "Семейный досуг",
        "title_en": "Family time",
        "title_az": "Ailə istirahəti",
    },
    {
        "filename": "art-drawing.jpg",
        "category": "ART",
        "title_ru": "Рисование",
        "title_en": "Drawing",
        "title_az": "Rəsm",
    },
    {
        "filename": "team-hands.jpg",
        "category": "EDU",
        "title_ru": "Командные занятия",
        "title_en": "Team activities",
        "title_az": "Komanda məşğələləri",
    },
)


def seed_home_hero_site_gallery_images(apps, schema_editor):
    site_gallery_image_model = apps.get_model("catalog", "SiteGalleryImage")
    if site_gallery_image_model.objects.filter(placement="HOME_HERO").exists():
        return

    static_gallery_dir = Path(settings.BASE_DIR) / "static" / "img" / "home" / "photos"
    media_gallery_dir = Path(settings.MEDIA_ROOT) / "site" / "gallery"
    media_gallery_dir.mkdir(parents=True, exist_ok=True)

    created_items = []
    for order, item in enumerate(HOME_HERO_GALLERY_ITEMS, start=1):
        source_path = static_gallery_dir / item["filename"]
        if not source_path.exists():
            continue

        destination_name = f"home-hero-{order:02d}-{item['filename']}"
        destination_path = media_gallery_dir / destination_name
        if not destination_path.exists():
            shutil.copy2(source_path, destination_path)

        created_items.append(
            site_gallery_image_model(
                placement="HOME_HERO",
                image=f"site/gallery/{destination_name}",
                category=item["category"],
                title_ru=item["title_ru"],
                title_en=item["title_en"],
                title_az=item["title_az"],
                order=order,
                is_active=True,
            )
        )

    if created_items:
        site_gallery_image_model.objects.bulk_create(created_items)


def unseed_home_hero_site_gallery_images(apps, schema_editor):
    site_gallery_image_model = apps.get_model("catalog", "SiteGalleryImage")
    site_gallery_image_model.objects.filter(
        placement="HOME_HERO",
        image__startswith="site/gallery/home-hero-",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0036_sitegalleryimage"),
    ]

    operations = [
        migrations.RunPython(
            seed_home_hero_site_gallery_images,
            unseed_home_hero_site_gallery_images,
        ),
    ]
