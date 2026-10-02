"""Conservative stage-11 planner: preserve existing IDs and queue unverified links."""
import hashlib
import json
import os
from pathlib import Path

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, transaction, models

from catalog.models import ConversionMapping, ConversionRun, Place, PricingPlan, PlacePhoto, PlaceLike, PlaceReview, PlaceReviewReaction

RULE_VERSION = 1
SOURCES = {'place': Place, 'pricing_plan': PricingPlan}


def _digest(value):
    return hashlib.sha256(json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def _fingerprint(instance):
    fields = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname)
        fields[field.attname] = value.name if isinstance(field, models.FileField) else value
    return _digest(fields)


def _piece(source, key, reason, target_type='', target_id=None):
    return {'source_type': 'pricing_plan' if isinstance(source, PricingPlan) else 'place', 'source_id': source.pk, 'rule_version': RULE_VERSION,
            'piece_key': key, 'source_version': getattr(source, 'content_version', None),
            'source_fingerprint': _fingerprint(source), 'target_type': target_type,
            'target_id': target_id, 'reason_code': reason}


def _retained_counts():
    return {'places': Place.objects.count(), 'pricing_plans': PricingPlan.objects.count(),
            'photos': PlacePhoto.objects.count(), 'favorites': PlaceLike.objects.count(),
            'reviews': PlaceReview.objects.count(), 'reactions': PlaceReviewReaction.objects.count()}


def _require_isolated_database():
    """Fail closed before even opening a connection to a non-QA04 database."""
    root_value = os.environ.get('TASK33_QA_ROOT', '')
    host_value = os.environ.get('TASK33_QA_SOCKET', '')
    if not settings.TESTING or os.environ.get('DJANGO_SETTINGS_MODULE') != 'settings':
        raise RuntimeError('Task 33 conversion requires QA04 isolated settings')
    if any(os.environ.get(name) for name in ('DATABASE_URL', 'LEGACY_DATABASE_URL', 'REDIS_URL')):
        raise RuntimeError('External database/cache URLs are forbidden')
    if not root_value or not host_value:
        raise RuntimeError('QA04 isolation markers are required')
    root = Path(root_value)
    host = Path(host_value)
    repo_tmp = Path(__file__).resolve().parents[3] / '.tmp'
    if (root.is_symlink() or not root.resolve().as_posix().startswith('/tmp/kidsmap-task33-qa04-')
            or host.is_symlink() or host.parent.is_symlink() or host.name != 'socket'
            or not host.parent.name.startswith('kidsmap-task33-qa04-socket-')
            or host.parent.parent.resolve() != repo_tmp.resolve()):
        raise RuntimeError('Unexpected QA04 scratch or socket path')
    db = settings.DATABASES
    if set(db) != {'default'}:
        raise RuntimeError('Additional DB aliases forbidden')
    target = db['default']
    if (target.get('ENGINE') != 'django.db.backends.postgresql'
            or target.get('NAME') not in {'qa_stage04', 'test_qa_stage04'}
            or target.get('USER') != 'qa_stage04'
            or target.get('HOST') != str(host)
            or target.get('TEST', {}).get('NAME') != 'test_qa_stage04'
            or connection.settings_dict.get('NAME') not in {'qa_stage04', 'test_qa_stage04'}):
        raise RuntimeError('Conversion database is not the QA04 disposable PostgreSQL target')


def build_plan():
    """Strictly read-only DB transaction; no model save, signal, or ledger write."""
    _require_isolated_database()
    with transaction.atomic():
        if connection.vendor != 'postgresql':
            raise RuntimeError('Conversion planning requires isolated PostgreSQL')
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout = '15s'")
        entries = []
        places_with_plans = set(PricingPlan.objects.exclude(place_id=None).values_list('place_id', flat=True))
        for place in Place.objects.order_by('pk').iterator(chunk_size=200):
            entries.append(_piece(place, 'identity', 'same_place_id', 'place', place.pk))
            if place.organization_id is None:
                entries.append(_piece(place, 'organization', 'organization_unconfirmed'))
            if place.pk not in places_with_plans and (place.pricing_plans_legacy or any(
                    getattr(place, name) is not None for name in ('price_from', 'price_to', 'price_per_lesson', 'price_per_month', 'price_per_8_lessons'))):
                entries.append(_piece(place, 'legacy_pricing', 'legacy_price_requires_classification'))
        for plan in PricingPlan.objects.order_by('pk').iterator(chunk_size=200):
            entries.append(_piece(plan, 'identity', 'same_plan_id', 'pricing_plan', plan.pk))
            if plan.place_id is not None:
                entries.append(_piece(plan, 'group_assignment', 'group_unconfirmed'))
        baseline_counts = _retained_counts()
    payload = {'schema_version': 1, 'rule_version': RULE_VERSION, 'baseline_counts': baseline_counts, 'entries': entries}
    return {**payload, 'digest': _digest(payload)}


def _validate(plan):
    if plan.get('schema_version') != 1 or plan.get('rule_version') != RULE_VERSION:
        raise ValueError('Unsupported conversion plan version')
    payload = {key: plan[key] for key in ('schema_version', 'rule_version', 'baseline_counts', 'entries')}
    if plan.get('digest') != _digest(payload):
        raise ValueError('Conversion plan digest mismatch')
    keys = [(e['source_type'], e['source_id'], e['rule_version'], e['piece_key']) for e in plan['entries']]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate conversion piece')
    manual_reasons = {('place', 'organization'): 'organization_unconfirmed',
                      ('place', 'legacy_pricing'): 'legacy_price_requires_classification',
                      ('pricing_plan', 'group_assignment'): 'group_unconfirmed'}
    for entry in plan['entries']:
        kind = entry['source_type']
        piece = entry['piece_key']
        source_id = entry['source_id']
        if kind not in SOURCES or entry['rule_version'] != RULE_VERSION or not isinstance(source_id, int) or source_id < 1:
            raise ValueError('Invalid conversion source')
        if piece == 'identity':
            if (entry['target_type'], entry['target_id'], entry['reason_code']) != (kind, source_id, f'same_{"plan" if kind == "pricing_plan" else "place"}_id'):
                raise ValueError('Identity target must retain its source ID')
        elif (kind, piece) not in manual_reasons or entry['target_type'] or entry['target_id'] is not None or entry['reason_code'] != manual_reasons[(kind, piece)]:
            raise ValueError('Unrecognized conversion piece or target')


def apply_plan(plan, *, batch_size=50, max_batches=None):
    _require_isolated_database()
    _validate(plan)
    if not 1 <= batch_size <= 500:
        raise ValueError('batch_size must be 1..500')
    stale = 0
    batches = 0
    while True:
        with transaction.atomic():
            run, _ = ConversionRun.objects.get_or_create(plan_digest=plan['digest'], defaults={
                'rule_version': RULE_VERSION, 'entry_count': len(plan['entries']), 'baseline_counts': plan['baseline_counts']})
            run = ConversionRun.objects.select_for_update().get(pk=run.pk)
            if run.entry_count != len(plan['entries']) or run.rule_version != RULE_VERSION or run.baseline_counts != plan['baseline_counts']:
                raise ValueError('Conversion run metadata mismatch')
            start = run.checkpoint
            if start >= len(plan['entries']):
                break
            for entry in plan['entries'][start:start + batch_size]:
                source = SOURCES[entry['source_type']].objects.select_for_update().filter(pk=entry['source_id']).first()
                current = _fingerprint(source) if source else None
                changed = current != entry['source_fingerprint']
                if changed:
                    stale += 1
                state = 'manual_review' if changed or not entry['target_type'] else 'applied'
                reason = 'changed_source' if changed else entry['reason_code']
                key = {name: entry[name] for name in ('source_type', 'source_id', 'rule_version', 'piece_key')}
                defaults = {name: entry[name] for name in ('source_version', 'source_fingerprint', 'target_type', 'target_id')}
                defaults.update(state=state, reason_code=reason, run=run)
                if changed:
                    defaults.update(target_type='', target_id=None)
                existing = ConversionMapping.objects.select_for_update().filter(**key).first()
                if existing and existing.source_fingerprint != entry['source_fingerprint'] and changed:
                    continue
                if existing:
                    for name, value in defaults.items():
                        setattr(existing, name, value)
                    existing.save(update_fields=[*defaults, 'updated_at'])
                else:
                    ConversionMapping.objects.create(**key, **defaults)
            run.checkpoint = min(start + batch_size, len(plan['entries']))
            run.save(update_fields=['checkpoint', 'updated_at'])
        batches += 1
        if max_batches is not None and batches >= max_batches:
            break
    return {'digest': plan['digest'], 'checkpoint': run.checkpoint, 'entry_count': run.entry_count,
            'stale': stale, 'batches': batches, 'reconciliation': reconciliation(plan['digest'])}


def reconciliation(digest):
    from django.db.models import Count
    run = ConversionRun.objects.get(plan_digest=digest)
    mappings = ConversionMapping.objects.filter(run=run)
    grouped = {f"{item['state']}:{item['reason_code']}": item['total'] for item in
               mappings.values('state', 'reason_code').annotate(total=Count('pk'))}
    retained = _retained_counts()
    return {'retained': retained, 'retained_counts_match': retained == run.baseline_counts,
            'mapping_total': mappings.count(), 'applied': mappings.filter(state='applied').count(),
            'manual_review': mappings.filter(state='manual_review').count(), 'by_reason': grouped,
            'checkpoint': run.checkpoint, 'entry_count': run.entry_count}
