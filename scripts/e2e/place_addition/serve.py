"""Run the actual place forms on the explicitly attested QA stand."""
import argparse
from environment import configure,source_manifest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--profile-root', required=True)
parser.add_argument('--socket-dir', required=True)
parser.add_argument('--port', type=int, default=8898)
args = parser.parse_args()
if not 1024 <= args.port <= 65535:
    parser.error('An unprivileged port is required')
repository=configure(args.profile_root, args.socket_dir)
build=source_manifest(repository)
from django.conf import settings
from django.http import JsonResponse
from django.urls import path
from importlib import import_module
assert settings.TESTING
# This endpoint exists only in the attested QA process, never in application URLs.
import_module(settings.ROOT_URLCONF).urlpatterns.insert(0,path('__qa__/build/',lambda request:JsonResponse({'synthetic':True,'sources':build})))
from django.core.management import call_command
call_command('runserver', f'0.0.0.0:{args.port}', use_reloader=False, insecure_serving=True)
