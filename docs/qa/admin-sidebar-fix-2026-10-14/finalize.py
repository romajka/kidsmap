"""Verify recorded browser results and produce a bounded handoff."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def result(name):
    text = (HERE / name).read_text()
    assert text.startswith("### Result\n"), text[:300]
    return json.JSONDecoder().raw_decode(text.split("\n", 1)[1])[0]

before = result("before.txt")
after = result("after.txt")
assert before["failures"], "Baseline did not reproduce the bug"
assert after["checked"] == after["passed"] and not after["failures"], after["failures"]
assert not after["errors"] and not after["network"], after
source = json.loads((HERE / "source-hashes.json").read_text())
assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == digest for p, digest in source.items())
for name, data in [("baseline.json", before), ("result.json", after)]:
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
manifest = [{"file": p.name, "bytes": p.stat().st_size,
             "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(HERE.glob("*.png"))]
(HERE / "screenshots.json").write_text(json.dumps(manifest, indent=2) + "\n")
(HERE / "REPORT.md").write_text(f"""# Исправление бокового меню админки — 2026-10-14

LOCAL WORKTREE на `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`.
Scope прямо разрешён пользователем: исправить наложение элементов burger/sidebar.
Production не проверялся и не изменялся; commit/push/deploy не выполнялись.

Причина: наши стили запрещали расширение панели при hover/focus, а AdminLTE
продолжал раскрывать подписи и расширять ссылки/логотип. Кроме того, custom
sidebar работал от 768px, тогда как vendor drawer переключался на 992px:
панель уезжала влево, страница заходила под неё, включалась блокирующая подложка.

Изменены только 6 файлов оболочки меню: глобальный layout, stylesheet imports,
стили custom sidebar и оба base template плюс base_site. Панель и отступы
страницы используют общие tokens; убран дублирующий inline layout. Свёрнутый
режим показывает иконки, сохраняет их названия/подсказки и не раскрывается при
наведении. Планшетная панель оставляет страницу доступной; мобильная подложка
закрывает drawer. Логотип помещается в панели. Версии CSS обновлены.

Проверка: настоящий Chromium через Playwright CLI, оба фактических base template,
установленные Jazzmin/AdminLTE CSS/JS и настоящий `data-widget=pushmenu`.
Подписи фикстуры RU/AZ/EN; ширины 375, 390, 768, 900, 991, 992, 1024, 1280,
1440px. Проверены положение панели/страницы, hover/focus, Enter, burger hit-test,
имена ссылок, логотип, доступность кнопки страницы, мобильная подложка и overflow.

- Исходная проверка: {before['passed']}/{before['checked']}, {len(before['failures'])} воспроизведённых FAIL.
- Финальная проверка: **{after['passed']}/{after['checked']} PASS**, 0 pageerrors, 0 локальных HTTP >=400.
- Дополнительные дефекты подложки, имён и логотипа сначала воспроизведены в
  `followup-before.txt` и `followup-before-logo.txt`, затем исправлены.
- Вручную просмотрены PNG обоих меню, collapsed/expanded на 900/1024px и mobile
  на 390px. [Скриншот обычного меню](after-legacy-900-expanded.png),
  [свёрнутое обычное меню](after-legacy-900-collapsed.png),
  [новое меню](after-modern-1024-collapsed.png).

Команды:

```bash
.venv/bin/python docs/qa/admin-sidebar-fix-2026-10-14/fixture.py 8765
playwright-cli -s=admin-sidebar-20261014 open 'http://127.0.0.1:8765/?shell=legacy&lang=ru' --browser chrome
playwright-cli -s=admin-sidebar-20261014 goto 'http://127.0.0.1:8765/?shell=legacy&lang=ru&phase=after'
playwright-cli -s=admin-sidebar-20261014 run-code --filename docs/qa/admin-sidebar-fix-2026-10-14/check.js > docs/qa/admin-sidebar-fix-2026-10-14/after.txt
python3 docs/qa/admin-sidebar-fix-2026-10-14/finalize.py
git diff --check
```

Границы: template fixture с вымышленной навигацией и unsaved staff user, без
настроек/.env приложения, с `DJANGO_TESTING=1`, пустой SQLite в памяти и LocMem
cache/email. Внешние запросы браузера заменены пустым ответом (Google Fonts —
fallback). Это проверка оболочки меню, не полного authenticated application:
данные, сохранение форм, полный Django suite, real screen reader/devices,
Firefox/WebKit и production — NOT RUN. Изолированные project PO не собирались;
языковая проверка подтверждает устойчивость меню к заданным длинным RU/AZ/EN
подписям. Исходные посторонние изменения сохранены.

Срез изменённых файлов: [hashes](source-hashes.json).
Машинный результат: [result](result.json); PNG: [manifest](screenshots.json).
""")
print(json.dumps({"checked": after["checked"], "passed": after["passed"],
                  "pageerrors": len(after["errors"]), "http_errors": len(after["network"]),
                  "source_hashes_match": True, "screenshots": len(manifest)}))
