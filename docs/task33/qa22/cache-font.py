"""Reuse the existing public font cache; no network request in stage22 setup."""
import pathlib
root = pathlib.Path('/root/task33-browser-tools')
assert (root/'material.ttf').is_file()
(root/'material22.css').write_text((root/'material.css').read_text())
