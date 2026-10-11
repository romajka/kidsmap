"""Bounded source and translation research; no compilation or source mutation."""
from pathlib import Path
import json,hashlib,gettext,subprocess
P=Path(__file__).resolve().parent;R=P.parents[2]
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/rules/audit-contract.md','docs/qa/module-acceptance-prompts.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/admin-place-map-fix-2026-10-09.md']
locale={}
for lang in ['ru','az','en']:
 p=R/f'locale/{lang}/LC_MESSAGES/django.mo'
 if p.exists():
  with p.open('rb') as f:t=gettext.GNUTranslations(f)
  locale[lang]={x:t.gettext(x) for x in ['Владелец','Связанное место','Начало мероприятия','Фото','Удалить']}
templates={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'templates').rglob('*') if p.is_file()}
(P/'snapshot-templates.json').write_text(json.dumps(templates,indent=2),encoding='utf-8')
data={'missing_required_docs':[p for p in docs if not (R/p).exists()],'compiled_worktree_translations':locale,'extra_root_templates_hash_count':len(templates),'template_snapshot_timing':'Captured before final state matrix. Launcher initial 2776-file digest did not include root templates; root templates are used by admin and separately verified here.','graph':{'project':'C-kidsmap','ready':True,'generation':'2026-10-09T21:09:07Z','nodes':88227,'edges':178873,'relevant_metadata_changed':True,'coverage':'owner template partial; domain/form/controller/model coverage unavailable; relevant routes verified from source; false-noise graph edges not relied upon'},'scope':'No regressions inferred without a demonstrated known-good version. Existing compiled .mo is part of this WORKTREE; external browser requests blocked.'}
(P/'source-facts.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(data,ensure_ascii=True))
