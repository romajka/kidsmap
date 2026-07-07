from __future__ import annotations

import unicodedata

from django.utils.translation import gettext as _
from django.utils.translation import override

from catalog.services.locations import get_location_translation

SUPPORTED_OPTION_LANGUAGES = ("az", "ru", "en")


def _normalize_language(language_code: str | None) -> str:
    normalized = str(language_code or "").strip().split("-")[0]
    return normalized if normalized in SUPPORTED_OPTION_LANGUAGES else "az"


def _translate_for_language(value: str, language_code: str) -> str:
    return get_location_translation(value, language_code)



def _extract_option_payload(raw) -> tuple[str, dict[str, str]]:
    if isinstance(raw, dict):
        labels_block = raw.get("labels") if isinstance(raw.get("labels"), dict) else {}
        labels = {
            lang: str(
                raw.get(f"label_{lang}")
                or raw.get(f"name_{lang}")
                or raw.get(lang)
                or labels_block.get(lang)
                or ""
            ).strip()
            for lang in SUPPORTED_OPTION_LANGUAGES
        }
        value = str(
            raw.get("value")
            or raw.get("code")
            or raw.get("id")
            or raw.get("key")
            or raw.get("slug")
            or raw.get("label_ru")
            or raw.get("name_ru")
            or raw.get("ru")
            or raw.get("label_az")
            or raw.get("name_az")
            or raw.get("az")
            or raw.get("label_en")
            or raw.get("name_en")
            or raw.get("en")
            or raw.get("label")
            or raw.get("name")
            or ""
        ).strip()
        return value, labels

    value = str(raw or "").strip()
    return value, {}


def build_localized_option(raw, language_code: str | None = None) -> dict[str, str]:
    current_language = _normalize_language(language_code)
    value, explicit_labels = _extract_option_payload(raw)
    if not value:
        return {}

    labels: dict[str, str] = {}
    for lang in SUPPORTED_OPTION_LANGUAGES:
        translated = explicit_labels.get(lang) or _translate_for_language(value, lang)
        labels[lang] = str(translated or value).strip() or value

    count = None
    if isinstance(raw, dict) and raw.get("count") is not None:
        try:
            count = int(raw.get("count"))
        except (TypeError, ValueError):
            count = None

    option = {
        "value": value,
        "label": labels[current_language],
        "label_az": labels["az"],
        "label_ru": labels["ru"],
        "label_en": labels["en"],
    }
    if isinstance(raw, dict):
        for k, v in raw.items():
            if k not in option and not k.startswith("label_") and k != "label" and k != "value":
                option[k] = v

    if count is not None:
        option["count"] = count
        option["label_with_count"] = f"{option['label']} — {count}"
        option["label_az_with_count"] = f"{option['label_az']} — {count}"
        option["label_ru_with_count"] = f"{option['label_ru']} — {count}"
        option["label_en_with_count"] = f"{option['label_en']} — {count}"
    return option


def build_localized_options(values, language_code: str | None = None) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    seen: set[str] = set()

    for raw in values or []:
        option = build_localized_option(raw, language_code)
        value = option.get("value", "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        options.append(option)

    return sorted(options, key=lambda item: _sortable_label(item["label"]))


def find_localized_label(options, value: str, language_code: str | None = None) -> str:
    target = str(value or "").strip()
    if not target:
        return ""

    normalized_language = _normalize_language(language_code)
    label_key = f"label_{normalized_language}"
    for option in options or []:
        if str(option.get("value") or "").strip() == target:
            return str(option.get(label_key) or option.get("label") or target).strip()
    return target


def sort_translated_values(values) -> list[str]:
    normalized_values: list[str] = []
    seen: set[str] = set()

    for raw in values or []:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized_values.append(value)

    return sorted(normalized_values, key=lambda item: str(_(item)).casefold())


def sort_choice_tuples(choices) -> list[tuple[str, object]]:
    return sorted(list(choices or ()), key=lambda item: _sortable_label(item[1]))


_SORT_TRANSLIT_MAP = str.maketrans(
    {
        "ə": "e",
        "Ə": "E",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ü": "u",
        "Ü": "U",
        "ş": "s",
        "Ş": "S",
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "а": "a",
        "А": "A",
        "б": "b",
        "Б": "B",
        "в": "v",
        "В": "V",
        "г": "g",
        "Г": "G",
        "д": "d",
        "Д": "D",
        "е": "e",
        "Е": "E",
        "ё": "e",
        "Ё": "E",
        "ж": "zh",
        "Ж": "Zh",
        "з": "z",
        "З": "Z",
        "и": "i",
        "И": "I",
        "й": "i",
        "Й": "I",
        "к": "k",
        "К": "K",
        "л": "l",
        "Л": "L",
        "м": "m",
        "М": "M",
        "н": "n",
        "Н": "N",
        "о": "o",
        "О": "O",
        "п": "p",
        "П": "P",
        "р": "r",
        "Р": "R",
        "с": "s",
        "С": "S",
        "т": "t",
        "Т": "T",
        "у": "u",
        "У": "U",
        "ф": "f",
        "Ф": "F",
        "х": "h",
        "Х": "H",
        "ц": "c",
        "Ц": "C",
        "ч": "ch",
        "Ч": "Ch",
        "ш": "sh",
        "Ш": "Sh",
        "щ": "sh",
        "Щ": "Sh",
        "ы": "y",
        "Ы": "Y",
        "э": "e",
        "Э": "E",
        "ю": "yu",
        "Ю": "Yu",
        "я": "ya",
        "Я": "Ya",
        "ъ": "",
        "Ъ": "",
        "ь": "",
        "Ь": "",
    }
)


def _sortable_label(value) -> str:
    text = str(value or "").translate(_SORT_TRANSLIT_MAP)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()
