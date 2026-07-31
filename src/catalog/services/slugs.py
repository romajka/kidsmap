from django.utils.text import slugify

from catalog.services.options import ASCII_TRANSLITERATION_MAP


PUBLIC_SLUG_MAX_LENGTH = 60


def build_ascii_slug(value, *, fallback: str) -> str:
    transliterated = str(value or "").translate(ASCII_TRANSLITERATION_MAP)
    slug = slugify(transliterated, allow_unicode=False)[:PUBLIC_SLUG_MAX_LENGTH].strip("-")
    return slug or fallback


def build_unique_ascii_slug(model, value, *, fallback: str, instance_pk=None) -> str:
    base = build_ascii_slug(value, fallback=fallback)
    candidate = base
    index = 2

    while model.objects.filter(slug=candidate).exclude(pk=instance_pk).exists():
        suffix = f"-{index}"
        candidate = f"{base[:PUBLIC_SLUG_MAX_LENGTH - len(suffix)].rstrip('-')}{suffix}"
        index += 1

    return candidate
