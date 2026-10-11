"""Build project gettext assets into a new owned scratch tree; verify by content."""
import argparse
import gettext
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / '.tmp'
OPTIONS = ['--check-format','--statistics','--endianness=little']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def no_links(path):
    for component in (path,*path.parents):
        if component.is_symlink() or component.is_junction():
            raise ValueError(f'Symlink/junction is not allowed: {component}')


def owned(path):
    path = Path(path).absolute()
    no_links(path)
    resolved = path.resolve()
    if resolved == SCRATCH.resolve() or not resolved.is_relative_to(SCRATCH.resolve()):
        raise ValueError('Output must be a new descendant of checkout .tmp')
    return resolved


def command(argv):
    result = subprocess.run(argv,capture_output=True,encoding='utf-8')
    if result.returncode:
        raise ValueError(f'Compiler command exited {result.returncode}: {result.stderr.strip()}')
    return result.stdout.strip(),result.stderr.strip()


def compiler(mode):
    if mode == 'wsl':
        prefix = ['wsl.exe','--exec','msgfmt']
        def filename(path):
            return command(['wsl.exe','--exec','wslpath','-u',str(path)])[0]
    else:
        executable = shutil.which('msgfmt')
        if not executable: raise ValueError('Native GNU msgfmt is unavailable')
        prefix = [executable]
        filename = str
    version = command(prefix+['--version'])[0].splitlines()[0]
    if 'GNU gettext' not in version: raise ValueError('GNU msgfmt is required')
    return prefix,filename,version


def source_files(source,locales):
    if not source.is_dir() or not locales or len(set(locales)) != len(locales):
        raise ValueError('Source directory and unique locales are required')
    files = []
    for locale in locales:
        if not re.fullmatch(r'[a-z]{2}(?:_[A-Z]{2})?',locale): raise ValueError('Invalid locale')
        paths = sorted((source/locale/'LC_MESSAGES').glob('*.po'))
        if not paths: raise ValueError(f'No source catalogue for {locale}')
        for path in paths:
            no_links(path)
            if not re.fullmatch(r'[A-Za-z0-9_]+',path.stem): raise ValueError('Invalid domain')
            files.append(path)
    return files


def build(source,output,locales,mode):
    output = owned(output)
    no_links(Path(source).absolute())
    source = Path(source).resolve()
    files = source_files(source,locales)
    if output.exists(): raise ValueError('Output already exists; choose a new directory')
    if source.is_relative_to(output) or output.is_relative_to(source):
        raise ValueError('Source and output must be disjoint')
    prefix,filename,version = compiler(mode)
    output.mkdir(parents=True,exist_ok=False)
    entries = []
    for path in files:
        relative = path.relative_to(source)
        digest = sha(path)
        frozen = output/'source'/relative
        frozen.parent.mkdir(parents=True,exist_ok=True)
        frozen.write_bytes(path.read_bytes())
        if sha(path) != digest or sha(frozen) != digest: raise ValueError('Source changed during capture')
        mo = (output/'locale'/relative).with_suffix('.mo')
        mo.parent.mkdir(parents=True,exist_ok=True)
        temporary = mo.with_suffix('.mo.tmp')
        argv = prefix+OPTIONS+['-o',filename(temporary),filename(frozen)]
        stdout,stderr = command(argv)
        with temporary.open('rb') as file: gettext.GNUTranslations(file)
        temporary.replace(mo)
        entries.append({'source':relative.as_posix(),'po_sha256':digest,
            'snapshot':frozen.relative_to(output).as_posix(),'mo':mo.relative_to(output).as_posix(),
            'mo_sha256':sha(mo),'command':argv,'exit_code':0,'stdout':stdout,'stderr':stderr})
    if any(sha(source/row['source']) != row['po_sha256'] for row in entries):
        raise ValueError('Source changed during compilation')
    manifest = {'schema_version':1,'status':'complete','source_root':str(source),
        'locale_root':str(output/'locale'),'locales':list(locales),'entries':entries,
        'compiler':{'mode':mode,'argv':prefix,'version':version,'options':OPTIONS}}
    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


def child(root,relative):
    if not isinstance(relative,str) or Path(relative).is_absolute(): raise ValueError('Invalid manifest path')
    path = root/relative
    no_links(path)
    if not path.resolve().is_relative_to(root.resolve()): raise ValueError('Manifest path escapes output')
    return path


def verify(manifest_path,source):
    manifest_path = owned(manifest_path)
    output = manifest_path.parent
    no_links(Path(source).absolute())
    source = Path(source).resolve()
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('schema_version') != 1 or manifest.get('status') != 'complete'
        or manifest.get('source_root') != str(source)
        or manifest.get('locale_root') != str(output/'locale')):
        raise ValueError('Incomplete or mismatched manifest')
    entries = manifest.get('entries',[])
    expected = {path.relative_to(source).as_posix() for path in source_files(source,manifest['locales'])}
    if not entries or len(entries) != len(expected) or {row['source'] for row in entries} != expected:
        raise ValueError('Incomplete catalogue set')
    for row in entries:
        po = child(source,row['source']); frozen = child(output,row['snapshot']); mo = child(output,row['mo'])
        if row['snapshot'] != 'source/'+row['source'] or row['mo'] != 'locale/'+str(Path(row['source']).with_suffix('.mo')).replace('\\','/'):
            raise ValueError('Unexpected asset paths')
        if sha(po) != row['po_sha256'] or sha(frozen) != row['po_sha256'] or sha(mo) != row['mo_sha256']:
            raise ValueError('Catalogue is stale or modified')
        with mo.open('rb') as file: gettext.GNUTranslations(file)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action',required=True)
    builder = sub.add_parser('build')
    builder.add_argument('--source-locale',default=str(ROOT/'locale'))
    builder.add_argument('--output',required=True)
    builder.add_argument('--locales',nargs='+',default=['ru','az','en'])
    builder.add_argument('--compiler',choices=['wsl','native'],required=True)
    verifier = sub.add_parser('verify')
    verifier.add_argument('--manifest',required=True)
    verifier.add_argument('--source-locale',default=str(ROOT/'locale'))
    args = parser.parse_args()
    try:
        manifest = (build(args.source_locale,args.output,args.locales,args.compiler) if args.action=='build'
                    else verify(args.manifest,args.source_locale))
        print(json.dumps({'status':'complete','locale_root':manifest['locale_root'],'catalogues':len(manifest['entries'])}))
    except (ValueError,OSError,KeyError,TypeError) as error:
        print(str(error),file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
