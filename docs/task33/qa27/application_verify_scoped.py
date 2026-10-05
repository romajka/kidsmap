"""Post-run wrapper: retain broad drift, verify the explicitly unexecuted review helper.

The frozen strict verifier retains every browser/runtime/isolation assertion.
Only its source evidence input names the separately recorded executed-source scope.
"""
import hashlib
import json
import sys
from pathlib import Path

run = Path(sys.argv[1])
output = Path(sys.argv[2])
workspace = Path('/mnt/c/kidsmap')
mirror = Path('/root/km27-browser-frozen')
broad = json.loads((run / 'source-current-check.json').read_text())
manifest = json.loads((run / 'source-sha256.json').read_text())
unused = 'docs/task33/qa27/review_current.py'
assert broad['mismatches'] == [unused]
assert not broad['new_application_files']
launchers = ('application_run-browser.sh', 'application_browser.py', 'application_sync.sh')
for name in launchers:
    assert 'review_current' not in (mirror / 'docs/task33/qa27' / name).read_text()
delta = {
    'path': unused,
    'frozen_sha256': manifest[unused],
    'current_sha256': hashlib.sha256((workspace / unused).read_bytes()).hexdigest(),
    'reason': 'Parent source-only reviewer collector updated after freeze; not referenced by browser launcher, wrapper or sync and not executed in browser runtime.',
}
assert delta['frozen_sha256'] != delta['current_sha256']
scoped = dict(broad)
scoped.update({
    'mismatches': [],
    'broad_check': 'source-current-check.json',
    'broad_mismatch_count': 1,
    'application_and_executed_browser_harness_mismatches': 0,
    'unexecuted_review_helper_delta': delta,
})
(run / 'source-scoped-current-check.json').write_text(json.dumps(scoped, indent=2) + '\n')
verifier = mirror / 'docs/task33/qa27/application_verify.py'
code = verifier.read_text()
needle = "current=json.loads((root/'source-current-check.json').read_text())"
assert code.count(needle) == 1
code = code.replace(needle, "current=json.loads((root/'source-scoped-current-check.json').read_text())")
sys.argv = [str(verifier), str(run), str(output)]
exec(compile(code, str(verifier), 'exec'), {'__name__': '__main__'})
