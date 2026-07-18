#!/usr/bin/env python3
"""Fail when tracked text files contain invalid UTF-8 or common mojibake."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


TEXT_SUFFIXES = {
    ".cfg", ".css", ".csv", ".html", ".ini", ".js", ".json", ".md",
    ".po", ".pot", ".py", ".rst", ".toml", ".txt", ".xml", ".yaml", ".yml",
}

# Stable fragments produced by decoding UTF-8 as Windows-1251 or Latin-1,
# plus known legacy Windows-1251 text decoded as Latin-1.
SUSPICIOUS = (
    "\u0420\u045f", "\u0420\u040e\u0420", "\u0420\u00b0\u0420",
    "\u0420\u00b5\u0420", "\u0420\u0451\u0420", "\u0420\u0455\u0420",
    "\u0420\u045c\u0420", "\u0420\u0491\u0420", "\u0420\u00bb\u0420",
    "\u0420\u0454\u0420", "\u0420\u0458\u0420", "\u0420\u0406\u0420",
    "\u0421\u0453", "\u0421\u201a", "\u0421\u040f", "\u0421\u045a",
    "\u0421\u2039", "\u0421\u2021", "\u0421\u20ac", "\u0421\u2030",
    "\u0419\u2122", "\u0419\u045f", "\u0413\u0458", "\u0413\u00b6",
    "\u0413\u00a7", "\u0432\u0402", "\u0432\u201e", "\u0432\u045a",
    "\u0432\u0459", "\u00c3", "\u00c2", "\u00d0", "\u00d1",
    "\u00c1\u00e0\u00ea\u00f3", "\ufffd",
)


def tracked_text_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "-z"], stderr=subprocess.DEVNULL
    )
    return [
        Path(name.decode("utf-8"))
        for name in output.split(b"\0")
        if name and Path(name.decode("utf-8")).suffix.lower() in TEXT_SUFFIXES
    ]


def main() -> int:
    problems: list[str] = []
    for path in tracked_text_files():
        # ``git ls-files`` keeps paths staged or marked for deletion until the
        # next commit.  Repository cleanup must not make the scanner crash.
        if not path.is_file():
            continue
        raw = path.read_bytes()
        if b"\0" in raw:
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            problems.append(f"{path}: invalid UTF-8 ({error})")
            continue
        for number, line in enumerate(text.splitlines(), 1):
            found = sorted({marker for marker in SUSPICIOUS if marker in line})
            if found:
                problems.append(f"{path}:{number}: {', '.join(repr(x) for x in found)}")

    if problems:
        print("Possible mojibake found:", *problems, sep="\n", file=sys.stderr)
        return 1
    print("Mojibake check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
