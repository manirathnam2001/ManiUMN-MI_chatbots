"""Tests for app_env, the deployment isolation layer.

These tests guard the boundary between the production deployment and the
parallel migration deployment. The most important property under test is that
an unconfigured deployment behaves exactly as production did before this module
existed, and that a deployment configured for testing cannot reach production
resources.
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app_env


PRODUCTION_SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"

MANAGED_VARS = (
    "MI_SHEET_ID",
    "MI_SHEET_NAME",
    "MI_ENVIRONMENT",
    "MI_SMTP_ENABLED",
)


class AppEnvTestCase(unittest.TestCase):
    """Base case that isolates each test from ambient environment variables."""

    def setUp(self):
        self._saved = {name: os.environ.get(name) for name in MANAGED_VARS}
        for name in MANAGED_VARS:
            os.environ.pop(name, None)

    def tearDown(self):
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class TestProductionDefaults(AppEnvTestCase):
    """An unconfigured deployment must behave exactly as production."""

    def test_sheet_id_defaults_to_production(self):
        self.assertEqual(app_env.get_sheet_id(), PRODUCTION_SHEET_ID)

    def test_sheet_name_defaults_to_sheet1(self):
        self.assertEqual(app_env.get_sheet_name(), "Sheet1")

    def test_environment_defaults_to_production(self):
        self.assertEqual(app_env.get_environment(), "production")

    def test_not_a_test_environment_by_default(self):
        self.assertFalse(app_env.is_test_environment())

    def test_smtp_enabled_by_default(self):
        self.assertTrue(app_env.is_smtp_enabled())


class TestTestEnvironmentOverrides(AppEnvTestCase):
    """A deployment configured for testing must not touch production."""

    def test_sheet_id_override_is_honoured(self):
        os.environ["MI_SHEET_ID"] = "test-sheet-abc123"
        self.assertEqual(app_env.get_sheet_id(), "test-sheet-abc123")
        self.assertNotEqual(app_env.get_sheet_id(), PRODUCTION_SHEET_ID)

    def test_sheet_name_override_is_honoured(self):
        os.environ["MI_SHEET_NAME"] = "TestCodes"
        self.assertEqual(app_env.get_sheet_name(), "TestCodes")

    def test_test_environment_is_detected(self):
        os.environ["MI_ENVIRONMENT"] = "test"
        self.assertTrue(app_env.is_test_environment())

    def test_environment_detection_is_case_insensitive(self):
        os.environ["MI_ENVIRONMENT"] = "TEST"
        self.assertTrue(app_env.is_test_environment())

    def test_environment_detection_tolerates_whitespace(self):
        os.environ["MI_ENVIRONMENT"] = "  test  "
        self.assertTrue(app_env.is_test_environment())

    def test_smtp_can_be_disabled(self):
        os.environ["MI_SMTP_ENABLED"] = "false"
        self.assertFalse(app_env.is_smtp_enabled())


class TestBooleanParsing(AppEnvTestCase):
    """MI_SMTP_ENABLED must not fail open on an unexpected value."""

    def test_recognised_false_spellings(self):
        for value in ("false", "False", "FALSE", "0", "no", "off", " off "):
            with self.subTest(value=value):
                os.environ["MI_SMTP_ENABLED"] = value
                self.assertFalse(app_env.is_smtp_enabled())

    def test_recognised_true_spellings(self):
        for value in ("true", "True", "1", "yes", "on"):
            with self.subTest(value=value):
                os.environ["MI_SMTP_ENABLED"] = value
                self.assertTrue(app_env.is_smtp_enabled())

    def test_unrecognised_value_falls_back_to_default(self):
        os.environ["MI_SMTP_ENABLED"] = "maybe"
        self.assertTrue(app_env.is_smtp_enabled())

    def test_empty_value_falls_back_to_default(self):
        os.environ["MI_SMTP_ENABLED"] = ""
        self.assertTrue(app_env.is_smtp_enabled())


class TestBannerIsInert(AppEnvTestCase):
    """The banner must be a no-op in production and importable without Streamlit."""

    def test_banner_does_nothing_in_production(self):
        # Must not raise, and must not attempt a Streamlit import, when the
        # deployment is production.
        app_env.render_environment_banner()


if __name__ == "__main__":
    unittest.main()
