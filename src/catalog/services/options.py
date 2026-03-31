from __future__ import annotations

from django.utils.translation import gettext as _


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
    return sorted(list(choices or ()), key=lambda item: str(item[1]).casefold())
