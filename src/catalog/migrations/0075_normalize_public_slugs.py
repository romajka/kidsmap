from django.db import migrations
from django.utils.text import slugify


TRANSLITERATION_MAP = str.maketrans(
    {
        "ə": "e", "Ə": "E", "ı": "i", "İ": "I", "ö": "o", "Ö": "O",
        "ü": "u", "Ü": "U", "ş": "s", "Ş": "S", "ç": "c", "Ç": "C",
        "ğ": "g", "Ğ": "G", "а": "a", "А": "A", "б": "b", "Б": "B",
        "в": "v", "В": "V", "г": "g", "Г": "G", "д": "d", "Д": "D",
        "е": "e", "Е": "E", "ё": "e", "Ё": "E", "ж": "zh", "Ж": "Zh",
        "з": "z", "З": "Z", "и": "i", "И": "I", "й": "i", "Й": "I",
        "к": "k", "К": "K", "л": "l", "Л": "L", "м": "m", "М": "M",
        "н": "n", "Н": "N", "о": "o", "О": "O", "п": "p", "П": "P",
        "р": "r", "Р": "R", "с": "s", "С": "S", "т": "t", "Т": "T",
        "у": "u", "У": "U", "ф": "f", "Ф": "F", "х": "h", "Х": "H",
        "ц": "c", "Ц": "C", "ч": "ch", "Ч": "Ch", "ш": "sh", "Ш": "Sh",
        "щ": "sh", "Щ": "Sh", "ы": "y", "Ы": "Y", "э": "e", "Э": "E",
        "ю": "yu", "Ю": "Yu", "я": "ya", "Я": "Ya", "ъ": "", "Ъ": "",
        "ь": "", "Ь": "",
    }
)
MAX_LENGTH = 60


def make_slug(value, fallback):
    transliterated = str(value or "").translate(TRANSLITERATION_MAP)
    return slugify(transliterated, allow_unicode=False)[:MAX_LENGTH].strip("-") or fallback


def normalize_model_slugs(model, source_fields, fallback):
    used = {
        slug
        for slug in model.objects.values_list("slug", flat=True)
        if slug and slug.isascii() and len(slug) <= MAX_LENGTH
    }
    for obj in model.objects.order_by("pk").iterator():
        if obj.slug in used:
            continue

        source = next((getattr(obj, field, "") for field in source_fields if getattr(obj, field, "")), fallback)
        base = make_slug(source, fallback)
        candidate = base
        index = 2
        while candidate in used:
            suffix = f"-{index}"
            candidate = f"{base[:MAX_LENGTH - len(suffix)].rstrip('-')}{suffix}"
            index += 1
        used.add(candidate)
        if obj.slug != candidate:
            obj.slug = candidate
            obj.save(update_fields=["slug"])


def normalize_public_slugs(apps, schema_editor):
    Place = apps.get_model("catalog", "Place")
    Event = apps.get_model("catalog", "Event")
    normalize_model_slugs(Place, ("name_az", "name_en", "name_ru", "name"), "place")
    normalize_model_slugs(Event, ("name_az", "name_ru", "name_en", "name"), "event")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0074_ensure_absheron_region"),
    ]

    operations = [
        migrations.RunPython(normalize_public_slugs, migrations.RunPython.noop),
    ]
