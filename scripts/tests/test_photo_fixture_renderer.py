"""Rendered form evidence may only create a new ignored local fixture."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]

class PhotoFixtureOutputTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('photo_fixture',ROOT/'scripts/render_photo_form_fixture.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)/'repo';(self.repo/'.tmp').mkdir(parents=True)

    def test_new_ignored_html_is_accepted(self):
        p=self.repo/'.tmp/fixture/form.html'
        self.assertEqual(self.module.validate_output(p,self.repo),p)

    def test_outside_scratch_is_rejected(self):
        with self.assertRaises(ValueError):self.module.validate_output(self.repo/'form.html',self.repo)

    def test_existing_fixture_is_preserved(self):
        p=self.repo/'.tmp/form.html';p.write_text('preserve')
        with self.assertRaises(ValueError):self.module.validate_output(p,self.repo)
        self.assertEqual(p.read_text(),'preserve')

    def test_symlink_ancestor_is_rejected(self):
        link=self.repo/'.tmp/link';link.symlink_to(self.repo,target_is_directory=True)
        with self.assertRaises(ValueError):self.module.validate_output(link/'form.html',self.repo)

    def test_non_html_output_is_rejected(self):
        with self.assertRaises(ValueError):self.module.validate_output(self.repo/'.tmp/form.py',self.repo)

    def test_parent_traversal_outside_scratch_is_rejected(self):
        with self.assertRaises(ValueError):self.module.validate_output(self.repo/'.tmp/../form.html',self.repo)
