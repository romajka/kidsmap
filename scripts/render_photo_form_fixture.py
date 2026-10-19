"""Render the real continuous photo form using an owned isolated quality profile.

Run only after run_isolated_quality.py on its disposable Unix-socket PostgreSQL.
No inherited credentials, shared database, network database or existing output.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

ROOT=Path(__file__).resolve().parents[1]


def validate_output(output, repository=ROOT):
    output=Path(output).absolute();repository=Path(repository).resolve()
    scratch=repository/'.tmp'
    if output.suffix!='.html' or not output.resolve().is_relative_to(scratch) or output.exists():
        raise ValueError('A new HTML fixture under repository .tmp is required')
    for p in (output,*output.parents):
        if p.is_symlink():raise ValueError('Fixture symlinks are not allowed')
        if p==repository:break
    return output.resolve()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile-root',required=True,type=Path)
    p.add_argument('--socket-dir',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    a=p.parse_args()
    sys.path.insert(0,str(ROOT))
    from scripts.run_isolated_quality import validate_paths
    profile,socket=validate_paths(a.profile_root,a.socket_dir)
    output=validate_output(a.output)
    if not stat.S_ISSOCK((socket/'.s.PGSQL.5432').stat().st_mode):
        raise ValueError('Owned PostgreSQL socket required')
    if (profile/'settings.py').is_symlink() or (profile/'attestation.json').is_symlink():
        raise ValueError('Owned quality profile files required')
    att=json.loads((profile/'attestation.json').read_text())
    if (att.get('testing') is not True or att.get('network_database') is not False
            or att.get('actual_database')!='qa_stage04' or att.get('actual_role')!='qa_stage04'
            or att.get('credentials_inherited') is not False or att.get('socket')!=str(socket)):
        raise ValueError('Verified isolated quality attestation required')
    # Clear credentials before importing Django/project settings.
    os.environ.clear()
    os.environ.update(DJANGO_TESTING='1',DJANGO_SETTINGS_MODULE='settings',
        TASK33_QA_ROOT=str(profile),TASK33_QA_SOCKET=str(socket),
        PATH='/usr/local/bin:/usr/bin:/bin',HOME=str(profile),LANG='C.UTF-8',
        PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(profile))
    sys.dont_write_bytecode=True
    sys.path[:0]=[str(profile),str(ROOT/'src')]
    from scripts.build_isolated_locales import verify
    locale=verify(Path(att['locale_root']).parent/'manifest.json',ROOT/'locale')
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    from catalog.services.catalog_conversion import _require_isolated_database
    _require_isolated_database()
    assert settings.TESTING and settings.EMAIL_BACKEND=='django.core.mail.backends.locmem.EmailBackend'
    assert list(map(str,settings.LOCALE_PATHS))==[locale['locale_root']]
    with connection.cursor() as c:
        c.execute('SELECT current_database(),current_user,inet_server_addr()')
        assert c.fetchone()==('qa_stage04','qa_stage04',None)
    from django.contrib.auth import get_user_model
    from django.test import Client
    from django.urls import reverse
    from django.utils.translation import override
    from catalog.testcases.utils import create_ready_place
    user,created=get_user_model().objects.get_or_create(username='rendered_photo_fixture',
        defaults={'email':'photo-fixture@example.invalid','is_active':True})
    assert user.email=='photo-fixture@example.invalid' and user.is_active and not user.is_staff and not user.is_superuser
    place=create_ready_place(owner=user,created_by=user,name_az='Fictional photo integration fixture',
        name_ru='Вымышленная проверка фотографий',name_en='Fictional photo integration fixture')
    client=Client();client.force_login(user)
    with override('ru'):
        response=client.get(reverse('owner_place_edit',args=[place.pk]))
    assert response.status_code==200
    html=response.content
    assert b'data-place-mode="continuous"' in html and b'owner_place_continuous.js' in html
    assert b'permanent_place_photos.js' in html and b'permanent_place_wizard.js' not in html
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as f:f.write(html)
    print(json.dumps({'fixture':str(output),'sha256':hashlib.sha256(html).hexdigest(),
        'bytes':len(html),'render':'actual Django authenticated continuous form',
        'fictional_only':True,'actual_database':'qa_stage04','network_database':False}))


if __name__=='__main__':main()
