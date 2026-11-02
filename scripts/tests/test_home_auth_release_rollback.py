"""Exercise the real release recovery handler without running server setup.

Only its AST exception handler is executed. Docker, health probes, file copying
and subprocesses are replaced; all local files live in a temporary directory.
"""
import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SCRIPT = Path(__file__).resolve().parents[1] / "releases" / "activate-home-auth-20261102.py"


def recovery_code():
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"), filename=str(SCRIPT))
    handlers = [
        node for node in tree.body
        if isinstance(node, ast.Try)
        and any(
            isinstance(handler.type, ast.Name) and handler.type.id == "BaseException"
            for handler in node.handlers
        )
    ]
    if len(handlers) != 1:
        raise AssertionError("Expected one top-level activation recovery handler")
    guarded = copy.deepcopy(handlers[0])
    guarded.body = [ast.Raise(exc=ast.Name(id="activation_error", ctx=ast.Load()), cause=None)]
    module = ast.fix_missing_locations(ast.Module(body=[guarded], type_ignores=[]))
    return compile(module, str(SCRIPT), "exec")


class HomeAuthReleaseRollbackTests(unittest.TestCase):
    def test_candidate_replaces_inherited_revision_and_keeps_other_labels(self):
        tree = ast.parse(SCRIPT.read_text())
        start = next(i for i, node in enumerate(tree.body)
                     if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                     and node.targets[0].id == 'config')
        end = next(i for i, node in enumerate(tree.body)
                   if isinstance(node, ast.FunctionDef) and node.name == 'escape')
        code = compile(ast.Module(body=tree.body[start:end], type_ignores=[]), str(SCRIPT), 'exec')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'previous.compose.json').write_text(json.dumps({'services': {'web': {
                'labels': {'org.opencontainers.image.revision': 'old', 'retained': 'yes'},
                'build': '.', 'environment': {'EXISTING': 'value'}, 'ports': []}}}))
            scope = {'ROOT': root, 'BUILD': {'tag': 'new-image', 'revision': 'new-commit'}, 'json': json}
            exec(code, scope)
        web = scope['config']['services']['web']
        self.assertEqual(web['labels'], {'org.opencontainers.image.revision': 'new-commit', 'retained': 'yes'})
        self.assertEqual(web['environment']['EXISTING'], 'value')
        self.assertNotIn('build', web)

    def exercise(self, *, copy_error=False, static_error=False, activation_error=False,
                 health_error=False, switched=True):
        events = []

        def action(name, fail):
            def perform(*args, **kwargs):
                events.append(name)
                if fail:
                    raise RuntimeError("Injected " + name)
            return Mock(side_effect=perform)

        failure = RuntimeError("Original activation failure")
        copy_restore = action("homepage_restore", copy_error)
        static_restore = action("static_manifest_restore", static_error)
        old_activation = action("previous_image_activation", activation_error)
        health = action("previous_image_health", health_error)
        with tempfile.TemporaryDirectory(prefix="kidsmap-release-rollback-test-") as temporary:
            root = Path(temporary)
            (root / "restore_homepage.py").write_text("# fictional restore payload\n")
            (root / "staticfiles.before.json").write_text('{"paths":{"a":"a.old"}}')
            scope = {
                "ROOT": root, "BEFORE": {"image_id": "sha256:previous", "image": "previous:retained"},
                "changed": True, "switched": switched, "activation_error": failure,
                "subprocess": SimpleNamespace(run=copy_restore, STDOUT=-2),
                "shutil": SimpleNamespace(copy2=static_restore),
                "command": lambda config, *args: [config, *args],
                "run": old_activation, "health": health,
                "inspect": Mock(return_value={"Image": "sha256:previous"}), "json": json,
            }
            with contextlib.redirect_stdout(io.StringIO()) as output:
                with self.assertRaises(RuntimeError) as raised:
                    exec(recovery_code(), scope)
            self.assertIs(raised.exception, failure, "Recovery must retain the original failure")
            result = json.loads((root / "rollback-result.json").read_text())

        copy_restore.assert_called_once()
        static_restore.assert_called_once()
        health.assert_called_once()
        if switched:
            old_activation.assert_called_once_with(
                ["rollback.compose.json", "up", "-d", "--no-deps", "--no-build", "web"],
                "rollback.log",
            )
        else:
            old_activation.assert_not_called()
        return events, result, output.getvalue()

    def test_copy_and_static_failures_cannot_suppress_previous_image_activation(self):
        for copy_error, static_error in ((True, False), (False, True), (True, True)):
            with self.subTest(copy_error=copy_error, static_error=static_error):
                events, result, output = self.exercise(copy_error=copy_error, static_error=static_error)
                expected = (["homepage_restore"] if copy_error else []) + (
                    ["static_manifest_restore"] if static_error else []
                )
                self.assertEqual(result["errors"], expected)
                self.assertEqual(events, ["homepage_restore", "static_manifest_restore",
                                          "previous_image_activation", "previous_image_health"])
                self.assertIn("ROLLBACK_REQUIRES_ATTENTION", output)
                self.assertNotIn("ROLLBACK_PASS", output)

    def test_previous_image_activation_failure_still_attempts_health_and_records_both(self):
        _, result, output = self.exercise(activation_error=True, health_error=True)
        self.assertEqual(result["errors"], ["previous_image_activation", "previous_image_health"])
        self.assertIn("ROLLBACK_REQUIRES_ATTENTION", output)

    def test_successful_recovery_records_pass_but_preserves_original_failure(self):
        _, result, output = self.exercise()
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["previous_image"], "previous:retained")
        self.assertIn("ROLLBACK_PASS", output)

    def test_failure_before_switch_restores_data_without_recreating_live_web(self):
        _, result, _ = self.exercise(copy_error=True, switched=False)
        self.assertEqual(result["errors"], ["homepage_restore"])


if __name__ == "__main__":
    unittest.main()
