import hashlib
import json
import re
import shutil
from pathlib import Path

root = Path('/mnt/c/kidsmap')
out = root / 'docs/qa/module11-repair-2026-10-18-pc-r1'
assert not (out / 'artifact-manifest.json').exists(), 'Already sealed'
notes = out / 'evidence/observer-and-environment-notes.md'
notes.write_text(notes.read_text() + '''
- The guarded 512-method run had zero functional failures and eight document-worker errors: the isolated child could not see a parent-only dependency target. The same verified pypdf 6.20.1 wheel was then installed in the owned app container's site-packages. The final fresh 514-method run passed with zero failures/errors; its source snapshot includes the expanded public-photo repair.
- The expanded photo repair first encountered a WSL open error before any source write. Exact before hashes were verified, then a native nontruncating FileStream applied the reviewed candidates. After hashes and the complete source snapshot were verified. No foreign process was stopped.
''')
report = out / 'REPORT.md'
text = report.read_text()
replacements = {
    '# Модуль11': '# Модуль 11',
    'Проверены7исходных пунктов:6исправлены, редактор SEO уже был исправлен в модуле10 и перепроверен. Дополнительно устранены2связанные проблемы:': 'Проверены 7 исходных пунктов: 6 исправлены, редактор SEO уже был исправлен в модуле 10 и перепроверен. Дополнительно устранены 2 связанные проблемы:',
    'объёме:0.': 'объёме: 0.',
    '**514уникальных backend-методов,0failures/0errors**': '**514 уникальных тестовых методов, 0 ошибок и падений**',
    '**378строк/2635проверок,2635PASS/0FAIL**': '**378 строк / 2635 проверок, все прошли**',
    'AZ/RU/EN,360/390/768/1024/1280/1440': 'AZ/RU/EN, ширина 360/390/768/1024/1280/1440 px',
    'не2635уникальных': 'не 2635 уникальных',
    'Все42предыдущих пакета/9279files': 'Все 42 предыдущих пакета / 9279 файлов',
    'Модуль12 —': 'Модуль 12 —',
    'модуля12.': 'модуля 12.',
    'модуля11.': 'модуля 11.',
    'Исходные7пунктов и2дополнительных': 'Исходные 7 пунктов и 2 дополнительных',
    ';8исправлены сейчас,1раньше': '; 8 исправлены сейчас, 1 раньше',
}
for before, after in replacements.items():
    text = text.replace(before, after)
text = re.sub(r'(?<=[0-9])(?=[А-Яа-яЁё])|(?<=[А-Яа-яЁё])(?=[0-9])', ' ', text)
report.write_text(text)
shutil.copyfile(Path(__file__), out / 'execution-scripts/m11-seal.py')
for path in out.rglob('*'):
    if not path.is_file() or path.suffix.lower() not in {'.py', '.js', '.json', '.md', '.txt', '.diff', '.html', '.ps1'}:
        continue
    content = path.read_text(errors='replace')
    for tag in re.findall(r'<input\b[^>]*>', content, re.I):
        if re.search(r'name=[\"\']csrfmiddlewaretoken[\"\']', tag, re.I):
            assert not re.search(r'value=[\"\'][A-Za-z0-9]{64}[\"\']', tag), 'Raw CSRF input in artifact'
files = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(out.rglob('*')) if p.is_file()}
(out / 'artifact-manifest.json').write_text(json.dumps(
    {'version': 1, 'algorithm': 'sha256', 'files': files}, indent=2))
print(json.dumps({'sealed_entries': len(files), 'raw_CSRF_input_scan': 'PASS'}))
