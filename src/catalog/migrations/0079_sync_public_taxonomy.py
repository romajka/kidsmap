from django.db import migrations, models


# Old broad categories that no longer exist as public taxonomy entries.
CATEGORY_MOVES = {
    "BEACH": "water-leisure",
    "WATERPARK": "water-leisure",
    "PARK": "parks-playgrounds",
}

# Preserve existing place assignments by moving every retired subcategory to
# the closest item in the new, smaller public taxonomy.
SUBCATEGORY_MOVES = {
    "parent-and-child": "kindergartens",
    "early-learning": "school-prep",
    "speech-development": "school-prep",
    "kindergarten-prep": "kindergartens",
    "educational-games": "school-prep",
    "mini-kindergarten": "kindergartens",
    "language-other": "other-foreign-languages",
    "mathematics": "school-subjects",
    "reading-literacy": "school-subjects",
    "after-school": "after-school-homework",
    "exam-prep": "exam-preparation",
    "tutoring": "school-subjects",
    "gymnastics-artistic": "artistic-gymnastics",
    "gymnastics-rhythmic": "rhythmic-gymnastics",
    "acrobatics-trampoline": "acrobatics",
    "kids-fitness": "kids-fitness-gpp",
    "table-tennis-badminton": "table-tennis",
    "karate-taekwondo": "karate",
    "boxing-kickboxing": "boxing",
    "wrestling-mma": "freestyle-wrestling",
    "roller-skating": "figure-skating",
    "climbing": "kids-fitness-gpp",
    "equestrian": "kids-fitness-gpp",
    "az-national-dance": "folk-dance",
    "world-national-dance": "folk-dance",
    "modern-choreography": "modern-dance",
    "hip-hop-street": "modern-dance",
    "breakdance": "modern-dance",
    "latin-dance": "modern-dance",
    "preschool-choreography": "kids-choreography",
    "dance-fitness": "modern-dance",
    "piano": "keyboards",
    "guitar": "string-instruments",
    "violin-strings": "string-instruments",
    "drums-percussion": "percussion-instruments",
    "other-instruments": "wind-instruments",
    "choir": "vocal",
    "public-speaking": "stage-speech",
    "musical-theater": "theater-acting",
    "game-dev": "programming",
    "web-design": "programming",
    "artificial-intelligence": "programming",
    "cybersecurity": "programming",
    "engineering-electronics": "robotics",
    "digital-literacy": "programming",
    "arts-crafts": "handicrafts",
    "sewing-fashion": "design-modeling",
    "architecture-design": "design-modeling",
    "photography": "design-modeling",
    "videography-vlogging": "design-modeling",
    "animation-comics": "drawing-painting",
    "culinary-classes": "handicrafts",
    "woodwork-modeling": "design-modeling",
    "calligraphy": "drawing-painting",
    "chess": "chess-checkers",
    "financial-literacy": "logic-puzzles",
    "entrepreneurship": "debates-public-speaking",
    "leadership-teamwork": "debates-public-speaking",
    "debates": "debates-public-speaking",
    "etiquette": "debates-public-speaking",
    "career-guidance": "debates-public-speaking",
    "special-educator": "defectologist",
    "social-skills": "child-psychologist",
    "inclusive-adaptive": "adaptive-physical-education",
    "behavioral-support": "aba-therapy",
    "parents-consultation": "child-psychologist",
    "trampoline-activity-parks": "amusement-parks",
    "museums-science-centers": "science-interactive-museums",
    "master-classes": "handicrafts",
    "birthday-parties": "kids-play-centers",
    "family-cafes-kids-zones": "cafes-kids-zone",
    "excursions-tours": "excursions",
    "nature-outdoor-activities": "outdoor-adventures",
    "kids-theaters-cinema": "theater-acting",
    "waterparks-pools": "waterparks",
    "zoos-aquariums": "zoos",
    "city-day-camp": "day-camps",
    "summer-camp": "residential-camps",
    "winter-camp": "residential-camps",
    "sports-camp": "residential-camps",
    "language-camp": "residential-camps",
    "creative-camp": "residential-camps",
    "tech-stem-camp": "residential-camps",
    "nature-camp": "residential-camps",
    "weekend-program": "day-camps",
    "summer-school": "day-camps",
    "international-camp": "residential-camps",
    "public-parks": "parks-boulevards",
    "rope-parks": "playgrounds",
}


def sync_taxonomy(apps, schema_editor):
    from catalog.taxonomy_data import (
        PUBLIC_CATEGORY_CODES,
        category_seed_rows,
        subcategory_seed_rows,
    )

    Category = apps.get_model("catalog", "Category")
    Subcategory = apps.get_model("catalog", "Subcategory")
    Place = apps.get_model("catalog", "Place")
    Event = apps.get_model("catalog", "Event")
    SiteGalleryImage = apps.get_model("catalog", "SiteGalleryImage")

    for item in category_seed_rows():
        Category.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "name_ru": item["name_ru"],
                "name_az": item["name_az"],
                "name_en": item["name_en"],
                "icon": item["icon"],
                "color_bg": item["color_bg"],
                "color_text": item["color_text"],
                "order": item["order"],
                "is_active": True,
                "deleted_at": None,
                "deleted_by_id": None,
            },
        )

    canonical_subcategory_codes = []
    for item in subcategory_seed_rows():
        category = Category.objects.get(code=item["cat"])
        Subcategory.objects.update_or_create(
            code=item["code"],
            defaults={
                "category_id": category.pk,
                "name": item["ru"],
                "name_ru": item["ru"],
                "name_az": item["az"],
                "name_en": item["en"],
                "order": item["order"],
                "is_active": True,
                "deleted_at": None,
                "deleted_by_id": None,
            },
        )
        canonical_subcategory_codes.append(item["code"])

    # Repoint places before retiring the old subcategory rows.
    for old_code, new_code in SUBCATEGORY_MOVES.items():
        old_subcategory = Subcategory.objects.filter(code=old_code).first()
        new_subcategory = Subcategory.objects.filter(code=new_code).first()
        if old_subcategory and new_subcategory and old_subcategory.pk != new_subcategory.pk:
            Place.objects.filter(subcategory_id=old_subcategory.pk).update(
                subcategory_id=new_subcategory.pk,
                category_id=new_subcategory.category_id,
            )

    # A subcategory is authoritative: this guarantees admin cards, public
    # filters and map pins all expose the same category after the migration.
    for subcategory in Subcategory.objects.filter(
        code__in=canonical_subcategory_codes
    ).iterator():
        Place.objects.filter(subcategory_id=subcategory.pk).exclude(
            category_id=subcategory.category_id
        ).update(category_id=subcategory.category_id)

    for old_code, new_code in CATEGORY_MOVES.items():
        Place.objects.filter(category_id=old_code, subcategory__isnull=True).update(
            category_id=new_code
        )
        Event.objects.filter(category_id=old_code).update(category_id=new_code)
        SiteGalleryImage.objects.filter(category=old_code).update(category=new_code)

    Subcategory.objects.exclude(code__in=canonical_subcategory_codes).update(
        is_active=False
    )
    Category.objects.exclude(code__in=PUBLIC_CATEGORY_CODES).update(is_active=False)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0078_place_created_by"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ("order", "name_ru"),
                "verbose_name": "Категория",
                "verbose_name_plural": "Категории",
            },
        ),
        migrations.AlterModelOptions(
            name="subcategory",
            options={
                "ordering": ("category__order", "order", "name_ru"),
                "verbose_name": "Подкатегория",
                "verbose_name_plural": "Подкатегории",
            },
        ),
        migrations.AlterField(
            model_name="sitegalleryimage",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SPRT", "Спорт"),
                    ("water-leisure", "Водный отдых"),
                    ("parks-playgrounds", "Парки и детские площадки"),
                    ("FUN", "Развлечения и досуг"),
                    ("ZOO", "Зоопарки и аквариумы"),
                    ("museums-culture", "Музеи и культура"),
                    ("dance", "Танцульки"),
                    ("EDU", "Образование"),
                    ("early-development", "Дошкольное развитие"),
                    ("ART", "Творчество"),
                    ("theater-stage", "Театр и сцена"),
                    ("MUS", "Музыка"),
                    ("intellect-skills", "Интеллект и навыки"),
                    ("TECH", "Наука и технологии"),
                    ("development-support", "Развитие и поддержка"),
                    ("CAMP", "Лагеря"),
                    ("excursions-tours", "Экскурсии и туры"),
                ],
                default="",
                help_text="Нужно для подписи фото в hero или будущих подборок.",
                max_length=50,
                verbose_name="Категория",
            ),
        ),
        migrations.RunPython(sync_taxonomy, migrations.RunPython.noop),
    ]
