"""Prepare audit-only harness and frozen copies of CURRENT catalogues; no compilation."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREVIOUS = ROOT/'docs/qa/place-qa05-plan-2026-10-10'
scratch = ROOT/'.tmp/place-qa06-plan-20261010'
scratch.mkdir(parents=True,exist_ok=False)
manifest = []
for language in ['ru','az','en']:
    for extension in ['po','mo']:
        source = ROOT/f'locale/{language}/LC_MESSAGES/django.{extension}'
        target = scratch/f'baseline-locale/{language}/LC_MESSAGES/django.{extension}'
        target.parent.mkdir(parents=True,exist_ok=True)
        data = source.read_bytes()
        target.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        assert digest==hashlib.sha256(source.read_bytes()).hexdigest()==hashlib.sha256(target.read_bytes()).hexdigest()
        manifest.append({'source':source.relative_to(ROOT).as_posix(),
            'copy':target.relative_to(ROOT).as_posix(),'sha256':digest,'operation':'byte-identical copy; not compiled'})
(HERE/'frozen-catalog-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
for old,new in [('qa05_settings.py','qa06_settings.py'),('runtime.py','runtime.py'),
                ('prepare.py','prepare.py'),('pw.py','pw.py'),('browser.config.json','browser.config.json'),
                ('browser-setup.js','browser-setup.js')]:
    content = (PREVIOUS/old).read_text(encoding='utf-8')
    for before,after in [('qa05','qa06'),('QA05','QA06'),('55440','55442'),('8819','8821')]:
        content = content.replace(before,after)
    if new=='qa06_settings.py':
        content += "\n# Read frozen baseline assets only; fresh compilation awaits scope approval.\nLOCALE_PATHS = [QA_ROOT / 'baseline-locale']\n"
    if new=='prepare.py':
        start = content.index("files = ['static/admin/css")
        end = content.index('active = next',start)
        content = content[:start]+"files = ['src/config/settings.py','Dockerfile','.github/workflows/deploy.yml','scripts/release-server.sh','docs/qa/module-acceptance-prompts.md']\nfiles += [f'locale/{language}/LC_MESSAGES/django.{ext}' for language in ['ru','az','en'] for ext in ['po','mo']]\nfiles += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT / 'docs/superpowers/plans').glob('2026-10-10-place-qa0[1-5]-*.md'))]\n"+content[end:]
    if new=='runtime.py':
        content = content.replace("'media_root':str(settings.MEDIA_ROOT)","'locale_paths':[str(p) for p in settings.LOCALE_PATHS],'compiled_assets':'frozen baseline copies, not recompiled','media_root':str(settings.MEDIA_ROOT)")
    (HERE/new).write_text(content,encoding='utf-8')
print('Created QA06 audit harness and six byte-identical PO/MO copies. No catalogue compiled.')
