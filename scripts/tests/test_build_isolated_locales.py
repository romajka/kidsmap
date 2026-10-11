"""Exercise real compiler output and provenance, including tamper/freshness failures."""
import gettext
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT/'scripts/build_isolated_locales.py'
PO = '''msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "Hello"
msgstr "Salam"

msgctxt "menu"
msgid "Board"
msgstr "Lövhə"

msgid "apple"
msgid_plural "apples"
msgstr[0] "alma"
msgstr[1] "almalar"

#, fuzzy
msgid "Fuzzy"
msgstr "Do not ship"
'''


class IsolatedLocaleBuildTests(unittest.TestCase):
    def setUp(self):
        (ROOT/'.tmp').mkdir(exist_ok=True)
        self.run_root = Path(tempfile.mkdtemp(prefix='locale-tool-test-',dir=ROOT/'.tmp'))
        self.source = self.run_root/'source'
        self.po = self.source/'az/LC_MESSAGES/django.po'
        self.po.parent.mkdir(parents=True)
        self.po.write_text(PO,encoding='utf-8')
        self.output = self.run_root/'build'

    def command(self,*args):
        return subprocess.run([sys.executable,str(TOOL),*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')

    def build(self,output=None):
        result = self.command('build','--source-locale',self.source,'--output',output or self.output,'--locales','az','--compiler','wsl')
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(((output or self.output)/'manifest.json').read_text(encoding='utf-8'))

    def verify(self):
        return self.command('verify','--manifest',self.output/'manifest.json','--source-locale',self.source)

    def test_real_singular_context_plural_and_fuzzy_omission(self):
        self.build()
        with (self.output/'locale/az/LC_MESSAGES/django.mo').open('rb') as file:
            catalogue = gettext.GNUTranslations(file)
        self.assertEqual(catalogue.gettext('Hello'),'Salam')
        self.assertEqual(catalogue.pgettext('menu','Board'),'Lövhə')
        self.assertEqual(catalogue.ngettext('apple','apples',2),'almalar')
        self.assertEqual(catalogue.gettext('Fuzzy'),'Fuzzy')
        self.assertEqual(self.verify().returncode,0)

    def test_same_inputs_have_deterministic_mo_hashes(self):
        first = self.build()
        second = self.build(self.run_root/'second')
        self.assertEqual(first['entries'][0]['mo_sha256'],second['entries'][0]['mo_sha256'])

    def test_changed_source_even_with_same_mtime_is_rejected(self):
        self.build(); times = self.po.stat().st_atime_ns,self.po.stat().st_mtime_ns
        self.po.write_text(PO.replace('Salam','Changed'),encoding='utf-8'); os.utime(self.po,ns=times)
        self.assertNotEqual(self.verify().returncode,0)

    def test_tampered_missing_asset_and_manifest_are_rejected(self):
        self.build(); mo = self.output/'locale/az/LC_MESSAGES/django.mo'
        mo.write_bytes(b'corrupt')
        self.assertNotEqual(self.verify().returncode,0)
        mo.unlink(); self.assertNotEqual(self.verify().returncode,0)
        (self.output/'manifest.json').unlink(); self.assertNotEqual(self.verify().returncode,0)

    def test_existing_output_and_source_are_refused_without_changes(self):
        self.build(); before = (self.output/'manifest.json').read_bytes()
        result = self.command('build','--source-locale',self.source,'--output',self.output,'--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual((self.output/'manifest.json').read_bytes(),before)
        result = self.command('build','--source-locale',self.source,'--output',self.source,'--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0); self.assertEqual(self.po.read_text(encoding='utf-8'),PO)

    def test_format_error_never_publishes_complete_manifest(self):
        self.po.write_text(PO+'\n#, python-format\nmsgid "Count %s"\nmsgstr "Count %d"\n',encoding='utf-8')
        result = self.command('build','--source-locale',self.source,'--output',self.output,'--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.output/'manifest.json').exists())

    def test_outside_owned_scratch_is_rejected(self):
        result = self.command('build','--source-locale',self.source,'--output',ROOT/'locale-illegal-test-output','--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0); self.assertFalse((ROOT/'locale-illegal-test-output').exists())

    def test_incomplete_and_escaping_manifests_are_rejected(self):
        manifest=self.build(); path=self.output/'manifest.json'
        for mutate in (lambda m:m.update(status='building'),lambda m:m.update(entries=[]),
                       lambda m:m['entries'][0].update(mo='../../outside.mo')):
            candidate=json.loads(json.dumps(manifest));mutate(candidate)
            path.write_text(json.dumps(candidate),encoding='utf-8')
            self.assertNotEqual(self.verify().returncode,0)

    @unittest.skipUnless(os.name=='nt','Windows junction test')
    def test_source_and_output_junctions_are_refused(self):
        link=self.run_root/'source-link'
        created=subprocess.run(['cmd','/c','mklink','/J',str(link),str(self.source)],capture_output=True)
        self.assertEqual(created.returncode,0)
        result=self.command('build','--source-locale',link,'--output',self.output,'--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0,'Source junction was accepted')
        result=self.command('build','--source-locale',self.source,'--output',link/'nested','--locales','az','--compiler','wsl')
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.source/'nested').exists())


if __name__ == '__main__': unittest.main()
