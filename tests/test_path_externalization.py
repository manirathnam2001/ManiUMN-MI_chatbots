"""Guards that no runtime path depends on the process working directory.

The application previously wrote to bare relative paths: ``git_logs`` for
application logs and ``SMTP logs`` for the email retry queue, plus a bare
``open('config.json')`` and a bare service-account filename. Those resolve
against the working directory, which is fine only when the app is launched from
the repository root.

Two things make that unacceptable for the migration. Under Apptainer the
application directory is read-only, so the first write fails outright. And a
Slurm job does not necessarily start in the repository root, so even a writable
deployment would put files somewhere unintended.

Phase 8 cannot proceed until every writable path can be redirected, which is
what these tests pin.
"""

import ast
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app_env


REPO_ROOT = Path(__file__).resolve().parent.parent

PATH_VARS = (
    "MI_LOG_DIR",
    "MI_QUEUE_DIR",
    "MI_STATE_DIR",
    "MI_CONFIG_PATH",
    "MI_GOOGLE_SA_FILE",
)

# Modules that resolve or write runtime paths.
PATH_AWARE_MODULES = (
    "app_env.py",
    "logger_config.py",
    "email_utils.py",
    "email_queue.py",
    "secret_code_portal.py",
    "utils/access_control.py",
)


class PathTestCase(unittest.TestCase):
    def setUp(self):
        self._saved = {n: os.environ.get(n) for n in PATH_VARS}
        for n in PATH_VARS:
            os.environ.pop(n, None)

    def tearDown(self):
        for n, v in self._saved.items():
            if v is None:
                os.environ.pop(n, None)
            else:
                os.environ[n] = v


class TestResolversReturnAbsolutePaths(PathTestCase):
    """Every resolver must be absolute, configured or not."""

    def test_defaults_are_absolute(self):
        for name, value in (
            ("log dir", app_env.get_log_dir()),
            ("queue dir", app_env.get_queue_dir()),
            ("state dir", app_env.get_state_dir()),
            ("config path", app_env.get_config_path()),
            ("service account", app_env.get_google_sa_file()),
        ):
            with self.subTest(name=name):
                self.assertTrue(
                    os.path.isabs(value),
                    f"{name} resolved to a relative path: {value}",
                )

    def test_overrides_are_absolute(self):
        os.environ["MI_LOG_DIR"] = "/var/log/mi"
        os.environ["MI_QUEUE_DIR"] = "/var/spool/mi"
        self.assertTrue(os.path.isabs(app_env.get_log_dir()))
        self.assertTrue(os.path.isabs(app_env.get_queue_dir()))

    def test_a_relative_override_resolves_against_the_app_root_not_the_cwd(self):
        """A relative value must not reintroduce working-directory dependence."""
        os.environ["MI_LOG_DIR"] = "somewhere/logs"
        resolved = app_env.get_log_dir()
        self.assertTrue(os.path.isabs(resolved))
        self.assertTrue(
            resolved.startswith(str(REPO_ROOT)),
            f"relative override escaped the app root: {resolved}",
        )


class TestOverridesAreHonoured(PathTestCase):
    def test_each_variable_redirects_its_path(self):
        for var, getter in (
            ("MI_LOG_DIR", app_env.get_log_dir),
            ("MI_QUEUE_DIR", app_env.get_queue_dir),
            ("MI_STATE_DIR", app_env.get_state_dir),
            ("MI_CONFIG_PATH", app_env.get_config_path),
            ("MI_GOOGLE_SA_FILE", app_env.get_google_sa_file),
        ):
            with self.subTest(var=var):
                os.environ[var] = "/tmp/mi-target"
                self.assertEqual(getter(), os.path.abspath("/tmp/mi-target"))
                os.environ.pop(var)


class TestDefaultsPreserveTodaysLayout(PathTestCase):
    """An unconfigured deployment keeps the previous directory names."""

    def test_log_dir_default_is_git_logs(self):
        self.assertEqual(os.path.basename(app_env.get_log_dir()), "git_logs")

    def test_config_path_default_is_repo_config_json(self):
        self.assertEqual(app_env.get_config_path(), str(REPO_ROOT / "config.json"))
        self.assertTrue(os.path.exists(app_env.get_config_path()))


class TestQueueDirectoryRename(PathTestCase):
    """The queue directory no longer contains a space."""

    def test_default_queue_dir_has_no_space(self):
        # A space in this path had to be quoted in every shell command, Slurm
        # script and Apptainer bind argument that referenced it.
        self.assertNotIn(" ", os.path.basename(app_env.get_queue_dir()))
        self.assertEqual(os.path.basename(app_env.get_queue_dir()), "smtp_queue")

    def test_legacy_dir_is_still_locatable_for_migration(self):
        # Retained for one release so queued reports are not stranded.
        self.assertEqual(
            os.path.basename(app_env.get_legacy_queue_dir()), "SMTP logs"
        )


class TestNoBareRelativePathsRemain(PathTestCase):
    """The literals that caused the problem must not reappear in code."""

    def test_no_module_opens_config_json_by_bare_name(self):
        for module in PATH_AWARE_MODULES:
            source = (REPO_ROOT / module).read_text(encoding="utf-8")
            for bad in ("open('config.json'", 'open("config.json"'):
                self.assertNotIn(
                    bad,
                    source,
                    f"{module} opens config.json by bare name; use "
                    f"app_env.get_config_path()",
                )

    def test_no_module_hardcodes_a_writable_directory_literal(self):
        """Only app_env may name the directories, and only as defaults."""
        for module in PATH_AWARE_MODULES:
            if module == "app_env.py":
                continue
            tree = ast.parse((REPO_ROOT / module).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(
                        node.value,
                        ("git_logs", "SMTP logs", "smtp_queue"),
                        f"{module} line {node.lineno} hardcodes a writable "
                        f"directory; resolve it through app_env",
                    )


if __name__ == "__main__":
    unittest.main()
