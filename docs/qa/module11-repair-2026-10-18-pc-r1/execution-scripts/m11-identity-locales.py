import json
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m11-full-r1';O=R/'docs/qa/module11-repair-2026-10-18-pc-r1';manifest=json.loads((Q/'locales-identity/manifest.json').read_text());assert set(manifest['locales'])=={'az','ru','en'};stage=json.loads((Q/'stage.json').read_text());stage['locales']='locales-identity';(Q/'stage.json').write_text(json.dumps(stage));(O/'stages/identity/evidence/isolated-locale-manifest.json').write_text(json.dumps(manifest,indent=2));print('Current identity locale manifest selected before new Django process, sharedMO untouched.')
