"""Read-only, access-scoped place identities and serialized creation checks.

An identity has independently labelled versions. Evidence from two versions is
never combined into a stronger match. This is not an owner/user data export.
"""
import math
import hashlib
import json
import re
import unicodedata
from urllib.parse import urlsplit

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.models import Exists, OuterRef
from django.utils import timezone
from catalog.models import Place, ServerDraft
from catalog.services import publication
from catalog.services.content_quality import public_place_queryset
from catalog.services.permanent_place_rules import copy as t

ACTIVE = ('draft', 'pending', 'rejected')
NAMES = ('name_az', 'name_ru', 'name_en', 'name')
FIELDS = (*NAMES, 'address', 'district', 'lat', 'lng', 'phone1', 'phone2', 'phone3',
          'phone_country', 'whatsapp_mode', 'whatsapp_number', 'website', 'instagram', 'public_links')
RANK = {'confirmed': 0, 'probable': 1, 'possible_branch': 2,
        'network_contact': 3, 'address_match': 4, 'nearby': 5}
_TRANSLIT = str.maketrans(dict(zip(
    'əıöüğşçабвгдеёзийклмнопрстуфхыэ',
    'eiougscabvgdeezijklmnoprstufhye')) | {
    'ж':'zh', 'ц':'ts', 'ч':'ch', 'ш':'sh', 'щ':'shch', 'ю':'yu', 'я':'ya', 'ь':'', 'ъ':''})


def normalize(value):
    if not isinstance(value, str): return ''
    raw = unicodedata.normalize('NFKC', value).casefold().translate(_TRANSLIT)
    return ' '.join(re.sub(r'[^\w]+', ' ', raw).split())


def phone(value):
    return re.sub(r'\D', '', value) if isinstance(value, str) else ''


def website(value):
    if not isinstance(value, str) or not value.strip(): return ''
    try:
        parts = urlsplit(value.strip() if '://' in value else 'https://' + value.strip())
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password: return ''
        return parts.hostname.casefold().removeprefix('www.') + parts.path.rstrip('/').casefold()
    except ValueError: return ''


def instagram(value):
    if not isinstance(value, str): return ''
    raw = value.strip().casefold().lstrip('@')
    if 'instagram.com/' in raw:
        raw = raw.split('instagram.com/', 1)[1].split('?', 1)[0].strip('/')
    return raw


def identity_fields(values):
    data = {}
    for name in FIELDS:
        value = values.get(name) if isinstance(values, dict) else getattr(values, name, None)
        if name == 'public_links':
            from catalog.services.place_public_links import normalize_public_links
            data[name] = []
            for row in value if isinstance(value,list) else []:
                if not isinstance(row,dict): continue
                try: data[name].extend(normalize_public_links([{'label':row.get('label'),'url':row.get('url')}]))
                except ValidationError: continue
        elif name in ('lat', 'lng'):
            try: value = float(value) if value is not None and value != '' else None
            except (TypeError, ValueError): value = None
            bound = 90 if name == 'lat' else 180
            data[name] = value if value is not None and math.isfinite(value) and abs(value) <= bound else None
        else:
            data[name] = value.strip() if isinstance(value, str) else ''
            if name in ('website','instagram') and '://' in data[name]:
                try:
                    parsed=urlsplit(data[name])
                    if parsed.username or parsed.password:data[name]=''
                except ValueError:data[name]=''
    return data


def _overlay(base, patch):
    patch = patch if isinstance(patch, dict) else {}
    values = identity_fields({**base, **{key: value for key, value in patch.items() if key in FIELDS}})
    if any(name in patch for name in NAMES[:3]):
        values['name'] = next((values[key] for key in NAMES[:3] if values[key]), '')
    return values


def _authorized(actor, place):
    try: publication.authorize(actor, place, 'place')
    except (PermissionDenied, ValidationError): return False
    return True


def identity_registry(actor, *, can_view=None, can_edit=None, exclude_draft_id=None, places=None):
    actor = publication.fresh_actor(actor)
    from catalog.services.business_team import platform_has_action
    from catalog.services.staff_roles import is_volunteer
    publisher = platform_has_action(user=actor, action='place.publish')
    staff_view = actor.is_staff and not is_volunteer(actor) and actor.has_perm('catalog.view_place')
    queryset = Place.objects.all() if places is None else places
    queryset = queryset.select_related('volunteer_revision').annotate(
        _identity_public=Exists(public_place_queryset(Place.objects.filter(pk=OuterRef('pk')))))
    records, by_id = [], {}
    for place in queryset.order_by('pk').iterator():
        if can_view is not None and not can_view(place): continue
        editable = publisher or _authorized(actor, place)
        if not (staff_view or editable or place._identity_public): continue
        if can_edit is not None and not can_edit(place): editable = False
        stored = identity_fields(place)
        record = {'key': f'place:{place.pk}', 'id': place.pk, 'draft_id': None,
                  'status': place.status, 'deleted': place.deleted_at is not None,
                  'is_public': place._identity_public, 'base_content_version': place.content_version,
                  'versions': [{'source':'stored', 'status':place.status,
                                'version':place.content_version, 'stale':False, 'fields':stored}]}
        revision = getattr(place, 'volunteer_revision', None)
        if editable and revision and revision.status in ACTIVE:
            # A stale candidate inherits its historical base where available,
            # never a mixture of new live fields and an old partial proposal.
            stale = revision.base_content_version != place.content_version
            base = _overlay(stored, revision.base_snapshot) if stale else stored
            record['versions'].append({'source':'candidate', 'status':revision.status,
                'version':revision.version, 'base_content_version':revision.base_content_version,
                'stale':stale, 'fields':_overlay(base, revision.payload)})
        records.append(record); by_id[place.pk] = (record, editable)
    for draft in ServerDraft.objects.filter(actor=actor, target_type='place',
            materialized_place__isnull=True).order_by('pk').iterator():
        if str(draft.pk) == str(exclude_draft_id): continue
        if draft.target_id:
            target = by_id.get(draft.target_id)
            if target is None or not target[1] or target[0]['deleted']: continue
            record = target[0]
            base = record['versions'][-1]['fields']
            stale = draft.source_version != record['base_content_version']
        else:
            if places is not None: continue
            record = {'key':f'draft:{draft.pk}', 'id':None, 'draft_id':str(draft.pk),
                      'status':'private_draft', 'deleted':False, 'is_public':False,
                      'base_content_version':None, 'versions':[]}
            records.append(record); base = {}; stale = False
        record['versions'].append({'source':'own_draft', 'status':'private_draft',
            'version':draft.version, 'draft_id':str(draft.pk), 'stale':stale,
            'fields':_overlay(base, draft.fields)})
    snapshot_id=hashlib.sha256(json.dumps(records,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'schema_version':1, 'snapshot_id':snapshot_id, 'export_scope':'duplicate_registry',
        'generated_at':timezone.now().isoformat(), 'coverage':{
            'scope':'accessible_records', 'complete_within_access':True,
            'global_absence_proven':False, 'records_scanned':len(records),
            'stored_versions':sum(any(v['source']=='stored' for v in r['versions']) for r in records),
            'candidate_versions':sum(any(v['source']=='candidate' for v in r['versions']) for r in records),
            'own_private_versions':sum(v['source']=='own_draft' for r in records for v in r['versions']),
            'candidate_access':'authorized_only', 'private_drafts':'actor_only',
            'limitations':['other_actors_private_drafts_excluded', 'object_permissions_applied',
                          'snapshot_requires_recheck_before_creation']}, 'records':records}


def _names(data):
    return {normalize(data.get(key)) for key in NAMES} - {'', normalize('Черновик без названия')}


def _near(a, b):
    if any(p.get(k) is None for p in (a,b) for k in ('lat','lng')): return False
    lat1,lat2 = map(math.radians,(a['lat'],b['lat']))
    delta_lat,delta_lng = lat2-lat1, math.radians(b['lng']-a['lng'])
    h = math.sin(delta_lat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(delta_lng/2)**2
    return 6371000 * 2 * math.asin(min(1, math.sqrt(max(0,h)))) <= 50


def _evidence(query, version):
    data = version['fields']; signals = []; matched_fields=[]
    same_name = bool(_names(query) & _names(data))
    same_address = bool(normalize(query['address']) and normalize(query['address']) == normalize(data['address']))
    different_address = bool(normalize(query['address']) and normalize(data['address']) and not same_address)
    if same_name:
        signals.append('name'); matched_fields.extend(k for k in NAMES if normalize(data[k]) in _names(query))
    if same_address: signals.append('address'); matched_fields.append('address')
    if _near(query,data): signals.append('coordinates'); matched_fields.extend(['lat','lng'])
    q_phones = {phone(query.get(k)) for k in ('phone1','phone2','phone3','whatsapp_number')} - {''}
    d_phones = {phone(data.get(k)) for k in ('phone1','phone2','phone3','whatsapp_number')} - {''}
    if q_phones & d_phones:
        signals.append('phone')
        matched_fields.extend(k for k in ('phone1','phone2','phone3','whatsapp_number') if phone(data[k]) in q_phones)
    def sites(values):
        return {website(values['website']), *[website(row['url']) for row in values['public_links']]} - {''}
    common_sites = sites(query) & sites(data)
    if common_sites:
        signals.append('website')
        if website(data['website']) in common_sites: matched_fields.append('website')
        if any(website(row['url']) in common_sites for row in data['public_links']): matched_fields.append('public_links')
    if instagram(query['instagram']) and instagram(query['instagram']) == instagram(data['instagram']):
        signals.append('instagram'); matched_fields.append('instagram')
    if not signals: return None
    contacts = set(signals) & {'phone','website','instagram'}
    if same_name and (same_address or ('coordinates' in signals and not different_address)):
        classification = 'confirmed'
    elif same_name and different_address: classification = 'possible_branch'
    elif same_name or (same_address and contacts): classification = 'probable'
    elif contacts: classification = 'network_contact'
    elif same_address: classification = 'address_match'
    else: classification = 'nearby'
    if version.get('stale') and classification in ('confirmed','possible_branch'): classification = 'probable'
    return {'source':version['source'], 'version':version['version'], 'signals':signals,
            'classification':classification, 'matched_fields':list(dict.fromkeys(matched_fields)), 'draft_id':version.get('draft_id'), 'stale':version.get('stale',False)}


def check_duplicates(actor, values, *, exclude_place_id=None, exclude_draft_id=None, registry=None):
    snapshot = registry if registry is not None else identity_registry(actor,exclude_draft_id=exclude_draft_id)
    source = dict(values) if isinstance(values, dict) else identity_fields(values)
    if source.get('phone'): source['phone1'] = source['phone']
    query = identity_fields(source)
    results = []
    for record in snapshot['records']:
        if record['id'] is not None and str(record['id']) == str(exclude_place_id): continue
        evidence = [e for v in record['versions'] if (e := _evidence(query,v))]
        if not evidence: continue
        evidence.sort(key=lambda e:RANK[e['classification']])
        best = evidence[0]
        best_version = next(v for v in record['versions'] if v['source']==best['source'] and v['version']==best['version'] and v.get('draft_id')==best.get('draft_id'))
        results.append({**record, 'classification':best['classification'], 'evidence':evidence,
            'matched':list(dict.fromkeys(s for e in evidence for s in e['signals'])),
            'match_fields':best_version['fields'], 'branch_override_allowed':
                any(e['classification']=='possible_branch' for e in evidence) and
                not any(e['classification']=='confirmed' or e['stale'] or
                    (e['classification']=='probable' and (e['source']!='stored' or record['is_public'] or
                        record['status']!='draft' or set(e['signals'])!={'name'})) for e in evidence)})
    results.sort(key=lambda r:(RANK[r['classification']], r['key']))
    return {'schema_version':1, 'generated_at':snapshot['generated_at'], 'coverage':snapshot['coverage'],
            'decision':results[0]['classification'] if results else 'not_found_within_access',
            'total':len(results), 'results':results}


def guard_new_place(actor, candidate, *, exclude_draft_id=None, distinct_branch=False, can_view=None, can_edit=None):
    """Caller owns the transaction: lock before any model/file creation."""
    if not connection.in_atomic_block: raise RuntimeError('Duplicate guard requires a transaction.')
    if connection.vendor == 'postgresql':
        with connection.cursor() as cursor: cursor.execute('SELECT pg_advisory_xact_lock(%s,%s)', [1042026,2901])
    registry=identity_registry(actor,exclude_draft_id=exclude_draft_id,can_view=can_view,can_edit=can_edit)
    result = check_duplicates(actor,candidate,registry=registry)
    blocked = next((row for row in result['results'] if row['classification'] in ('confirmed','probable','possible_branch')
                    and not (distinct_branch and row['branch_override_allowed'])),None)
    if blocked:
        reference = f"#{blocked['id']}" if blocked['id'] is not None else t('ваш личный черновик','şəxsi qaralamanız','your private draft')
        message = t('Возможный дубль: %(reference)s. Сравните обе версии. Для отдельного филиала укажите другой адрес и подтвердите создание филиала.',
            'Mümkün dublikat: %(reference)s. Hər iki versiyanı müqayisə edin. Ayrıca filial üçün başqa ünvan göstərin və filialı təsdiqləyin.',
            'Possible duplicate: %(reference)s. Compare both versions. For a separate branch provide a different address and confirm branch creation.') % {'reference':reference}
        error = ValidationError(message,code='place_identity_duplicate')
        error.identity_result = blocked
        raise error
    return result
