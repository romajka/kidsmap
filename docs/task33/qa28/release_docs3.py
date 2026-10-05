"""Publish actual V3 release evidence while preserving the complete V2 packet."""
import json
from pathlib import Path

root = Path('/mnt/c/kidsmap/docs/task33')
def read(name):
    return json.loads((root/'reports'/name).read_text())
artifact = read('28-artifact.json')
image = read('28-release-image.json')
static = read('28-release-image-static.json')
host = read('28-static.json')
identity = read('28-artifact-identity.json')
assert artifact['identity'] == image['artifact_identity'] == static['artifact_identity'] == host['artifact_identity']
assert identity['workspace_captured_source_mismatches'] == []
for key in ('file_count', 'manifest_sha256', 'file_inventory_sha256'):
    assert static[key] == host[key]
document = root/'release-R2.md'
preserved = root/'reports/28-release-packet-v2.md'
assert not preserved.exists()
text = document.read_text()
preserved.write_text(text)
begin = text.index('## Exact revision')
end = text.index('## Schema, media, cohort')
exact = f'''## Exact revision

Checkout C:\\kidsmap, branch task33-progress, HEAD015d031d8eb17114bd860159dde805b38df3c13c. Candidate includes dirty application21–27 and the root-owned stage28 Event admin/owner datetime precision fix; HEAD alone does not identify it. Current V3 artifact `{artifact['identity']}`, {artifact['file_count']} allowlisted regular files, standby `{artifact['standby']}`.

Archive `{artifact['archive']}`; archiveSHA256 `{artifact['archive_sha256']}`, manifestSHA256 `{artifact['manifest_sha256']}`. V1/V2 archives and prior packet preserved. V3 changes exactly `src/catalog/domain_admin/place.py` and `src/catalog/forms.py`, adds `src/catalog/testcases/test_task33_event_admin_precision.py`, deletes nothing. Root final GREEN43 precedes freeze; [28-artifact-refresh3.json](reports/28-artifact-refresh3.json) retains exact approved member hashes. QA recovery_reader remains SHA83513bde82b1211adbd170aeec95187154a7d9df328c175ab7bbd9dfcc389d21.

No env/Git/venv/user media/database/logs/dumps; shell modes0755. Host Python3.12.3/39 installed dependencies inventoried; offline wheels are not bundled. [28-artifact.json](reports/28-artifact.json) captures every sourceSHA and three explicit AZ/RU/EN compiled MO deltas from identical PO. Current workspace2794 captured source files verified with zero drift; Windows bytes preserved. [28-artifact-identity.json](reports/28-artifact-identity.json) records exact executable/dependency/static/migration identities.

'''
text = text[:begin]+exact+text[end:]
begin = text.index('## Built LOCAL image and static closure')
end = text.index('## Stop criteria and external gates')
built = f'''## Built LOCAL image and static closure

Earlier V2 reader-only refresh and the failed2795 inventory (two generated QA-helper pyc files) remain historical evidence, with original standby preserved. V3 was extracted from its verified archive into `/root/km28-image-context3`: exactly2794 actual regular files, no extras/symlinks/env/media/DB/venv. Full inventory and SHA equality checked before AND after actual build. [28-release-context.json](reports/28-release-context.json), [V2 packet](reports/28-release-packet-v2.md).

Final LOCAL image config ID `{image['image_id']}`, tag `{image['tag']}`. Actual `docker build --iidfile ... -t ... /root/km28-image-context3` exit0. [28-release-image.json](reports/28-release-image.json) records actual daemon inspection; no registry publish/accessibility or registry manifest identity is inferred from config ID. Owned networknone/noports metadata-only probe confirms all2794 image members match artifact and data paths are absent; cleanupPASS. [28-release-image-verification.json](reports/28-release-image-verification.json).

Image Python3.12.15/39 packages differs from tested host Python3.12.3/39; only package-version delta is pip24.0→25.0.1. [Runtime delta](reports/28-release-runtime-delta.json). Full application suite inside image NOT_RUN. Guarded image and separately executed root host WhiteNoise production-backend collectstatic both PASS for this exact V3: {static['file_count']} files, manifestSHA `{static['manifest_sha256']}`, inventorySHA `{static['file_inventory_sha256']}`. DJANGO_TESTING1, network/libpq guards TRUE, external credentials FALSE; image networknone/noports/read-only QA helper/owned temporary output; cleanupPASS. No web/Gunicorn/deployment started. [Image static](reports/28-release-image-static.json), [root host static](reports/28-static.json).

Official standalone Compose v5.5.0 config merge repeated for exact context3: exit0, three missing required variables each exit1; default writesoff/userIDs empty/private bind exact. Synthetic image digest in config validation remains explicitly synthetic; actual local build is separate evidence. [28-release-compose.json](reports/28-release-compose.json). Future production runtime checks and activation require separate instruction.

'''
text = text[:begin]+built+text[end:]
text = text.replace('Base/deployment/application unchanged; override never activated here.',
                    'Base Compose and deployment files unchanged by this package; override never activated here.')
document.write_text(text)
review = root/'reports/28-release-review.md'
with review.open('a') as out:
    out.write(f'''\n## Current V3 after root Event precision correction\n\nRoot-owned final GREEN43 preceded freeze. `release3_build.py` exit0: current `{artifact['identity']}`,2794 files; exactly two application members changed and one new regression module added, no deletion. Approved three SHA values verified before freeze. V1/V2 preserved; [28-artifact-refresh3.json](28-artifact-refresh3.json). Current workspace2794 zero captured drift, archive/manifest/standby PASS. Recovery reader unchanged; exact metadata handed directly to DB for fresh native restoration.\n\n`release_clean_context.py /root/km28-image-context3 v2`, `release_image_build.py release3`, `release_image_verify.py release3`, `release_image_static.py release3`, `release_compose_verify.py v4`, `release_runtime_delta.py release3`, `release_finalize.py release3` all exit0. Commands invoked with `wsl -d Ubuntu-24.04 -u root --exec env PYTHONDONTWRITEBYTECODE=1 /root/kidsmap-task33/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/<helper>`. Actual current LOCAL image `{image['image_id']}`,2794 exact image members/no data paths; exhaustive source context before/after and owned-container cleanup PASS. Current root host and actual-image static both9305 files with identical manifest/inventory SHA. Interpreter drift3.12.3→3.12.15 and pip24.0→25.0.1 remains explicit; full suite inside image NOT_RUN. Prior V2 image/context/static/identity/Compose summaries preserved. Production NOT_CONTACTED, registry publish/deploy NOT_RUN.\n\nSequential security-reviewer fresh260 execution and independent DB/browser/root final full-suite closure belong to their current evidence; release checks above do not establish whole-site or production readiness.\n''')
print(json.dumps({'status':'PASS','current_identity':artifact['identity'],'prior_packet_preserved':True,'production':'NOT_CONTACTED'}))
