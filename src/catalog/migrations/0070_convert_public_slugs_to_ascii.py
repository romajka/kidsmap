from django.db import migrations
from django.utils.text import slugify


TRANSLITERATION = str.maketrans(
    {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
        "ə": "e", "ı": "i", "ö": "o", "ü": "u", "ş": "sh", "ç": "ch", "ğ": "gh",
    }
)


def _ascii_slug(value, fallback):
    return slugify(str(value or "").lower().translate(TRANSLITERATION), allow_unicode=False) or fallback


def _convert_slugs(apps, model_name, fallback):
    Model = apps.get_model("catalog", model_name)
    used = set()
    for item in Model.objects.order_by("pk").iterator():
        base = _ascii_slug(item.slug, fallback)
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{suffix}"
            suffix += 1
        used.add(candidate)
        if item.slug != candidate:
            Model.objects.filter(pk=item.pk).update(slug=candidate)


def convert_public_slugs_to_ascii(apps, schema_editor):
    _convert_slugs(apps, "Place", "place")
    _convert_slugs(apps, "Event", "event")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0069_place_multilingual_extra_fields")]

    operations = [migrations.RunPython(convert_public_slugs_to_ascii, migrations.RunPython.noop)]
