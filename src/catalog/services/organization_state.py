"""One read model for an organization's lifecycle, readiness and branch health.

Admin, the owner workspace, the public pages and the diagnostics command all
ask this module the same questions, so a status or a branch count can no
longer differ between screens. Nothing here grants rights or writes data,
except ``assign_public_slug`` which the publication service calls when an
organization is approved.
"""
from dataclasses import dataclass, field
import re

from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.urls import NoReverseMatch, reverse

from catalog.services.permanent_place_rules import copy as t

LINK_KINDS = ('business', 'informational')


# --- visibility -----------------------------------------------------------

def public_q(prefix=''):
    """Q for organizations a visitor may see. ``prefix`` e.g. 'organization__'."""
    return Q(**{f'{prefix}status': 'published', f'{prefix}approved_at__isnull': False,
                f'{prefix}archived_at__isnull': True})


def current_branch_q(prefix=''):
    """Q over Place: the place's link to its organization is still confirmed."""
    p = prefix
    return Q(**{f'{p}organization__isnull': False, f'{p}organization__archived_at__isnull': True,
                f'{p}organization_relationship_kind__in': LINK_KINDS,
                f'{p}organization_join_place_ownership_version': F(f'{p}ownership_version'),
                f'{p}organization_join_org_ownership_version': F(f'{p}organization__ownership_version')})


def is_public(org):
    return bool(org and org.status == 'published' and org.approved_at is not None and org.archived_at is None)


def is_inconsistent(org):
    """Legacy rows marked published without an approval are never public."""
    return org.status == 'published' and org.approved_at is None and org.archived_at is None


def public_path(org, language=None):
    from django.utils.translation import override
    name = 'organization_detail_slug' if org.slug else 'organization_detail'
    kwargs = {'slug': org.slug} if org.slug else {'public_id': org.public_id}
    try:
        if language:
            with override(language):
                return reverse(name, kwargs=kwargs)
        return reverse(name, kwargs=kwargs)
    except NoReverseMatch:
        return ''


# --- slugs -----------------------------------------------------------------

def build_slug(org, *, exclude_pk=None):
    from catalog.models import Organization
    from catalog.services.slugs import build_ascii_slug, PUBLIC_SLUG_MAX_LENGTH
    source = org.name_az or org.name_en or org.name_ru
    base = build_ascii_slug(source, fallback=f'organization-{org.pk or "new"}')
    # Never collide with the UUID route or look like a bare id.
    if re.match(r'^\d+(?:-|$)', base):
        base = f'org-{base}'[:PUBLIC_SLUG_MAX_LENGTH].rstrip('-')
    candidate, index = base, 2
    while Organization.objects.filter(slug=candidate).exclude(pk=exclude_pk or org.pk).exists():
        suffix = f'-{index}'
        candidate = f'{base[:PUBLIC_SLUG_MAX_LENGTH - len(suffix)].rstrip("-")}{suffix}'
        index += 1
    return candidate


def assign_public_slug(org):
    """Reserve the readable URL at first approval; later renames keep it stable."""
    from catalog.models import Organization
    if org.slug:
        return org.slug
    while True:
        slug = build_slug(org)
        try:
            # A namesake may reserve this slug while its own approval commits.
            # Keep the conflicting write inside a savepoint so approval can retry.
            with transaction.atomic():
                Organization.objects.filter(pk=org.pk, slug__isnull=True).update(slug=slug)
            break
        except IntegrityError:
            if not Organization.objects.filter(slug=slug).exclude(pk=org.pk).exists():
                raise
    org.slug = Organization.objects.filter(pk=org.pk).values_list('slug', flat=True).first()
    return org.slug


# --- social links ------------------------------------------------------------

_SOCIAL = {
    'instagram': ('https://www.instagram.com/', ('instagram.com',)),
    'facebook': ('https://www.facebook.com/', ('facebook.com', 'fb.com')),
    'tiktok': ('https://www.tiktok.com/@', ('tiktok.com',)),
}


def social_url(kind, value):
    value = (value or '').strip()
    if not value:
        return ''
    prefix, hosts = _SOCIAL[kind]
    if re.match(r'^https?://', value, re.I):
        host = re.sub(r'^https?://(www\.)?', '', value, flags=re.I).split('/', 1)[0].lower()
        return value if any(host == h or host.endswith('.' + h) for h in hosts) else ''
    handle = value.lstrip('@').strip('/')
    if not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', handle):
        return ''
    return prefix + handle


def normalize_social(kind, value):
    """Store a clean handle or URL; raise ValueError for anything else."""
    value = (value or '').strip()
    if value and not social_url(kind, value):
        raise ValueError(kind)
    return value


def social_links(org):
    rows = []
    for kind, label in (('instagram', 'Instagram'), ('facebook', 'Facebook'), ('tiktok', 'TikTok')):
        url = social_url(kind, getattr(org, kind, ''))
        if url:
            rows.append({'kind': kind, 'label': label, 'url': url})
    return rows


# --- lifecycle -----------------------------------------------------------------

@dataclass
class Lifecycle:
    code: str
    label: str
    tone: str           # good | warn | danger | info | muted
    icon: str           # material symbol name
    hint: str
    public: bool
    review_pending: bool = False
    needs_changes: bool = False
    review_note: str = ''


def _revision(org, revision):
    if revision is not False:
        return revision
    from catalog.models import VolunteerPlaceRevision
    return VolunteerPlaceRevision.objects.filter(organization=org).only(
        'status', 'version', 'review_note', 'changed_fields', 'updated_at').first()


def lifecycle(org, revision=False):
    """The single status shown for an organization on every screen."""
    revision = _revision(org, revision)
    rstatus = getattr(revision, 'status', None)
    pending = rstatus == 'pending'
    rejected = rstatus in ('rejected', 'declined')
    note = (getattr(revision, 'review_note', '') or '') if rejected else ''
    public = is_public(org)
    if org.archived_at is not None:
        return Lifecycle('archived', t('В архиве', 'Arxivdə', 'Archived'), 'muted', 'inventory_2',
                         t('Организация скрыта и не редактируется.', 'Təşkilat gizlədilib.', 'Hidden and read-only.'), False)
    if is_inconsistent(org) and not pending:
        return Lifecycle('inconsistent', t('Требует решения модератора', 'Moderator qərarı lazımdır', 'Needs a moderator decision'),
                         'danger', 'report',
                         t('Отмечена опубликованной, но не была одобрена. На сайте не видна.',
                           'Dərc kimi qeyd olunub, lakin təsdiqlənməyib. Saytda görünmür.',
                           'Marked published but never approved. Not visible on the site.'), False, pending, rejected, note)
    if public and pending:
        return Lifecycle('published_review', t('Опубликована · правки на проверке', 'Dərc olunub · dəyişikliklər yoxlamada', 'Published · changes in review'),
                         'good', 'published_with_changes',
                         t('На сайте видна текущая версия. Новые сведения появятся после одобрения.',
                           'Saytda cari versiya görünür. Yeni məlumatlar təsdiqdən sonra çıxacaq.',
                           'The current version is live. New details appear after approval.'), True, True)
    if public and rejected:
        return Lifecycle('published_changes', t('Опубликована · правки вернули', 'Dərc olunub · dəyişikliklər qaytarıldı', 'Published · changes returned'),
                         'warn', 'rate_review',
                         t('Исправьте правки по замечанию модератора и отправьте снова.',
                           'Moderatorun qeydinə görə düzəldin və yenidən göndərin.',
                           'Fix the changes per the moderator note and resubmit.'), True, False, True, note)
    if public:
        return Lifecycle('published', t('Опубликована', 'Dərc olunub', 'Published'), 'good', 'verified',
                         t('Организация видна в каталоге KidsMap.', 'Təşkilat KidsMap kataloqunda görünür.',
                           'Visible in the KidsMap directory.'), True)
    if pending:
        return Lifecycle('pending', t('На проверке', 'Yoxlamada', 'In review'), 'info', 'hourglass_top',
                         t('Модератор KidsMap проверяет сведения. Обычно это занимает до 24 часов.',
                           'KidsMap moderatoru məlumatları yoxlayır. Adətən 24 saata qədər.',
                           'A KidsMap moderator is reviewing it, usually within 24 hours.'), False, True)
    if rejected:
        return Lifecycle('needs_changes', t('Нужны исправления', 'Düzəliş lazımdır', 'Needs changes'), 'warn', 'edit_note',
                         t('Модератор вернул сведения. Исправьте и отправьте снова.',
                           'Moderator məlumatları qaytardı. Düzəldin və yenidən göndərin.',
                           'The moderator returned it. Fix and resubmit.'), False, False, True, note)
    return Lifecycle('draft', t('Черновик', 'Qaralama', 'Draft'), 'muted', 'draft',
                     t('Заполните профиль и отправьте на проверку, чтобы появиться в каталоге.',
                       'Profili doldurun və kataloqda görünmək üçün yoxlamaya göndərin.',
                       'Complete the profile and submit it for review to appear in the directory.'), False)


# --- branches -----------------------------------------------------------------

@dataclass
class BranchHealth:
    current: list = field(default_factory=list)
    stale: list = field(default_factory=list)
    pending_requests: int = 0

    @property
    def total(self):
        return len(self.current) + len(self.stale)

    @property
    def current_count(self):
        return len(self.current)

    @property
    def stale_count(self):
        return len(self.stale)

    @property
    def public_count(self):
        return sum(1 for p in self.current if getattr(p, 'is_public', False))


def stale_reason(place, org):
    if place.organization_relationship_kind not in LINK_KINDS:
        return t('Тип связи не задан', 'Əlaqə növü yoxdur', 'Link type missing')
    if place.organization_join_place_ownership_version != place.ownership_version:
        return t('У места сменился владелец', 'Məkanın sahibi dəyişib', 'The place changed owner')
    if place.organization_join_org_ownership_version != org.ownership_version:
        return t('У организации сменился владелец', 'Təşkilatın sahibi dəyişib', 'The organization changed owner')
    return t('Связь не подтверждена', 'Əlaqə təsdiqlənməyib', 'Link not confirmed')


def branch_health(org, places=None):
    """Split linked places into confirmed and needing re-confirmation.

    A link is bound to both sides' ownership versions on purpose: a new owner
    must not inherit a network the previous owner agreed to. Instead of the
    old silent disappearance, stale links are reported with their reason.
    """
    from catalog.models import OrganizationPlaceRequest, Place
    from catalog.services.organization_ownership import affiliation_current
    if places is None:
        places = list(Place.objects.filter(organization=org, deleted_at__isnull=True).order_by('pk'))
    health = BranchHealth()
    for place in places:
        if affiliation_current(place, org):
            place.link_state = 'current'
            health.current.append(place)
        else:
            place.link_state = 'stale'
            place.link_stale_reason = stale_reason(place, org)
            health.stale.append(place)
    health.pending_requests = OrganizationPlaceRequest.objects.filter(organization=org, status='pending').count()
    return health


def branch_counts_by_org(org_ids):
    """{org_id: (current, stale)} in two queries, for lists."""
    from django.db.models import Count
    from catalog.models import Place
    base = Place.objects.filter(organization_id__in=org_ids, deleted_at__isnull=True)
    current = dict(base.filter(current_branch_q()).values('organization_id').annotate(n=Count('pk')).values_list('organization_id', 'n'))
    total = dict(base.values('organization_id').annotate(n=Count('pk')).values_list('organization_id', 'n'))
    return {pk: (current.get(pk, 0), total.get(pk, 0) - current.get(pk, 0)) for pk in org_ids}


# --- readiness ---------------------------------------------------------------

def readiness(org, *, data=None, health=None):
    """What the profile still lacks before it reads well publicly.

    ``data`` overrides model values with the open candidate, so the checklist
    reflects what the owner is about to submit.
    """
    values = {name: getattr(org, name, '') for name in (
        'name_az', 'name_ru', 'name_en', 'description_az', 'description_ru', 'phone', 'whatsapp',
        'website', 'logo', 'cover_photo', 'instagram', 'facebook', 'tiktok', 'address')}
    if data:
        values.update({k: v for k, v in data.items() if k in values})
    has = lambda name: bool(str(values.get(name) or '').strip())
    health = health or branch_health(org)
    items = [
        ('name', t('Название на азербайджанском', 'Azərbaycan dilində ad', 'Azerbaijani name'), has('name_az'), True, 'org-about'),
        ('translations', t('Название на русском или английском', 'Rus və ya ingilis dilində ad', 'Russian or English name'), has('name_ru') or has('name_en'), False, 'org-about'),
        ('description', t('Описание от 80 символов', '80 simvoldan təsvir', 'Description, 80+ characters'), len(str(values.get('description_az') or '').strip()) >= 80, False, 'org-about'),
        ('contacts', t('Телефон, WhatsApp или сайт', 'Telefon, WhatsApp və ya sayt', 'Phone, WhatsApp or website'), has('phone') or has('whatsapp') or has('website'), False, 'org-about'),
        ('logo', t('Логотип', 'Loqo', 'Logo'), has('logo'), False, 'org-media'),
        ('cover', t('Обложка', 'Örtük şəkli', 'Cover image'), has('cover_photo'), False, 'org-media'),
        ('social', t('Соцсети', 'Sosial şəbəkələr', 'Social links'), has('instagram') or has('facebook') or has('tiktok'), False, 'org-about'),
        ('branches', t('Хотя бы один подтверждённый филиал', 'Ən azı bir təsdiqlənmiş filial', 'At least one confirmed branch'), health.current_count > 0, False, 'org-branches'),
    ]
    rows = [{'key': k, 'label': label, 'done': done, 'required': req, 'anchor': anchor} for k, label, done, req, anchor in items]
    done = sum(1 for r in rows if r['done'])
    required_missing = [r for r in rows if r['required'] and not r['done']]
    return {'items': rows, 'done': done, 'total': len(rows), 'percent': round(100 * done / len(rows)),
            'can_submit': not required_missing, 'missing_required': required_missing}


def steps(org, state, ready, health):
    """Five-step journey shown as a stepper in the workspace."""
    profile_done = ready['can_submit']
    media_done = any(r['done'] for r in ready['items'] if r['key'] in ('logo', 'cover'))
    rows = [
        ('profile', t('Профиль', 'Profil', 'Profile'), profile_done, '#org-about'),
        ('media', t('Медиа', 'Media', 'Media'), media_done, '#org-media'),
        ('branches', t('Филиалы', 'Filiallar', 'Branches'), health.current_count > 0, '#org-branches'),
        ('review', t('Проверка', 'Yoxlama', 'Review'), state.review_pending or state.public, '#org-about'),
        ('live', t('На сайте', 'Saytda', 'Live'), state.public, ''),
    ]
    current = next((i for i, row in enumerate(rows) if not row[2]), None)
    # The line fills up to the last step reached in order.
    reached = current if current is not None else len(rows) - 1
    progress = round(100 * reached / (len(rows) - 1))
    return {'items': [{'key': k, 'label': label, 'done': done, 'href': href, 'index': i + 1, 'current': i == current}
                      for i, (k, label, done, href) in enumerate(rows)], 'progress': progress}


# --- diagnostics -----------------------------------------------------------------

def diagnose():
    """Rows describing data that breaks the organization rules (read only)."""
    from catalog.models import Organization, Place, VolunteerPlaceRevision
    issues = []
    pending_orgs = set(VolunteerPlaceRevision.objects.filter(organization__isnull=False, status='pending')
                       .values_list('organization_id', flat=True))
    for org in Organization.objects.filter(status='published', approved_at__isnull=True, archived_at__isnull=True).order_by('pk'):
        issues.append({'code': 'published_without_approval', 'organization_id': org.pk, 'name': str(org),
                       'has_pending_review': org.pk in pending_orgs})
    for org in Organization.objects.filter(public_q(), slug__isnull=True).order_by('pk'):
        issues.append({'code': 'public_without_slug', 'organization_id': org.pk, 'name': str(org)})
    stale = Place.objects.filter(organization__isnull=False, deleted_at__isnull=True).exclude(current_branch_q()).select_related('organization').order_by('organization_id', 'pk')
    for place in stale:
        issues.append({'code': 'stale_branch', 'organization_id': place.organization_id, 'name': str(place.organization),
                       'place_id': place.pk, 'reason': stale_reason(place, place.organization)})
    for org in Organization.objects.filter(owner__isnull=True, archived_at__isnull=True).order_by('pk'):
        issues.append({'code': 'no_owner', 'organization_id': org.pk, 'name': str(org)})
    return issues
