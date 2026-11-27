#!/usr/bin/env python3
"""Weekly KidsMap disk cleanup. Default: preview. Run with --apply to clean.

Run on the deployment host with its system Python (python3-yaml) and Docker.
DRY_RUN=1 forces preview; DRY_RUN=0 alone does not authorize changes.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

RELEASES = Path('/opt/kidsmap-releases')
LOCK = Path('/run/lock/kidsmap-release.lock')
LAYOUT = {'source', 'source.tar', 'static.before', 'candidate.compose.json',
          'rollback.compose.json', 'commands.log', 'baseline-source-drift.json', 'state.json'}
RELEASE_NAME = re.compile(r'[0-9a-f]{12}-[\w-]+')
IMAGE_ID = re.compile(r'sha256:[0-9a-f]{64}')
PRUNES = (('docker', 'image', 'prune'), ('docker', 'builder', 'prune'))


def command(*args):
    # Inspect and Compose output may contain secrets. Only callers select printable fields.
    result = subprocess.run(args, input='y\n' if args in PRUNES else '', capture_output=True,
                            text=True, check=False, env={**os.environ, 'LC_ALL': 'C'})
    if result.returncode:
        raise RuntimeError(f'{args[0]} {args[1]} failed (exit {result.returncode})')
    return result.stdout.strip()


def apply_requested(argv):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--dry-run', action='store_true', help='preview only (default)')
    modes.add_argument('--apply', action='store_true', help='execute the displayed cleanup policy')
    args = parser.parse_args(argv)
    env = os.environ.get('DRY_RUN')
    if env not in (None, '0', '1'):
        parser.error('DRY_RUN must be 0 or 1')
    if args.apply and env == '1':
        parser.error('--apply conflicts with DRY_RUN=1')
    return args.apply


def disk():
    print(command('df', '-h', '/'), flush=True)


def mountpoints():
    paths = [line.split()[4] for line in Path('/proc/self/mountinfo').read_text().splitlines()]
    return {Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), p)) for p in paths}


def docker_containers():
    ids = command('docker', 'ps', '-aq').split()
    if not ids:
        raise RuntimeError('No Docker containers found')
    return json.loads(command('docker', 'container', 'inspect', *ids))


def compose_references(path, root, seen):
    """Collect image references and release dependencies, never serialize Compose values."""
    if path in seen:
        return set(), set()
    seen.add(path)
    raw = path.read_bytes()
    if not re.search(rb'(?:^|[\n{,])\s*["\x27]?(?:services|include)["\x27]?\s*:', raw):
        return set(), set()
    try:
        if path.suffix.lower() == '.json':
            doc = json.loads(raw)
        else:
            import yaml
            doc = yaml.safe_load(raw)
    except ImportError:
        raise RuntimeError('System Python requires python3-yaml for Compose YAML') from None
    except (ValueError, TypeError, UnicodeError):
        raise RuntimeError(f'Unreadable Compose document: {path.name}') from None
    except Exception as error:
        # YAML exceptions can contain the offending line and unrelated environment values.
        raise RuntimeError(f'Cannot parse {path.name} ({type(error).__name__})') from None
    if not isinstance(doc, dict):
        return set(), set()
    services = doc.get('services', {})
    if not isinstance(services, dict):
        raise RuntimeError(f'Unrecognized services in {path.name}')
    images = {svc['image'] for svc in services.values() if isinstance(svc, dict) and svc.get('image')}
    links = set()
    # A retained config can point into another release, including through a relative bind.
    def add_paths(value):
        if isinstance(value, dict):
            for item in value.values():
                add_paths(item)
        elif isinstance(value, list):
            for item in value:
                add_paths(item)
        elif isinstance(value, str):
            links.update(re.findall(re.escape(str(root)) + r'/([\w.-]+)', value))
            if value.startswith(('../', './', '/')):
                relative = (path.parent / value.split(':', 1)[0]).resolve()
                if relative.is_relative_to(root) and relative != root:
                    links.add(relative.relative_to(root).parts[0])
    add_paths(doc)
    external = []
    for item in doc.get('include', []):
        spec = item['path'] if isinstance(item, dict) else item
        external.extend(spec if isinstance(spec, list) else [spec])
    for service in services.values():
        extends = service.get('extends') if isinstance(service, dict) else None
        if isinstance(extends, dict) and extends.get('file'):
            external.append(extends['file'])
    for name in external:
        if '$' in name:
            raise RuntimeError(f'Unresolved Compose dependency in {path.name}')
        child = (path.parent / name).resolve()
        if child.is_relative_to(root):
            links.add(child.relative_to(root).parts[0])
        more_images, more_links = compose_references(child, root, seen)
        images.update(more_images)
        links.update(more_links)
    return images, links


def inspect_release(path, root, mounts):
    eligible = bool(RELEASE_NAME.fullmatch(path.name))
    layout = {p.name for p in path.iterdir()}
    eligible &= LAYOUT <= layout <= LAYOUT | {'checkout-update.log'}
    state = {}
    if 'state.json' in layout:
        state = json.loads((path / 'state.json').read_bytes())
    revision = state.get('revision', '')
    eligible &= (state.get('phase') == 'complete' and len(revision) == 40
                 and path.name.startswith(revision[:12] + '-'))
    images, dependencies = set(), set()
    def fail(error):
        raise error
    for base, dirs, files in os.walk(path, followlinks=False, onerror=fail):
        directory = Path(base)
        for name in dirs + files:
            low = name.lower()
            entry = directory / name
            # Shipped icon packs contain a category called Media in both static trees.
            if name == 'Media' and (entry.is_relative_to(path / 'source' / 'static')
                                    or entry.is_relative_to(path / 'static.before')):
                continue
            # git archive includes source/media/.gitkeep in ordinary code-only releases.
            if entry == path / 'source' / 'media' and entry not in mounts and not entry.is_symlink() and entry.is_dir():
                contents = list(entry.iterdir())
                if not contents or (len(contents) == 1 and contents[0].name == '.gitkeep'
                                    and not contents[0].is_symlink() and contents[0].is_file()
                                    and contents[0].stat().st_size == 0):
                    continue
            media_archive = 'media' in low and low.endswith(('.tar', '.tgz', '.tar.gz', '.tar.zst', '.zip'))
            if (media_archive or low in {'.env', '.git', 'node_modules', 'media', 'original-photo', 'backups',
                                         'private_documents', 'private_drafts'}
                    or (low.startswith(('private-media', 'private_media', '.env.')) and low != '.env.example')
                    or low.endswith(('.dump', '.sql.gz', '.sql.zst', '.pgdump', '.backup'))):
                eligible = False
        dirs[:] = [n for n in dirs if directory / n not in mounts and n not in ('.git', 'node_modules')]
        for name in files:
            f = directory / name
            if f.suffix.lower() in ('.yml', '.yaml') or (f.suffix.lower() == '.json' and
                    (directory == path or 'compose' in name.lower() or 'override' in name.lower())):
                imgs, links = compose_references(f, root, set())
                images.update(imgs)
                dependencies.update(links)
    return eligible, state, images, dependencies


def release_plan(root, containers, mounts):
    if root.resolve() != root:
        raise RuntimeError('Unexpected release root')
    releases = sorted((p for p in root.iterdir() if p.is_dir() and not p.is_symlink()),
                      key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
    keep = set(releases[:3])
    mounts = set(mounts)
    references = set()
    live_file = None
    live_id = None
    def preserve(path):
        if path.is_relative_to(root) and path != root:
            keep.add(root / path.relative_to(root).parts[0])
    for f in root.iterdir():
        if f.is_file() and f.suffix.lower() in ('.yaml', '.yml', '.json'):
            images, links = compose_references(f, root, set())
            references.update(images)
            keep.update(root / name for name in links)
    for mount in mounts:
        preserve(mount)
    for container in containers:
        labels = container['Config'].get('Labels') or {}
        work = Path(labels.get('com.docker.compose.project.working_dir') or '/')
        preserve(work)
        for mount in container['Mounts']:
            preserve(Path(mount['Source']).resolve())
        for config in filter(None, labels.get('com.docker.compose.project.config_files', '').split(',')):
            path = (work / config).resolve()
            preserve(path)
            if not path.is_relative_to(root) and path.is_file():
                images, links = compose_references(path, root, set())
                references.update(images)
                keep.update(root / n for n in links)
            if container['Name'] == '/kidsmap-web' and container['State']['Running'] and path.name == 'candidate.compose.json':
                live_file, live_id = path, container['Image']
    if not live_file or live_file.parent not in releases:
        raise RuntimeError('Cannot identify the active pinned web release')
    entries = {p: inspect_release(p, root, mounts) for p in releases}
    # Touching an archived directory must not displace the third most recent release.
    completed = [p for p in releases if entries[p][1].get('phase') == 'complete']
    completed.sort(key=lambda p: ((p / 'state.json').stat().st_mtime_ns, p.name), reverse=True)
    keep.update(completed[:3])
    state = entries[live_file.parent][1]
    rollback = state.get('baseline_image', '')
    if not (state.get('phase') == 'complete' and state.get('candidate_image') == live_id
            and IMAGE_ID.fullmatch(rollback) and IMAGE_ID.fullmatch(live_id)):
        raise RuntimeError('Active release journal does not confirm current and rollback images')
    for path, (eligible, old, images, links) in entries.items():
        references.update(images)
        if old.get('phase') in ('activating', 'rollback_failed'):
            raise RuntimeError('Unfinished release requires recovery')
        if not eligible or old.get('candidate_image') in (live_id, rollback):
            keep.add(path)
    pending = list(keep)
    while pending:
        path = pending.pop()
        if path not in entries:
            continue
        for linked in entries[path][3]:
            dependency = root/linked
            if dependency not in keep:
                keep.add(dependency)
                pending.append(dependency)
    return sorted(set(releases) - keep), references, (live_id, rollback)


def compose_uses(image, references):
    full = image['Id']
    for ref in references:
        if ('$' in ref or ref == full or ref in (image.get('RepoDigests') or [])
                or re.fullmatch(r'[0-9a-f]{12,64}', ref) and full[7:].startswith(ref)):
            return True
    return False


def tags(image):
    return json.loads(command('docker', 'image', 'inspect', '--format', '{{json .RepoTags}}', image)) or []


def protect_tags(pair):
    for image, alias in zip(pair, ('kidsmap:keep-current', 'kidsmap:keep-rollback')):
        if not tags(image):
            owner = command('docker', 'image', 'ls', '--no-trunc', '-q', alias)
            if owner and owner != image:
                raise RuntimeError(f'Conflicting protection tag: {alias}')
            command('docker', 'tag', image, alias)
        if not tags(image):
            raise RuntimeError('Protected image has no tag')


def image_candidates(containers, refs, pair):
    used = {c['Image'] for c in containers}
    unused = sorted(set(command('docker', 'image', 'ls', '--no-trunc', '-q', '--filter', 'dangling=true').split()) - used)
    candidates = [img for img in unused if img not in pair]
    if candidates:
        images = json.loads(command('docker', 'image', 'inspect', *candidates))
        if any(compose_uses(img, refs) for img in images):
            raise RuntimeError('A Compose file could use an untagged image; unfiltered image prune is unsafe')
    return candidates


def perform(apply, paths, pair, refs):
    if not apply:
        return
    for path in paths:
        if path.is_symlink() or any(m.is_relative_to(path) for m in mountpoints()):
            raise RuntimeError(f'Release path changed: {path.name}')
        shutil.rmtree(path)
    disk()
    command('journalctl', '--vacuum-time=14d')
    disk()
    protect_tags(pair)
    image_candidates(docker_containers(), refs, pair)
    for args in PRUNES:
        output = command(*args)
        print(next((s for s in reversed(output.splitlines()) if s.lower().startswith('total')), 'Done'))
        disk()


def run(apply):
    containers = docker_containers()
    paths, refs, pair = release_plan(RELEASES, containers, mountpoints())
    # Retain the IDs as well as the names in case a Compose tag moves during cleanup.
    tags_by_id = command('docker', 'image', 'ls', '--no-trunc', '--format', '{{.ID}} {{.Repository}}:{{.Tag}}')
    for row in tags_by_id.splitlines():
        image, tag = row.split(maxsplit=1)
        if tag in refs or tag.removesuffix(':latest') in refs:
            refs.add(image)
    candidates = image_candidates(containers, refs, pair)
    print('APPLY' if apply else 'DRY_RUN')
    disk()
    for label, image in zip(('current', 'rollback'), pair):
        print(f'{label}: {image} tags={tags(image) or "would add keep tag"}')
    print(f'Release directories eligible: {len(paths)}')
    if paths:
        print(command('du', '-x', '-sh', '--', *map(str, paths)))
    cutoff = time.time() - 14 * 86400
    old = [p for p in Path('/var/log/journal').glob('*/*@*.journal*') if p.stat().st_mtime < cutoff]
    print(f'Journal retention: 14 days; {len(old)} archived files older by mtime, '
          f'{sum(p.stat().st_blocks * 512 for p in old) / 2**20:.1f} MiB')
    print(f'Unused dangling images eligible: {len(candidates)}', *candidates)
    summary = command('docker', 'system', 'df').splitlines()
    cache_row = next((line for line in summary if line.startswith('Build Cache')), None)
    if cache_row is None:
        raise RuntimeError('Cannot identify Docker build cache in docker system df')
    print(summary[0])
    print(cache_row)
    perform(apply, paths, pair, refs)
    if apply:
        if not all(tags(img) for img in pair):
            raise RuntimeError('Protected image missing after cleanup')
        current = docker_containers()
        def running(items):
            return {(c['Id'], c['State']['StartedAt']) for c in items if c['State']['Running']}
        if running(current) != running(containers):
            raise RuntimeError('Running containers changed during cleanup')
        for path in ('/', '/ru/catalog/'):
            code = command('curl', '-sS', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '45',
                           'https://kidsmap.az' + path)
            print(f'{path} HTTP {code}')
            if code != '200':
                raise RuntimeError('Site check failed')


def main(argv=None):
    apply = apply_requested(argv)
    with LOCK.open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Skipped: another cleanup or release holds the deployment lock.')
            return 0
        run(apply)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f'Cleanup stopped: {error}', file=sys.stderr)
        sys.exit(1)
