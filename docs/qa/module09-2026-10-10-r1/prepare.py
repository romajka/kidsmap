"""Own module09 audit bootstrap; prior helper reused, prior evidence not reused."""
from pathlib import Path
import sys
sys.stdout.reconfigure(encoding='utf-8')
P=Path(__file__).resolve().parent
R=P.parents[2]
source=(R/'docs/qa/module08-2026-10-10-r1/prepare.py').read_text(encoding='utf-8')
source=source.replace("OLD=R/'docs/qa/module07-2026-10-10-r1'", "OLD=R/'docs/qa/module08-2026-10-10-r1'")
source=source.replace('module08','module09').replace('55439','55440').replace('8821','8822')
source=source.replace("OLD=R/'docs/qa/module09-2026-10-10-r1'", "OLD=R/'docs/qa/module08-2026-10-10-r1'")
source=source.replace('assert not scratch.exists();scratch.mkdir(parents=True)', 'scratch.mkdir(parents=True,exist_ok=True)')
source=source.replace("(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')", "assert not (P/'preservation-entry.json').exists() or json.loads((P/'preservation-entry.json').read_text())==prior\n(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')")
source=source.replace("(P/'screenshots').mkdir()", "(P/'screenshots').mkdir(exist_ok=True)")
source=source.replace(".replace('module07','module09').replace('55438','55440').replace('8820','8822')", ".replace('module08','module09').replace('55439','55440').replace('8821','8822')")
exec(compile(source,str(P/'prepare.py'),'exec'))
(P/'PLAN.md').write_text('''# Модуль09 — AUDIT ONLY

Один /root выполняет canonical orchestrator, Django, frontend-reviewer и browser-qa последовательно; независимая делегация не заявляется. Ownership: собственный run09, ignored scratch, PG55440/HTTP8822/browser module09-r1 и строка09 журнала. Приложение/правила/миграции/assertions не менять. Только fictional fixtures; без production/commit/push/deploy.

- [ ] Snapshot, preservation, graph-first discovery/coverage и source contracts.
- [ ] Новый отдельный стенд и initial synthetic fixtures; runtime соответствует WORKTREE.
- [ ] Reviews site/place/specialist/activity/event: create/validation/edit/moderation/reject/approve/hide, candidate/live, owner response/ACL, reactions/counters/pagination/escaping.
- [ ] Favorites add/remove/repeat/reload/logout/login; hidden/archive/deleted without privacy leak.
- [ ] Notifications read/unread/counters/links/invite accept, repeat/stale/revoked/deleted/foreign ID.
- [ ] RU/AZ/EN ×360/390/768/1024/1280/1440 native rendered states, keyboard/rating/menu, console/network and screenshots.
- [ ] Unchanged targeted tests, exact commands/exits, nine-section report, SOCIAL-QA findings/prompts, gaps/classification, only journal09 and handoff10; final preservation verification.
''',encoding='utf-8')
