#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import shlex
import sys
from pathlib import Path


def load_local_map_environment(project_root, command):
    """Supply local map settings for runserver without importing other .env services."""
    if command != 'runserver':
        return
    env_file = project_root / '.env'
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        name, separator, value = line.partition('=')
        name = name.strip().removeprefix('export ')
        if not separator or name not in {'GOOGLE_MAPS_API_KEY', 'GOOGLE_MAPS_MAP_ID'}:
            continue
        if name in os.environ:
            continue
        try:
            parts = shlex.split(value, comments=True)
        except ValueError:
            continue
        if len(parts) <= 1:
            os.environ[name] = parts[0] if parts else ''


def main():
    """Run administrative tasks."""
    project_root = Path(__file__).resolve().parent
    load_local_map_environment(project_root, sys.argv[1] if len(sys.argv) > 1 else '')
    src_path = str(project_root / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
