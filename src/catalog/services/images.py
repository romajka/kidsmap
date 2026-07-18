from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _


ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_PIXELS = 24_000_000
MAX_IMAGE_BYTES = 2 * 1024 * 1024
IMAGE_VARIANT_VERSION = "v1"
_KNOWN_VARIANTS: set[tuple[int, str]] = set()


@dataclass(frozen=True)
class ImageVariant:
    name: str
    width: int
    height: int
    crop: bool = True
    quality: int = 80


IMAGE_PROFILES: dict[str, tuple[ImageVariant, ...]] = {
    "listing": (
        ImageVariant("thumb-160", 160, 160, quality=76),
        ImageVariant("card-480", 480, 480, quality=78),
        ImageVariant("card-960", 960, 960, quality=80),
        ImageVariant("detail-1600", 1600, 1600, crop=False, quality=82),
    ),
    "profile": (
        ImageVariant("avatar-320", 320, 320, quality=78),
        ImageVariant("avatar-640", 640, 640, quality=80),
    ),
    "hero": (
        ImageVariant("hero-mobile", 760, 560, quality=78),
        ImageVariant("hero-desktop", 1600, 500, quality=82),
    ),
    "background": (
        ImageVariant("background-960", 960, 960, crop=False, quality=78),
        ImageVariant("background-1920", 1920, 1080, crop=False, quality=82),
    ),
    "hero_gallery": (
        ImageVariant("gallery-640", 640, 640, quality=78),
        ImageVariant("gallery-1200", 1200, 1200, crop=False, quality=82),
    ),
    "illustration": (
        ImageVariant("illustration-600", 600, 400, crop=False, quality=80),
        ImageVariant("illustration-1200", 1200, 800, crop=False, quality=82),
    ),
}


def validate_uploaded_image(file_obj) -> None:
    """Validate actual raster contents instead of trusting filename/MIME type."""
    if not file_obj:
        return
    # Existing FieldFile values were validated when uploaded. Reopening every
    # legacy image on unrelated form saves would add I/O and break remote storage.
    if not isinstance(file_obj, UploadedFile):
        return

    extension = Path(getattr(file_obj, "name", "")).suffix.lower()
    if extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValidationError(_("Поддерживаются только файлы JPG, PNG и WebP."))

    if getattr(file_obj, "size", 0) > MAX_IMAGE_BYTES:
        raise ValidationError(_("Размер изображения не должен превышать 2 МБ."))

    position = None
    try:
        position = file_obj.tell()
    except (AttributeError, OSError):
        pass

    try:
        from PIL import Image, UnidentifiedImageError

        image = Image.open(file_obj)
        image_format = (image.format or "").upper()
        width, height = image.size
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(_("Поддерживаются только изображения JPEG, PNG и WebP."))
        if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
            raise ValidationError(_("Разрешение изображения не должно превышать 24 мегапикселя."))
        if getattr(image, "is_animated", False):
            raise ValidationError(_("Анимированные изображения не поддерживаются."))
        image.verify()
    except ValidationError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise ValidationError(_("Файл повреждён или не является изображением.")) from exc
    finally:
        try:
            file_obj.seek(0 if position is None else position)
        except (AttributeError, OSError):
            pass


def variant_name(original_name: str, variant: str) -> str:
    path = Path(original_name)
    return str(path.with_name(f"{path.stem}__{IMAGE_VARIANT_VERSION}__{variant}.webp")).replace("\\", "/")


def image_variant_url(file_field, variant: str, *, fallback: bool = True) -> str:
    if not file_field or not getattr(file_field, "name", ""):
        return ""
    storage = file_field.storage
    candidate = variant_name(file_field.name, variant)
    cache_key = (id(storage), candidate)
    if cache_key in _KNOWN_VARIANTS:
        return storage.url(candidate)
    try:
        if storage.exists(candidate):
            _KNOWN_VARIANTS.add(cache_key)
            return storage.url(candidate)
    except OSError:
        pass
    return file_field.url if fallback else ""


def generate_image_variants(file_field, profile: str, *, force: bool = False) -> list[str]:
    """Generate deterministic WebP derivatives. Invalid legacy files are skipped."""
    variants = IMAGE_PROFILES.get(profile, ())
    if not variants or not file_field or not getattr(file_field, "name", ""):
        return []

    target_names = [variant_name(file_field.name, item.name) for item in variants]
    if not force:
        try:
            if all(file_field.storage.exists(name) for name in target_names):
                return []
        except OSError:
            pass

    try:
        from PIL import Image, ImageOps

        with file_field.storage.open(file_field.name, "rb") as source:
            image = Image.open(source)
            image.load()
        if (image.format or "").upper() not in ALLOWED_IMAGE_FORMATS or getattr(image, "is_animated", False):
            return []
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
    except (OSError, ValueError, SyntaxError):
        return []

    saved: list[str] = []
    for variant in variants:
        if variant.crop:
            rendered = ImageOps.fit(
                image,
                (variant.width, variant.height),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
        else:
            rendered = image.copy()
            rendered.thumbnail((variant.width, variant.height), Image.Resampling.LANCZOS)

        output = BytesIO()
        rendered.save(output, format="WEBP", quality=variant.quality, method=4, optimize=True)
        target_name = variant_name(file_field.name, variant.name)
        try:
            if not force and file_field.storage.exists(target_name):
                continue
            if force and file_field.storage.exists(target_name):
                file_field.storage.delete(target_name)
            file_field.storage.save(target_name, ContentFile(output.getvalue()))
            _KNOWN_VARIANTS.add((id(file_field.storage), target_name))
            saved.append(target_name)
        except OSError:
            continue
    return saved


def delete_image_and_variants(file_field, profile: str, *, delete_original: bool = True) -> None:
    if not file_field or not getattr(file_field, "name", ""):
        return
    storage = file_field.storage
    names = [variant_name(file_field.name, item.name) for item in IMAGE_PROFILES.get(profile, ())]
    if delete_original:
        names.append(file_field.name)
    for name in names:
        try:
            if storage.exists(name):
                storage.delete(name)
            _KNOWN_VARIANTS.discard((id(storage), name))
        except OSError:
            continue
