"""Inspect selected public locale entries; no compilation, DB or Django setup."""
import ast
import gettext
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
KEYS = [
    "Статистика", "Активные пользователи", "Сессии", "Просмотры страниц",
    "GA4, последние 30 дней", "Обзор Google Analytics 4", "Выбор периода",
    "Обновлено сегодня", "Посещаемость", "Уникальные", "Просмотры",
    "Топ событий за последние 30 дней", "Топ страниц за последние 30 дней",
    "События GA4", "Популярные страницы GA4",
]
po_path = ROOT / "locale/az/LC_MESSAGES/django.po"
mo_path = ROOT / "locale/az/LC_MESSAGES/django.mo"
po_bytes = po_path.read_bytes()
mo_bytes = mo_path.read_bytes()
entries = {}
lines = po_bytes.decode("utf-8-sig").splitlines()
offset = 0
for block in re.split(r"\n\s*\n", po_bytes.decode("utf-8-sig")):
    data = {"msgid": "", "msgstr": ""}
    field = None
    for line in block.splitlines():
        if line.startswith("msgid ") or line.startswith("msgstr "):
            field, value = line.split(" ", 1)
            data[field] = ast.literal_eval(value)
        elif line.startswith('"') and field in data:
            data[field] += ast.literal_eval(line)
    key = data["msgid"]
    if key in KEYS:
        data["fuzzy"] = any(line.startswith("#,") and "fuzzy" in line for line in block.splitlines())
        data["references"] = [line[3:] for line in block.splitlines() if line.startswith("#: ")]
        data["po_line"] = next((index + 1 for index, line in enumerate(lines) if line == "msgid " + json.dumps(key, ensure_ascii=False)), None)
        entries[key] = data
with mo_path.open("rb") as handle:
    compiled = gettext.GNUTranslations(handle)
head_po = subprocess.check_output(["git", "show", "HEAD:locale/az/LC_MESSAGES/django.po"], cwd=ROOT).decode("utf-8-sig")
head_entries = {}
for block in re.split(r"\n\s*\n", head_po):
    head_data = {"msgid": "", "msgstr": ""}
    field = None
    for line in block.splitlines():
        if line.startswith("msgid ") or line.startswith("msgstr "):
            field, value = line.split(" ", 1)
            head_data[field] = ast.literal_eval(value)
        elif line.startswith('"') and field in head_data:
            head_data[field] += ast.literal_eval(line)
    if head_data["msgid"] in KEYS:
        head_data["fuzzy"] = any(line.startswith("#,") and "fuzzy" in line for line in block.splitlines())
        head_entries[head_data["msgid"]] = head_data
rows = []
for key in KEYS:
    row = dict(entries.get(key, {"msgid": key, "msgstr": None, "fuzzy": None, "po_line": None}))
    row["mo_contains_key"] = key in compiled._catalog
    row["mo_gettext"] = compiled.gettext(key)
    row["mo_returns_msgid"] = row["mo_gettext"] == key
    row["head_po"] = head_entries.get(key)
    row["selected_po_content_matches_head"] = row["head_po"] == {field: row.get(field) for field in ("msgid", "msgstr", "fuzzy")}
    rows.append(row)
evidence = {
    "mode": "AUDIT ONLY / raw PO and runtime compiled GNU MO lookup, no compilation",
    "po_sha256": hashlib.sha256(po_bytes).hexdigest(),
    "mo_sha256": hashlib.sha256(mo_bytes).hexdigest(),
    "po_path": po_path.relative_to(ROOT).as_posix(),
    "mo_path": mo_path.relative_to(ROOT).as_posix(),
    "entries": rows,
}
(OUT / "locale-checks.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
assert mo_path.read_bytes() == mo_bytes
print(json.dumps({"entries": len(rows), "fuzzy": sum(bool(row["fuzzy"]) for row in rows), "missing_mo": sum(not row["mo_contains_key"] for row in rows), "head_heading_translation": compiled.gettext("Статистика"), "compiled_unchanged": True, "selected_po_matching_head": sum(row["selected_po_content_matches_head"] for row in rows)}, ensure_ascii=False))
for row in rows:
    print(json.dumps({"key": row["msgid"], "line": row["po_line"], "fuzzy": row["fuzzy"], "mo_present": row["mo_contains_key"], "po": row["msgstr"], "mo": row["mo_gettext"]}, ensure_ascii=False))
