"""The synthetic seeder must fail before touching any user/model outside QA04."""
import ast
from pathlib import Path
import unittest

class AdminSeederIsolationTests(unittest.TestCase):
    def test_guard_failure_prevents_seed_data_access(self):
        tree=ast.parse((Path(__file__).resolve().parents[1]/'seed_admin_test_data.py').read_text())
        function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='run')
        def denied():
            raise RuntimeError('not isolated')
        namespace={'_require_isolated_database':denied}
        exec(compile(ast.Module(body=[function],type_ignores=[]),'seeder-contract','exec'),namespace)
        with self.assertRaisesRegex(RuntimeError,'not isolated'):
            namespace['run']()
