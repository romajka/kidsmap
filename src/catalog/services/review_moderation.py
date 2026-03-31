from __future__ import annotations

import re
from dataclasses import dataclass


_PROFANITY_PATTERNS = (
    re.compile(r"\b(?:бля(?:д|т|ха|ть)?|ху(?:й|е|я|и|ё)[а-яё]*|пизд[а-яё]*|ё?еб[а-яё]*|муд[а-яё]*|залуп[а-яё]*|гандон[а-яё]*|сук[а-яё]*)\b", re.IGNORECASE),
    re.compile(r"\b(?:fuck(?:er|ing)?|shit(?:ty)?|bitch(?:es)?|asshole|motherfucker)\b", re.IGNORECASE),
    re.compile(r"\b(?:sik(?:dir|ik|ən)?|amc[ıi]q|qəhb[əe]|gijd[ıi]llaq)\b", re.IGNORECASE),
)


@dataclass(slots=True)
class ModeratedReviewText:
    author_name: str
    text: str
    contains_profanity: bool


def _mask_match(match: re.Match[str]) -> str:
    value = match.group(0)
    if len(value) <= 2:
        return "*" * len(value)
    return value[0] + ("*" * (len(value) - 2)) + value[-1]


def _sanitize_value(value: str) -> tuple[str, bool]:
    sanitized = value or ""
    contains = False

    for pattern in _PROFANITY_PATTERNS:
        sanitized, count = pattern.subn(_mask_match, sanitized)
        if count:
            contains = True

    return sanitized, contains


def moderate_review_content(*, author_name: str, text: str) -> ModeratedReviewText:
    safe_author, author_flag = _sanitize_value(author_name)
    safe_text, text_flag = _sanitize_value(text)
    return ModeratedReviewText(
        author_name=safe_author,
        text=safe_text,
        contains_profanity=author_flag or text_flag,
    )
