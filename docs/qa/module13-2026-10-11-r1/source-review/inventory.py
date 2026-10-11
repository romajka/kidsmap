"""Read-only source inventory; no Django setup, DB, network or application writes."""
import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('C:/kidsmap')
OUT = Path(__file__).resolve().parent


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def domain(text):
    text = text.lower()
    for words, result in [
        (('specialist',), 'specialists'), (('event',), 'events'),
        (('organization', 'program', 'activit', 'group'), 'business_structure'),
        (('team', 'ownership', 'invitation', 'permission'), 'access'),
        (('review',), 'reviews'), (('photo', 'media'), 'media'),
        (('analytics', 'track'), 'analytics'),
        (('auth', 'password', 'login', 'logout', 'signup', 'profile', 'account_settings'), 'account'),
        (('volunteer',), 'volunteer'), (('place', 'catalog', 'category'), 'places'),
    ]:
        if any(word in text for word in words):
            return result
    return 'other'


def literal(node):
    return node.value if isinstance(node, ast.Constant) else ast.unparse(node)


routes = []
for rel in ['src/catalog/urls.py', 'src/config/urls.py']:
    code = (ROOT / rel).read_text(encoding='utf-8')
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        function = ast.unparse(node.func)
        if function not in ('path', 're_path'):
            continue
        route = literal(node.args[0])
        target = ast.unparse(node.args[1]) if len(node.args) > 1 else ''
        name = next((literal(x.value) for x in node.keywords if x.arg == 'name'), '')
        routes.append(dict(file=rel, line=node.lineno, route=route, target=target,
                           name=name, domain=domain(str(route) + ' ' + str(name)),
                           kind='declaration', runtime_coverage='UNKNOWN'))

models = []
classes = []
for path in sorted((ROOT / 'src/catalog/models').glob('*.py')):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    classes += [(path, node, [ast.unparse(x) for x in node.bases])
                for node in tree.body if isinstance(node, ast.ClassDef)]
model_names = {node.name for _, node, bases in classes if 'models.Model' in bases}
for _ in range(len(classes)):
    inherited = {node.name for _, node, bases in classes if any(x in model_names for x in bases)}
    if inherited <= model_names:
        break
    model_names.update(inherited)
for path, node, bases in classes:
        if node.name not in model_names:
            continue
        fields = []
        for child in node.body:
            if isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
                call = ast.unparse(child.value.func)
                if 'Field' in call or call.endswith(('ForeignKey', 'OneToOneField', 'ManyToManyField')):
                    fields += [ast.unparse(x) for x in child.targets]
        models.append(dict(file=path.relative_to(ROOT).as_posix(), line=node.lineno,
                           name=node.name, bases=bases, fields=fields,
                           domain=domain(node.name), runtime_coverage='UNKNOWN'))

admin_surfaces = []
admin_routes = []
for path in sorted((ROOT / 'src/catalog/domain_admin').glob('*.py')):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and ast.unparse(decorator.func).endswith('register'):
                    admin_surfaces.append(dict(file=path.relative_to(ROOT).as_posix(), line=node.lineno,
                        models=[ast.unparse(x) for x in decorator.args], admin_class=node.name,
                        runtime_coverage='UNKNOWN', kind='decorator declaration'))
        elif isinstance(node, ast.Call) and ast.unparse(node.func).endswith('site.register'):
            admin_surfaces.append(dict(file=path.relative_to(ROOT).as_posix(), line=node.lineno,
                models=[ast.unparse(x) for x in node.args[:1]],
                admin_class=ast.unparse(node.args[1]) if len(node.args) > 1 else '',
                runtime_coverage='UNKNOWN', kind='registration declaration'))
        elif isinstance(node, ast.Call) and ast.unparse(node.func) in ('path', 're_path') and node.args:
            admin_routes.append(dict(file=path.relative_to(ROOT).as_posix(),line=node.lineno,
                route=literal(node.args[0]), target=ast.unparse(node.args[1]) if len(node.args)>1 else '',
                name=next((literal(x.value) for x in node.keywords if x.arg=='name'),''),
                kind='admin route declaration',runtime_coverage='UNKNOWN'))

history = []
for number in range(1, 13):
    folders = sorted((ROOT / 'docs/qa').glob(f'module{number:02d}-*'))
    folder = folders[-1]
    report = folder / 'REPORT.md'
    findings = folder / 'FINDINGS.md'
    texts = [p.read_text(encoding='utf-8') for p in (report, findings) if p.exists()]
    combined = '\n'.join(texts)
    ids = sorted(set(re.findall(r'\b[A-Z][A-Z0-9-]*-QA-\d+\b', combined)))
    history.append(dict(module=f'{number:02d}', report=report.relative_to(ROOT).as_posix(),
        findings=findings.relative_to(ROOT).as_posix() if findings.exists() else None,
        read_complete_files=len(texts), hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (report, findings) if p.exists()},
        snapshot_shas=sorted(set(re.findall(r'\b[0-9a-f]{40}\b', combined))),
        finding_ids=ids, status='HISTORICAL_CHECKLIST_ONLY', fresh_runtime='NOT_RUN_BY_THIS_AGENT',
        section_headings=[line for text in texts for line in text.splitlines() if line.startswith('## ')],
        all_run_folders=[p.relative_to(ROOT).as_posix() for p in folders]))

coverage_map = [
    dict(domain='places', modules=['01','05','06','09','11','12'], scenarios=['create','draft/reload','moderation','candidate/live','map','photos','nested pricing','public cards'],
         sources=['src/catalog/controllers/owner_places_controller.py','src/catalog/services/publication.py','src/catalog/domain_admin/place.py']),
    dict(domain='business_structure', modules=['02','05','07','09','11'], scenarios=['organization no branches','canonical connect','program/activity/group','detach','contacts inheritance'],
         sources=['src/catalog/controllers/organization_workspace.py','src/catalog/controllers/program_workspace.py','src/catalog/services/organization_ownership.py','src/catalog/services/organization_connections.py','src/catalog/services/catalog_structure.py','src/catalog/domain_admin/business.py']),
    dict(domain='specialists', modules=['03','06','09','11'], scenarios=['proposal','claim','cooperation','practice locations','private docs','profile publication'],
         sources=['src/catalog/controllers/specialist_workspace.py','src/catalog/services/specialist_domain.py','src/catalog/services/specialist_documents.py','src/catalog/services/specialist_proposal_drafts.py','src/catalog/forms_specialist_locations.py']),
    dict(domain='events', modules=['04','06','09','11'], scenarios=['onsite/online','organizer versus venue','draft/review','occurrence reschedule/cancel','venue snapshot'],
         sources=['src/catalog/controllers/owner_events_controller.py','src/catalog/services/event_domain.py','src/catalog/domain_admin/place.py']),
    dict(domain='access', modules=['07','08','09','12'], scenarios=['business roles/scopes','object ACL','revoke','foreign IDs','volunteer rights','identity'],
         sources=['src/catalog/services/business_team.py','src/catalog/services/place_access.py','src/catalog/controllers/business_team_api.py']),
    dict(domain='settings', modules=['10','11','12'], scenarios=['sections OFF/ON','menu/direct/search/map','locale','tracking switches'],
         sources=['src/catalog/services/features.py','src/catalog/domain_admin/site.py','src/catalog/services/public_presentation.py','src/catalog/controllers/public_details.py']),
    dict(domain='reviews_favorites', modules=['09','10'], scenarios=['moderation','private/public visibility','favorites toggling','related feeds'],
         sources=['src/catalog/services/review_use_cases.py','src/catalog/controllers/owner_reviews_controller.py','src/catalog/views.py']),
    dict(domain='seo_analytics', modules=['11','12'], scenarios=['canonical/redirect','views','phone events','candidate/live metadata'],
         sources=['src/catalog/services/seo.py','src/catalog/services/public_urls.py','src/catalog/services/tracking.py','src/catalog/views.py']),
]
for row in coverage_map:
    row['historical_modules_are_not_current_proof'] = True
    row['this_agent_runtime_status'] = 'NOT_RUN'
paths = sorted(set(p for row in coverage_map for p in row['sources']) | {
    'src/catalog/urls.py','src/config/urls.py','src/catalog/services/publication_forms.py',
    'src/catalog/services/owner_specialist_use_cases.py','src/catalog/domain_admin/volunteer.py',
    'src/catalog/domain_admin/owner.py','src/catalog/controllers/workflow_notifications.py',
    'src/catalog/services/volunteer_proposals.py','src/catalog/models/volunteer.py',
    'src/catalog/models/catalog_structure.py','src/catalog/models/specialist_domain.py',
    'src/catalog/templates/admin/volunteer/hub_detail.html',
    'src/catalog/templates/pages/includes/organization_join_request.html',
    'src/catalog/templates/pages/organization_create.html',
    'src/catalog/templates/pages/organization_workspace.html',
    'src/catalog/templates/pages/organization_connections.html',
    'src/catalog/templates/pages/program_editor.html',
    'src/catalog/templates/pages/specialist_workspace.html',
    'src/catalog/templates/pages/owner_event_manage.html',
    'src/catalog/templates/admin/catalog/business/change_form.html'})
source_hashes = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths if (ROOT/p).exists()}
snapshot = dict(checkout=ROOT.as_posix(), head=git('rev-parse','HEAD'), branch=git('branch','--show-current'),
    active_run=re.search(r'^active_run:\s*(.+)$',(ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8'),re.M).group(1),
    utc=datetime.now(timezone.utc).isoformat(), mode='AUDIT_ONLY', production='NOT_RUN',
    source_hashes=source_hashes, missing_cited_sources=[p for p in paths if not (ROOT/p).exists()],
    dirty_cited_paths=[p for p in git('diff','--name-only','--',*paths).splitlines() if p])
result = dict(snapshot=snapshot,routes=routes,admin_routes=admin_routes,models=models,admin_surfaces=admin_surfaces,
    domain_map=coverage_map,history=history,
    limitations=['Static declarations are not runtime URL resolution or actual admin registry.',
        'Model inheritance/custom registration/dynamic relationships require source/runtime follow-up.',
        'Every runtime status is UNKNOWN or NOT RUN here; root owns the real-browser evidence.',
        'Graph best-effort cited coverage metadata_changed, coverage_unavailable; exact source was read.'])
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(routes=len(routes),admin_routes=len(admin_routes),models=len(models),admin_surfaces=len(admin_surfaces),
    historical_reports=len(history),historical_findings_mentions=sum(len(x['finding_ids']) for x in history),
    source_files=len(source_hashes),missing_cited_sources=snapshot['missing_cited_sources'],head=snapshot['head']),ensure_ascii=False))
