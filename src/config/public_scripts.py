"""Serve the same small set of ordered script bundles in runserver and collectstatic."""
import os
from multiprocessing.util import Finalize
from pathlib import Path
from shutil import rmtree
from tempfile import NamedTemporaryFile, mkdtemp

from django.conf import settings
from django.contrib.staticfiles.finders import BaseFinder
from django.contrib.staticfiles.utils import matches_patterns
from django.core.files.storage import FileSystemStorage


BUNDLES = {
    "js/public_shell.js": (
        "km_controls.js", "header.js", "motion.js", "motion_budget.js", "auth_navigation.js",
        "public_actions.js", "lazy_sections.js", "km_card_fx.js",
    ),
    "js/map_tools.js": (
        "kidsmap_map_pins.js", "google_maps_motion.js", "google_maps_markers.js",
        "map_paging.js", "map_event_layer.js",
    ),
}


class PublicScriptFinder(BaseFinder):
    def __init__(self):
        self.storages = {}
        self.signatures = {}

    def _process_storage(self):
        pid = os.getpid()
        if pid not in self.storages:
            # Each worker owns the lifetime of its own generated files.
            directory = mkdtemp(prefix="kidsmap-public-js-")
            storage = FileSystemStorage(location=directory)
            Finalize(storage, rmtree, args=(directory,), kwargs={"ignore_errors": True}, exitpriority=10)
            self.storages.setdefault(pid, storage)
        return self.storages[pid]

    def find(self, path, find_all=False, **kwargs):
        if path not in BUNDLES:
            return []
        sources = [settings.BASE_DIR / "static/js" / name for name in BUNDLES[path]]
        signature = tuple(source.stat().st_mtime_ns for source in sources)
        target = Path(self._process_storage().path(path))
        if self.signatures.get(path) != signature or not target.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            with NamedTemporaryFile(dir=target.parent, delete=False) as output:
                for source in sources:
                    output.write(source.read_bytes())
                    output.write(b"\n;\n")
            os.replace(output.name, target)
            self.signatures[path] = signature
        return [str(target)] if find_all else str(target)

    def list(self, ignore_patterns):
        for path in BUNDLES:
            if not matches_patterns(path, ignore_patterns):
                self.find(path)
                yield path, self._process_storage()

    def check(self, **kwargs):
        return []
