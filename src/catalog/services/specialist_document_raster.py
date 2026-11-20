"""Bounded private raster cache. Authorization always runs before this service."""
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from threading import BoundedSemaphore

from catalog.private_storage import is_private_document_file

MAX_SOURCE_BYTES = 10 * 1024 * 1024
_WORKER = Path(__file__).with_name('specialist_document_raster_worker.py')
_RENDER_SLOTS = BoundedSemaphore(2)


class PreviewUnavailable(Exception):
    pass


class PageNotFound(Exception):
    pass


def render_document_page(field, page, *, thumbnail=False):
    if not is_private_document_file(field):
        raise PageNotFound
    try:
        path = Path(field.path)
        stat = path.stat()
        if not 0 < stat.st_size <= MAX_SOURCE_BYTES:
            raise PreviewUnavailable
        return _render_file(path, stat.st_mtime_ns, stat.st_size, page, 440 if thumbnail else 1800)
    except (OSError, ValueError) as exc:
        raise PreviewUnavailable from exc


@lru_cache(maxsize=16)
def _render_file(path, modified_ns, size, page, edge):
    # The path, mtime and size identify the private source, including after restores.
    if not _RENDER_SLOTS.acquire(timeout=2):
        raise PreviewUnavailable
    try:
        with path.open('rb') as source:
            result = subprocess.run(
                [sys.executable, '-I', str(_WORKER), str(page), str(edge)],
                stdin=source, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=10, env={'PATH': os.defpath, 'LC_ALL': 'C'},
            )
        if result.stdout == b'no-page\n':
            raise PageNotFound
        count, _, jpeg = result.stdout.partition(b'\n')
        if result.returncode or not count.isdigit() or not jpeg.startswith(b'\xff\xd8'):
            raise PreviewUnavailable
        return int(count), jpeg
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PreviewUnavailable from exc
    finally:
        _RENDER_SLOTS.release()
