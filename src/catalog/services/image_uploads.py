from __future__ import annotations

from io import BytesIO
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.utils.text import get_valid_filename
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener
except ImportError:  # pragma: no cover - reported clearly when HEIC is uploaded
    register_heif_opener = None
else:
    register_heif_opener()


MAX_IMAGE_SOURCE_BYTES = 15 * 1024 * 1024
MAX_STANDARD_IMAGE_SOURCE_BYTES = 2 * 1024 * 1024
MAX_IMAGE_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_IMAGE_DIMENSION = 2400
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "HEIF"}
HEIF_EXTENSIONS = {".heic", ".heif", ".hif"}


def _safe_output_name(original_name: str) -> str:
    stem = get_valid_filename(Path(original_name or "photo").stem).strip("._-") or "photo"
    return f"{stem[:80]}.jpg"


def _flatten_to_rgb(image: Image.Image) -> Image.Image:
    if image.mode == "RGB":
        return image
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.getchannel("A"))
        return background
    return image.convert("RGB")


def _encode_jpeg(image: Image.Image) -> bytes:
    working = image.copy()
    working.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

    for _resize_attempt in range(4):
        for quality in (90, 82, 74, 65, 55):
            output = BytesIO()
            working.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
                progressive=True,
                exif=b"",
            )
            if output.tell() <= MAX_IMAGE_OUTPUT_BYTES:
                return output.getvalue()
        next_size = (
            max(1, round(working.width * 0.82)),
            max(1, round(working.height * 0.82)),
        )
        working = working.resize(next_size, Image.Resampling.LANCZOS)

    raise ValidationError(
        _("Не удалось уменьшить фотографию до 2 МБ. Выберите изображение меньшего разрешения.")
    )


def normalize_uploaded_image(uploaded_file) -> ContentFile:
    """Decode, orient, validate and normalize an uploaded photo to JPEG."""
    if not uploaded_file:
        return uploaded_file

    original_name = getattr(uploaded_file, "name", "") or "photo"
    source_size = int(getattr(uploaded_file, "size", 0) or 0)
    suffix = Path(original_name).suffix.lower()
    is_heif = suffix in HEIF_EXTENSIONS or (getattr(uploaded_file, "content_type", "") or "").lower() in {
        "image/heic",
        "image/heif",
    }
    if source_size <= 0:
        raise ValidationError(_("Файл «%(name)s» пустой.") % {"name": original_name})
    source_limit = MAX_IMAGE_SOURCE_BYTES if is_heif else MAX_STANDARD_IMAGE_SOURCE_BYTES
    if source_size > source_limit:
        raise ValidationError(
            _("Файл «%(name)s» слишком большой. Обычные изображения — до 2 МБ, HEIC/HEIF — до 15 МБ.")
            % {"name": original_name}
        )
    if is_heif and register_heif_opener is None:
        raise ValidationError(
            _("HEIC/HEIF временно недоступен на сервере. Сообщите об этом администратору.")
        )

    try:
        uploaded_file.seek(0)
        source = uploaded_file.read()
        with Image.open(BytesIO(source)) as probe:
            detected_format = (probe.format or "").upper()
            probe.verify()
        if detected_format not in SUPPORTED_IMAGE_FORMATS:
            raise ValidationError(
                _("Формат файла «%(name)s» не поддерживается. Используйте JPG, PNG, WEBP, HEIC или HEIF.")
                % {"name": original_name}
            )

        with Image.open(BytesIO(source)) as decoded:
            decoded.load()
            oriented = ImageOps.exif_transpose(decoded)
            normalized = _flatten_to_rgb(oriented)
            if normalized.width < 1 or normalized.height < 1:
                raise ValidationError(_("Фотография «%(name)s» имеет некорректный размер.") % {"name": original_name})
            output_bytes = _encode_jpeg(normalized)
    except ValidationError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValidationError(
            _("Фотография «%(name)s» имеет слишком большое разрешение.") % {"name": original_name}
        )
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise ValidationError(
            _("Не удалось прочитать «%(name)s»: файл повреждён или это не поддерживаемое изображение.")
            % {"name": original_name}
        )
    finally:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass

    normalized_file = ContentFile(output_bytes, name=_safe_output_name(original_name))
    normalized_file.content_type = "image/jpeg"
    return normalized_file
