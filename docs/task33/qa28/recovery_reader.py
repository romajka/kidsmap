"""Read the restored QA23 database with the frozen compatible application code."""
import hashlib
import json
import os
import socket as socket_module
from pathlib import Path


def install_restored_db_guards(socket):
    """Guard this fresh process, which does not inherit QA04's Python patches."""
    socket = socket.resolve()
    original_connect = socket_module.socket.connect
    original_connect_ex = socket_module.socket.connect_ex
    def only_socket(sock, address):
        if (sock.family != socket_module.AF_UNIX or not isinstance(address, str)
                or not Path(address).resolve().is_relative_to(socket)):
            raise RuntimeError('Compatible reader foreign socket denied')
    def guarded_connect(sock, address):
        only_socket(sock, address)
        return original_connect(sock, address)
    def guarded_connect_ex(sock, address):
        only_socket(sock, address)
        return original_connect_ex(sock, address)
    socket_module.socket.connect = guarded_connect
    socket_module.socket.connect_ex = guarded_connect_ex

    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    original_pg = psycopg.Connection.connect
    def guarded_pg(cls, conninfo='', **kwargs):
        connection_kwargs = {key: value for key, value in kwargs.items()
                             if key not in {'autocommit', 'prepare_threshold', 'context', 'row_factory', 'cursor_factory'}}
        target = conninfo_to_dict(conninfo, **connection_kwargs)
        if (target.get('host') != str(socket) or target.get('hostaddr') or target.get('service')
                or target.get('dbname') != 'qa_stage28_restore' or target.get('user') != 'qa_stage04'):
            raise RuntimeError('Compatible reader foreign libpq target denied')
        return original_pg(conninfo, **kwargs)
    psycopg.Connection.connect = classmethod(guarded_pg)
    psycopg.connect = psycopg.Connection.connect


def main():
    if os.environ.get('DJANGO_TESTING') != '1' or os.environ.get('DJANGO_SETTINGS_MODULE') != 'settings':
        raise RuntimeError('Only QA04 settings may read the restored database')
    if any(os.environ.get(name) for name in ('DATABASE_URL', 'LEGACY_DATABASE_URL', 'REDIS_URL')):
        raise RuntimeError('External endpoints forbidden')
    socket = Path(os.environ.get('TASK33_QA_SOCKET', ''))
    if socket.name != 'socket' or not socket.parent.name.startswith('kidsmap-task33-qa04-socket-') or socket.is_symlink():
        raise RuntimeError('Foreign PostgreSQL socket forbidden')
    if os.environ.get('TASK33_R1_RESTORE_DB') != 'qa_stage28_restore':
        raise RuntimeError('Foreign restore database forbidden')
    media = Path(os.environ.get('TASK33_R1_MEDIA_COPY', ''))
    output = Path(os.environ.get('TASK33_QA_OUTPUT', ''))
    if (not str(media).startswith(str(output) + '/') or media.is_symlink() or not media.is_dir()
            or any(path.is_symlink() for path in media.rglob('*'))):
        raise RuntimeError('Foreign media copy forbidden')
    from django.conf import settings
    if settings.DATABASES['default']['HOST'] != str(socket) or settings.DATABASES['default']['NAME'] != 'qa_stage04':
        raise RuntimeError('QA04 base database settings changed')
    if (set(settings.DATABASES) != {'default'} or settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql'
            or settings.DATABASES['default']['USER'] != 'qa_stage04'
            or set(settings.CACHES) != {'default'}
            or settings.CACHES['default']['BACKEND'] != 'django.core.cache.backends.locmem.LocMemCache'
            or settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend'
            or not settings.TESTING or settings.TASK33_R1_WRITE_MODE != 'off'
            or settings.TASK33_R1_WRITE_USER_IDS):
        raise RuntimeError('Compatible reader settings are not isolated')
    settings.DATABASES['default']['NAME'] = 'qa_stage28_restore'
    settings.MEDIA_ROOT = media
    private = Path(os.environ['TASK33_R2_PRIVATE_COPY'])
    if not private.resolve().is_relative_to(output.resolve()) or private.is_symlink(): raise RuntimeError('Unsafe private copy')
    settings.PRIVATE_MEDIA_ROOT = private
    install_restored_db_guards(socket)
    import django
    django.setup()
    import catalog
    standby_root = Path(__file__).resolve().parents[3]
    if not Path(catalog.__file__).resolve().is_relative_to(standby_root / 'src'):
        raise RuntimeError('Compatible reader did not import frozen application source')
    from django.contrib.auth.models import AnonymousUser
    from catalog.services.r1_cohort import r1_writes_enabled
    if r1_writes_enabled(AnonymousUser()):
        raise RuntimeError('Compatible standby must keep HTTP writes off')
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute('BEGIN READ ONLY')
        cursor.execute("SET LOCAL statement_timeout = '20s'")
        cursor.execute('SELECT current_database(), inet_server_addr() IS NULL')
        database, unix = cursor.fetchone()
        if database != 'qa_stage28_restore' or not unix:
            raise RuntimeError('Restored database connection mismatch')
        from catalog.models import Place, PricingPlan, PlacePhoto, PlaceReview, PlaceReviewReaction, Activity
        place = Place.objects.get(name_az='Sınaqdan sonrakı məkan')
        activity = Activity.objects.get(place=place)
        if (place.status != 'published' or activity.program_snapshot.get('name_az') != 'Təsdiqlənmiş proqram'
                or PricingPlan.objects.filter(place=place).count() != 1
                or PricingPlan.objects.filter(offering_group__activity=activity).count() != 1):
            raise RuntimeError('Compatible reader lost publication or price rows')
        review = PlaceReview.objects.get(place=place)
        if (review.current_revision_id is None or review.status != 'approved'
                or PlaceReviewReaction.objects.filter(review=review, revision_id=review.current_revision_id).count() != 1):
            raise RuntimeError('Compatible reader lost review/reaction')
        photo = PlacePhoto.objects.get(place=place)
        relative = Path(photo.image.name)
        if relative.is_absolute() or '..' in relative.parts:
            raise RuntimeError('Unsafe restored media path')
        file = media / relative
        if not file.is_file() or not file.resolve().is_relative_to(media.resolve()):
            raise RuntimeError('Compatible reader lost media bytes')
        media_hash = hashlib.sha256(file.read_bytes()).hexdigest()
        from django.utils.translation import override
        with override('az'):
            az_url = place.get_absolute_url()
        with override('ru'):
            ru_url = place.get_absolute_url()
        if not az_url or not ru_url or az_url == ru_url:
            raise RuntimeError('Compatible reader lost localized URL')
        from django.test import Client
        from django.urls import reverse
        public_read = Client().get(az_url)
        paused_write = Client().post(reverse('typed_reviews', args=['place', place.pk]), {})
        if public_read.status_code != 200 or paused_write.status_code != 503:
            raise RuntimeError('Frozen compatible standby did not read or pause HTTP writes')
        from catalog.models import Specialist, SpecialistClaim, SpecialistEmployment, SpecialistDocument, Event, EmailOutbox
        from catalog.services.specialist_documents import is_public_document
        person = Specialist.objects.get(name='QA28 post-switch person')
        if SpecialistClaim.objects.filter(specialist=person,status='approved').count()!=1: raise RuntimeError('Claim lost')
        employment=SpecialistEmployment.objects.get(specialist=person)
        if employment.status!='active' or employment.history.count()!=3: raise RuntimeError('Employment history lost')
        if person.practice_locations.count()!=2: raise RuntimeError('Practice history lost')
        docs=list(SpecialistDocument.objects.filter(specialist=person).order_by('document_type'))
        for doc in docs:
            if not Path(doc.file.path).is_file(): raise RuntimeError('Private file lost')
            expected=200 if is_public_document(doc) else 404
            response=Client().get(reverse('serve_specialist_document',args=[doc.pk]))
            if response.status_code!=expected: raise RuntimeError('Restored document ACL differs')
            # Close only the owned file resource. HttpResponse.close emits
            # request_finished and closes the connection holding our readonly
            # verification transaction; the private-media TestCase uses the
            # same bounded resource-close pattern.
            if response.streaming:
                for closer in response._resource_closers:
                    closer()
        event=Event.objects.get(name_az='QA28 post-switch event')
        if event.occurrence_changes.count()!=2 or event.occurrence_state!='cancelled': raise RuntimeError('Event history lost')
        if not EmailOutbox.objects.filter(notification__event_kind='qa28_recovery',status='pending').exists(): raise RuntimeError('Queue lost')
        with override('ru'):
            event_read=Client().get(event.get_absolute_url())
        if event_read.status_code!=200: raise RuntimeError('Event restored public reader fails')
        cursor.execute('ROLLBACK')
    print(json.dumps({'status': 'PASS', 'database': 'qa_stage28_restore', 'unix_socket': True,
                      'read_only_transaction': True, 'post_switch_place': 1, 'program_approved_snapshot': True,
                      'direct_and_group_price': True, 'current_review_reaction': True,
                      'http_public_read_status': public_read.status_code,
                      'http_paused_write_status': paused_write.status_code,
                      'media_bytes_sha256': media_hash,
                      'localized_urls': True}))


if __name__ == '__main__':
    main()
