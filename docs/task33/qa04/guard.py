"""Fail closed: only the runner's Unix socket, never TCP/SMTP/Redis."""
import os
import socket
from pathlib import Path


def socket_path():
    run_root=Path(os.environ['TASK33_QA_ROOT'])
    raw=Path(os.environ.get('TASK33_QA_SOCKET',str(run_root/'socket')))
    if raw.is_symlink():raise RuntimeError('Symlink QA socket root forbidden')
    resolved=raw.resolve()
    expected=run_root.resolve()/'socket'
    prefix=str(Path(__file__).resolve().parents[3]/'.tmp'/'kidsmap-task33-qa04-socket-')
    if resolved!=expected and not str(resolved).startswith(prefix):raise RuntimeError('Unowned QA socket location')
    return resolved

def validate_settings(settings):
    raw_root = Path(os.environ['TASK33_QA_ROOT'])
    run_root = raw_root.resolve()
    if not str(run_root).startswith('/tmp/kidsmap-task33-qa04-') or raw_root.is_symlink():
        raise RuntimeError('Unsafe QA root')
    db = settings.DATABASES
    if set(db) != {'default'}:
        raise RuntimeError('Additional database aliases forbidden')
    target = db['default']
    if target['ENGINE'] != 'django.db.backends.postgresql' or target['HOST'] != str(socket_path()):
        raise RuntimeError('Database target is not the disposable QA Unix socket')
    if target['NAME'] != 'qa_stage04' or target['TEST']['NAME'] != 'test_qa_stage04':
        raise RuntimeError('Unexpected disposable DB names')
    if set(settings.CACHES)!={'default'}:raise RuntimeError('Extra cache aliases forbidden')
    if settings.CACHES['default']['BACKEND'] != 'django.core.cache.backends.locmem.LocMemCache':
        raise RuntimeError('Non-local cache forbidden')
    if settings.EMAIL_BACKEND != 'django.core.mail.backends.locmem.EmailBackend':
        raise RuntimeError('SMTP forbidden')
    if Path(settings.MEDIA_ROOT).resolve() != run_root / 'media':
        raise RuntimeError('Working media path forbidden')
    if not settings.TESTING:
        raise RuntimeError('DJANGO_TESTING is required')
    if any(getattr(settings, k, '') for k in ['GOOGLE_MAPS_API_KEY','GOOGLE_OAUTH_CLIENT_ID','GOOGLE_OAUTH_CLIENT_SECRET','GOOGLE_ANALYTICS_MEASUREMENT_ID','GOOGLE_APPLICATION_CREDENTIALS','INDEXNOW_KEY']):
        raise RuntimeError('External integration credentials forbidden')


def install_network_guard():
    original = socket.socket.connect
    original_ex = socket.socket.connect_ex
    def check(sock, address):
        if sock.family != socket.AF_UNIX:
            raise RuntimeError('QA external/TCP connection blocked')
        root = socket_path()
        if not isinstance(address, str) or not Path(address).resolve().is_relative_to(root):
            raise RuntimeError('QA unrelated Unix socket blocked')
    def connect(sock, address):
        check(sock, address)
        return original(sock, address)
    def connect_ex(sock, address):
        check(sock, address)
        return original_ex(sock, address)
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    return original, original_ex

def install_libpq_guard():
    """psycopg uses C sockets, so Python socket guards alone are insufficient."""
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
    original=psycopg.Connection.connect
    allowed=str(socket_path())
    def connect(cls, conninfo='', **kwargs):
        connection_kwargs={k:v for k,v in kwargs.items() if k not in {'autocommit','prepare_threshold','context','row_factory','cursor_factory'}}
        target=conninfo_to_dict(conninfo,**connection_kwargs)
        if target.get('host')!=allowed or target.get('hostaddr') or target.get('service'):
            raise RuntimeError('QA libpq foreign connection blocked')
        return original(conninfo,**kwargs)
    psycopg.Connection.connect=classmethod(connect)
    # module-level connect is a previously-bound alias in psycopg.
    psycopg.connect=psycopg.Connection.connect
