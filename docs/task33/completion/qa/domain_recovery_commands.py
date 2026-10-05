"""Synthetic conversion and native restore in a single QA04-owned PostgreSQL container."""
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('qa04_commands', HERE.parent.parent / 'qa04' / 'commands.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
dump = base.dump
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parent.parent / 'qa23'))
from container_guard import find_owned_container


def checked(args, *, data=None):
    result = subprocess.run(args, input=data, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('Native QA23 command failed: ' + args[0] + ' ' + args[1])
    return result.stdout


def table_digest(container, database, table):
    # Fixed ORM table names, never untrusted input. Only count/digest leave PostgreSQL.
    if not table.replace('_', '').isalnum():
        raise RuntimeError('Unexpected digest table')
    query = f'SELECT count(*), md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text)::text,\'[]\')) FROM "{table}" t'
    output = checked(['docker', 'exec', container, 'psql', '-h', '/qa-socket', '-U', 'qa_stage04',
                      '-d', database, '-At', '-F', '|', '-c', query]).decode().strip()
    count, digest = output.split('|', 1)
    return {'count': int(count), 'sha256_of_digest': hashlib.sha256(digest.encode()).hexdigest()}


def inventory(container, database, models):
    return {model.__name__: table_digest(container, database, model._meta.db_table) for model in models}


def all_r1_tables(container, database):
    query = "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    output = checked(['docker', 'exec', container, 'psql', '-h', '/qa-socket', '-U', 'qa_stage04',
                      '-d', database, '-At', '-c', query]).decode()
    return [name for name in output.splitlines() if name]


def database_digest_inventory(container, database, tables):
    return {table: table_digest(container, database, table) for table in tables}


def media_inventory(media_root):
    root = Path(media_root)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob('*') if path.is_file()}


def canonical_schema(data):
    """Canonicalize only PostgreSQL's equivalent constant varchar-array casts.

    pg_dump/restore reparses ARRAY[varchar constants]::text[] as an array of
    individually text-cast constants. Preserve every value, order and all other
    SQL syntax; do not discard constraints, predicates or index attributes.
    """
    literal = r"'(?:[^']|'')*'::character varying"
    pattern = re.compile(r"\(\(ARRAY\[(" + literal + r"(?:, " + literal + r")*)\]\)::text\[\]\)")
    def replace(match):
        values = re.findall(literal, match.group(1))
        return "(ARRAY[" + ", ".join("(" + value + ")::text" for value in values) + "])"
    result = json.loads(json.dumps(data))
    for section, field in (('constraints', 'definition'), ('indexes', 'indexdef')):
        for row in result[section]:
            row[field] = pattern.sub(replace, row[field])
    return result


def schema_signature(container,database):
    """Compare structural metadata without OIDs or database-specific physical names."""
    query="""WITH columns AS (
        SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod) AS type,
            a.attnotnull,pg_get_expr(d.adbin,d.adrelid) AS default_expression
        FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
        JOIN pg_attribute a ON a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
        LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum
        WHERE n.nspname='public' AND c.relkind='r'),
      constraints AS (
        SELECT c.relname,k.conname,k.contype,k.condeferrable,k.condeferred,
            pg_get_constraintdef(k.oid) AS definition
        FROM pg_constraint k JOIN pg_class c ON c.oid=k.conrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public'),
      indexes AS (SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public')
      SELECT jsonb_build_object(
        'columns',(SELECT jsonb_agg(to_jsonb(x) ORDER BY relname,attname) FROM columns x),
        'constraints',(SELECT jsonb_agg(to_jsonb(x) ORDER BY relname,conname) FROM constraints x),
        'indexes',(SELECT jsonb_agg(to_jsonb(x) ORDER BY tablename,indexname) FROM indexes x))"""
    raw=checked(['docker','exec',container,'psql','-h','/qa-socket','-U','qa_stage04',
        '-d',database,'-At','-c',query])
    data=json.loads(raw)
    base.dump('schema-'+database+'.json',data)
    data=canonical_schema(data)
    return {'sha256':hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        'columns':len(data['columns']),'constraints':len(data['constraints']),'indexes':len(data['indexes'])}


def compatible_standby_read(media_copy):
    metadata_path = Path(os.environ.get('TASK33_R1_ARTIFACT_JSON', ''))
    if not metadata_path.is_file():
        return {'status': 'NOT_RUN', 'reason': 'exact compatible local artifact not frozen'}
    from artifact import digest, verify
    metadata = json.loads(metadata_path.read_text())
    standby = Path(metadata['standby'])
    if not str(standby).startswith('/root/km28-release') or standby.is_symlink() or not standby.is_dir():
        raise RuntimeError('Unsafe compatible standby path')
    if metadata.get('identity') != 'r2-local-sha256-' + metadata['identity'].removeprefix('r2-local-sha256-'):
        raise RuntimeError('Invalid compatible artifact identity')
    archive = Path(metadata['archive'])
    manifest_path = metadata_path.parent / 'manifest.json'
    if (not archive.is_file() or not manifest_path.is_file() or digest(archive.read_bytes()) != metadata['archive_sha256']
            or digest(manifest_path.read_bytes()) != metadata['manifest_sha256']):
        raise RuntimeError('Compatible archive digest mismatch')
    manifest = json.loads(manifest_path.read_text())
    canonical = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()
    if metadata['identity'] != 'r2-local-sha256-' + digest(canonical):
        raise RuntimeError('Compatible manifest identity mismatch')
    runtime_dependencies = sorted({(d.metadata['Name'], d.version) for d in importlib.metadata.distributions()})
    if (manifest.get('python') != platform.python_version()
            or manifest.get('python_executable_sha256') != digest(Path(sys.executable).resolve().read_bytes())
            or manifest.get('dependencies') != [list(item) for item in runtime_dependencies]):
        raise RuntimeError('Compatible interpreter or dependency inventory differs')
    verify(standby, manifest)
    # The QA reader is an explicit external input, not replacement APP code.
    # Verify the entire frozen application before and after its read-only run.
    reader = HERE / 'domain_recovery_reader.py'
    if not reader.is_file():
        raise RuntimeError('Compatible reader absent from frozen artifact')
    environment = dict(os.environ)
    environment['PYTHONPATH'] = str(standby / 'docs/task33/qa04') + os.pathsep + str(standby / 'src')
    environment['TASK33_R1_RESTORE_DB'] = 'qa_completion_restore'
    environment['TASK33_R1_MEDIA_COPY'] = str(media_copy)
    environment['TASK33_R1_WRITE_MODE'] = 'off'
    environment['TASK33_R1_WRITE_USER_IDS'] = ''
    environment['TASK33_R2_PRIVATE_COPY'] = str(media_copy.parent / 'r2-private-media')
    environment['TASK33_COMPLETION_VERIFIED_STANDBY'] = str(standby)
    completed = subprocess.run([sys.executable, str(reader)], cwd=standby, env=environment,
                               capture_output=True, text=True, check=False, timeout=60)
    if completed.returncode:
        (base.OUTPUT / 'standby-reader-error.log').write_text(completed.stderr)
        raise RuntimeError('Frozen compatible reader failed')
    verify(standby, manifest)
    result = json.loads(completed.stdout)
    if result.get('status') != 'PASS' or result.get('database') != 'qa_completion_restore':
        raise RuntimeError('Frozen compatible reader did not verify restore')
    if result.get('media_bytes_sha256') not in media_inventory(media_copy).values():
        raise RuntimeError('Frozen reader media bytes differ from copied media')
    return {'status': 'PASS', 'artifact_identity': metadata['identity'], 'verified_files': len(manifest['files']),
            'external_read_only_qa_reader': True, 'qa_reader_sha256': digest(reader.read_bytes()),
            'application_verified_before_and_after': True,
            'read_only_database': result['database'], 'unix_socket': result['unix_socket'],
            'post_switch_place': result['post_switch_place'], 'media_bytes_sha256': result['media_bytes_sha256'],
            'standalone_taxonomy':result['standalone_taxonomy'],
            'linked_approved_subcategory':result['linked_approved_subcategory'],
            'detached_taxonomy_copy':result['detached_taxonomy_copy'],
            'exact_taxonomy_search':result['exact_taxonomy_search']}


def main(mode, labels):
    if mode != 'probe' or labels:
        raise RuntimeError('QA23 native rehearsal requires probe mode without labels')
    code = base.main(mode, labels)
    if code:
        return code
    from django.contrib.auth import get_user_model
    from django.test import Client, override_settings
    from django.urls import reverse
    from django.conf import settings
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.utils import timezone
    from unittest.mock import patch
    from io import BytesIO
    from PIL import Image
    from catalog.models import (Place, PricingPlan, PlacePhoto, PlaceLike, PlaceReview,
                                Organization, Program, Activity, OfferingGroup,
                                PlaceReviewRevision, PlaceReviewReaction, ConversionRun, ConversionMapping)
    from catalog.services.catalog_conversion import build_plan, apply_plan, reconciliation
    from catalog.services.organization_ownership import request_join
    from catalog.testcases.utils import create_quality_place

    container = find_owned_container(os.environ['TASK33_QA_SOCKET'])
    models = (Place, PricingPlan, PlacePhoto, PlaceLike, PlaceReview, PlaceReviewRevision, PlaceReviewReaction)
    before = inventory(container, 'qa_stage04', models)
    media_before = media_inventory(settings.MEDIA_ROOT)
    if ConversionRun.objects.exists() or ConversionMapping.objects.exists():
        raise RuntimeError('Rehearsal requires empty conversion ledger')
    dry_tables = all_r1_tables(container, 'qa_stage04')
    dry_all_before = database_digest_inventory(container, 'qa_stage04', dry_tables)
    plan = build_plan()
    if database_digest_inventory(container, 'qa_stage04', dry_tables) != dry_all_before:
        raise RuntimeError('Dry-run changed any persisted table')
    if inventory(container, 'qa_stage04', models) != before:
        raise RuntimeError('Dry-run changed source rows')
    real_create = ConversionMapping.objects.create
    calls = 0
    def interrupt_second_piece(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError('Synthetic mid-batch interruption')
        return real_create(**kwargs)
    with patch.object(ConversionMapping.objects, 'create', side_effect=interrupt_second_piece):
        try:
            apply_plan(plan, batch_size=2)
        except RuntimeError as exc:
            if str(exc) != 'Synthetic mid-batch interruption':
                raise
        else:
            raise RuntimeError('Mid-batch interruption did not fire')
    if ConversionRun.objects.exists() or ConversionMapping.objects.exists():
        raise RuntimeError('Failed batch left partial ledger writes')
    part = apply_plan(plan, batch_size=1, max_batches=1)
    if part['checkpoint'] != 1:
        raise RuntimeError('Interrupted checkpoint mismatch')
    complete = apply_plan(plan, batch_size=1)
    rerun = apply_plan(plan, batch_size=1)
    if complete['checkpoint'] != len(plan['entries']) or rerun['checkpoint'] != len(plan['entries']):
        raise RuntimeError('Incomplete conversion ledger')
    if reconciliation(plan['digest'])['mapping_total'] != len(plan['entries']):
        raise RuntimeError('Duplicate/missing conversion pieces')
    if inventory(container, 'qa_stage04', models) != before:
        raise RuntimeError('Conversion modified source rows')
    if media_inventory(settings.MEDIA_ROOT) != media_before:
        raise RuntimeError('Conversion modified media bytes')

    # Post-switch write remains in the live disposable source DB. The dump is
    # taken *after* this write, then restored into a second disposable DB.
    actor = get_user_model().objects.create_user('qa23_post_switch', email='qa23-post@example.invalid')
    new = create_quality_place(owner=actor, created_by=actor, name='QA23 post-switch',
                               name_az='Sınaqdan sonrakı məkan', with_subcategory=True)
    PricingPlan.objects.create(place=new, product_type='lesson', price='29')
    post_org = Organization.objects.create(owner=actor, created_by=actor, name_az='Sonrakı təşkilat',
                                           status='published', approved_at=timezone.now())
    request_join(actor=actor, place_id=new.pk, organization_id=post_org.pk)
    post_program = Program.objects.create(organization=post_org, created_by=actor,
        category_id=new.category_id, subcategory_id=new.subcategory_id,
        name_az='Təsdiqlənmiş proqram', description_az='Sintetik təsdiqlənmiş proqram',
        status='published', approved_at=timezone.now())
    post_activity = Activity.objects.create(place=new, program=post_program, status='published')
    post_group = OfferingGroup.objects.create(activity=post_activity, name_az='Sonrakı qrup', age_from=5, age_to=9)
    PricingPlan.objects.create(offering_group=post_group, product_type='lesson', price='19', age_from=5, age_to=9)
    post_program.name_az = 'Gözləyən yeni versiya'
    post_program.status = 'pending'
    post_program.save()
    post_activity.refresh_from_db()
    if post_activity.program_snapshot.get('name_az') != 'Təsdiqlənmiş proqram':
        raise RuntimeError('Approved publication snapshot was overwritten')
    post_review = PlaceReview.objects.create(place=new, user=actor, rating=5,
                                             text='Sintetik sonrakı rəy', status='approved')
    voter = get_user_model().objects.create_user('qa23_post_voter', email='qa23-voter@example.invalid')
    PlaceReviewReaction.objects.create(review=post_review, user=voter, value=1)
    pixel = BytesIO()
    Image.new('RGB', (16, 16), '#a3c991').save(pixel, format='JPEG')
    PlacePhoto.objects.create(place=new, image=SimpleUploadedFile('qa23-post-switch.jpg', pixel.getvalue(), content_type='image/jpeg'))
    post_switch = inventory(container, 'qa_stage04', models)
    media_post_switch = media_inventory(settings.MEDIA_ROOT)
    if not Place.objects.filter(pk=new.pk).exists() or reconciliation(plan['digest'])['retained_counts_match']:
        raise RuntimeError('Post-switch record or drift signal missing')
    with override_settings(TASK33_R1_WRITE_MODE='off'):
        client = Client()
        client.force_login(actor)
        reader = client.get(new.get_absolute_url())
        paused_writer = client.post(reverse('typed_reviews', args=['place', new.pk]), {})
        if reader.status_code != 200 or paused_writer.status_code != 503:
            raise RuntimeError('Paused cohort hid a reader or allowed an HTTP write')
    if inventory(container, 'qa_stage04', models) != post_switch:
        raise RuntimeError('Paused cohort changed persisted post-switch rows')
    from domain_recovery_fixtures import add_r2_records, performance
    r2 = add_r2_records(actor, new, post_org)
    performance_result = performance()
    private_root = Path(settings.PRIVATE_MEDIA_ROOT)
    private_before = media_inventory(private_root)
    if len(private_before) < 2: raise RuntimeError('Missing private fixture bytes')
    tables = all_r1_tables(container, 'qa_stage04')
    all_post_switch = database_digest_inventory(container, 'qa_stage04', tables)
    schema_before=schema_signature(container,'qa_stage04')
    dump = checked(['docker', 'exec', container, 'pg_dump', '-h', '/qa-socket', '-U', 'qa_stage04',
                    '-d', 'qa_stage04', '-Fc', '--no-owner', '--no-acl'])
    if len(dump) < 1024:
        raise RuntimeError('Unexpectedly small PostgreSQL dump')
    dump_file = base.OUTPUT / 'r2-post-switch.dump'
    with dump_file.open('xb') as stream:
        stream.write(dump)
    media_copy = base.OUTPUT / 'r2-post-switch-media'
    shutil.copytree(settings.MEDIA_ROOT, media_copy, symlinks=False)
    if media_inventory(media_copy) != media_post_switch:
        raise RuntimeError('Media copy failed byte-level verification')
    private_copy = base.OUTPUT / 'r2-private-media'
    shutil.copytree(private_root, private_copy, symlinks=False)
    if media_inventory(private_copy) != private_before: raise RuntimeError('Private byte copy mismatch')
    checked(['docker', 'exec', container, 'createdb', '-h', '/qa-socket', '-U', 'qa_stage04', 'qa_completion_restore'])
    checked(['docker', 'exec', '-i', container, 'pg_restore', '-h', '/qa-socket', '-U', 'qa_stage04',
             '-d', 'qa_completion_restore', '--no-owner', '--no-acl'], data=dump)
    restored_tables = all_r1_tables(container, 'qa_completion_restore')
    restored = database_digest_inventory(container, 'qa_completion_restore', restored_tables)
    source_after_restore = database_digest_inventory(container, 'qa_stage04', tables)
    schema_restored=schema_signature(container,'qa_completion_restore')
    if schema_before!=schema_restored or schema_signature(container,'qa_stage04')!=schema_before:
        raise RuntimeError('Restored source/schema signatures differ')
    if restored_tables != tables or restored != all_post_switch or source_after_restore != all_post_switch:
        raise RuntimeError('Restore lost or changed pre/post-switch records')
    standby_result = compatible_standby_read(media_copy)
    base.dump('r2-rehearsal.json', {
        'status': 'PASS', 'fixture': 'synthetic-only', 'container_owned': True,
        'network_none_tmpfs_socket': True, 'source_digest_preserved': True,
        'dry_run_read_only': True, 'partial_checkpoint': part['checkpoint'],
        'forced_mid_batch_rollback': True,
        'completed_entries': len(plan['entries']), 'rerun_duplicate_pieces': False,
        'post_switch_record_present': True, 'post_switch_count_drift_detected': True,
        'post_switch_program_approved_snapshot_retained': True,
        'post_switch_review_reaction_created': True,
        'off_mode_public_reader_status': reader.status_code,
        'off_mode_http_write_status': paused_writer.status_code,
        'off_mode_preserves_rows': True,
        'native_dump_bytes': len(dump), 'native_pg_restore': 'PASS',
        'source_and_restore_row_digests_equal': True,
        'source_and_restored_schema_signature_equal':True,'schema_signature':schema_before,
        'compatible_standby_read': standby_result,
        'r2_records': r2, 'performance': performance_result,
        'private_files_compared': len(private_before), 'private_media_digests_equal': True,
        'tables_compared_count': len(tables), 'raw_dump': str(dump_file),
        'media_files_compared': len(media_post_switch), 'media_byte_digests_equal': True,
        'source_counts': {name: value['count'] for name, value in post_switch.items()},
    })
    return 0
