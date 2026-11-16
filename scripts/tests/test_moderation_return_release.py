"""Runtime fingerprint ignores bind ordering but preserves actual mount changes."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest

source = Path(__file__).resolve().parents[1] / 'releases/moderation-return-20261116/release.py'
module = ast.parse(source.read_text())
functions = ast.Module(body=[node for node in module.body if isinstance(node, ast.FunctionDef)
    and node.name in {'digest', 'fingerprint'}], type_ignores=[])
scope = {'hashlib': hashlib, 'json': json}
exec(compile(functions, str(source), 'exec'), scope)

class RuntimeFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.before = {'Config': {'Env':['X=1']}, 'Mounts':[
            {'Type':'bind','Source':'/media','Destination':'/app/media','RW':True},
            {'Type':'bind','Source':'/static','Destination':'/app/staticfiles','RW':True}],
            'HostConfig':{'Binds':['/media:/app/media:rw','/static:/app/staticfiles:rw']},
            'NetworkSettings':{'Networks':{'default':{}}}}

    def test_bind_order_is_not_runtime_drift(self):
        after=copy.deepcopy(self.before)
        after['HostConfig']['Binds'].reverse()
        after['Mounts'].reverse()
        self.assertEqual(scope['fingerprint'](self.before),scope['fingerprint'](after))

    def test_real_mount_change_is_detected(self):
        after=copy.deepcopy(self.before)
        after['HostConfig']['Binds'][0]='/different:/app/media:rw'
        self.assertNotEqual(scope['fingerprint'](self.before),scope['fingerprint'](after))

if __name__ == '__main__':
    unittest.main()
