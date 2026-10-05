"""Run the checked-in media location rules with isolated nginx and synthetic files."""
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import urlopen


def main():
    source = Path('/mnt/c/kidsmap/deploy/nginx/kidsmap.az.conf')
    executable = Path('/root/task33-nginx-tools/root/usr/sbin/nginx')
    assert executable.is_file()
    original = source.read_text()
    server = original[original.rfind('server {'):]
    with tempfile.TemporaryDirectory(prefix='kidsmap-qa24-nginx-') as temporary:
        root = Path(temporary)
        media = root / 'media'
        media.mkdir()
        files = {'public.txt': b'public synthetic bytes',
                 'protected_docs/specialists/identity.txt': b'private synthetic bytes',
                 'specialist-documents/proof.bin': b'private synthetic bytes',
                 'private-media/proof.bin': b'private synthetic bytes'}
        for name, content in files.items():
            target = media / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            port = listener.getsockname()[1]
        # Adapt only runtime wiring: TLS/listen/certs and filesystem locations.
        # All source location matching, deny rules and public-media headers remain intact.
        server = re.sub(r'^\s*listen .*?;\s*$', '', server, flags=re.M)
        server = re.sub(r'^\s*ssl_.*?;\s*$', '', server, flags=re.M)
        server = server.replace('server {', f'server {{\nlisten 127.0.0.1:{port};', 1)
        server = server.replace('/opt/kidsmap/media/', str(media) + '/')
        server = server.replace('/opt/kidsmap/staticfiles/', str(root / 'static') + '/')
        config = root / 'nginx.conf'
        config.write_text(f'user root;\npid {root}/nginx.pid;\nerror_log {root}/error.log;\n'
                          f'events {{ worker_connections 32; }}\nhttp {{ access_log off;\n'
                          f'client_body_temp_path {root}/body; proxy_temp_path {root}/proxy; '
                          f'fastcgi_temp_path {root}/fastcgi; uwsgi_temp_path {root}/uwsgi; '
                          f'scgi_temp_path {root}/scgi;\n' + server + '\n}\n')
        validation = subprocess.run([str(executable), '-e', str(root/'error.log'), '-p', str(root), '-c', str(config), '-t'],
                                    capture_output=True, text=True)
        assert validation.returncode == 0, 'nginx config validation failed: ' + validation.stderr
        process = subprocess.Popen([str(executable), '-e', str(root/'error.log'), '-p', str(root), '-c', str(config), '-g', 'daemon off;'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                try:
                    with socket.create_connection(('127.0.0.1', port), timeout=.1):
                        break
                except OSError:
                    if process.poll() is not None:
                        raise RuntimeError('Isolated nginx exited before readiness')
                    time.sleep(.05)
            paths = {'/media/public.txt': 200,
                     '/media/protected_docs/specialists/identity.txt': 404,
                     '/media/%70rotected_docs/specialists/identity.txt': 404,
                     '/media/specialist-documents/proof.bin': 404,
                     '/media/private-media/proof.bin': 404,
                     '/media/public/../protected_docs/specialists/identity.txt': 404}
            results = []
            for path, expected in paths.items():
                try:
                    with urlopen(f'http://127.0.0.1:{port}{path}', timeout=3) as response:
                        status = response.status
                        body = response.read()
                except HTTPError as error:
                    status = error.code
                    body = error.read()
                assert status == expected, f'Unexpected media status {path}: {status}'
                assert b'private synthetic bytes' not in body
                if expected == 200:
                    assert body == b'public synthetic bytes'
                results.append({'path': path, 'status': status, 'passed': True})
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        return {'status': 'PASS', 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'binary_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                'nginx_version': subprocess.check_output([str(executable), '-v'], stderr=subprocess.STDOUT).decode().strip(),
                'nginx_config_check': 'PASS', 'cases': results, 'cleanup': 'PASS',
                'production': 'NOT_CONTACTED', 'tls': 'NOT_TESTED; loopback HTTP adapter'}


if __name__ == '__main__':
    result = main()
    destination = Path('/root/task33-evidence/stage24-nginx-20261003.json')
    assert not destination.exists()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
