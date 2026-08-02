"""Pytest configuration for the whole repository.

Guarantees that the test suite runs against production defaults regardless of
what the developer has exported in their shell.

This matters because of the deployment isolation variables introduced in
app_env.py. A developer working on the migration environment will typically have
MI_SMTP_ENABLED=false and MI_SHEET_ID set to a test sheet. Without the fixture
below, those ambient values would leak into the suite and change behaviour under
test. For example, the SMTP gate in email_utils would short-circuit
send_email_with_attachment and test_connection, and the assertions in
tests/test_email_utils.py would fail for reasons that have nothing to do with
the code under test.

Tests that need a non-default value set it themselves and restore it afterwards,
as tests/test_app_env.py does.
"""

import os

import pytest


# Deployment isolation variables owned by app_env.py, plus the paths that
# Phase 5 will introduce. Listed here so a developer's environment can never
# silently change what the suite is testing.
_DEPLOYMENT_ENV_VARS = (
    "MI_SHEET_ID",
    "MI_SHEET_NAME",
    "MI_ENVIRONMENT",
    "MI_SMTP_ENABLED",
    "MI_BOX_EMAIL_OVERRIDE",
    "MI_CONFIG_PATH",
    "MI_LOG_DIR",
    "MI_QUEUE_DIR",
    "MI_STATE_DIR",
)


@pytest.fixture(autouse=True, scope="session")
def _neutralize_deployment_env():
    """Clear deployment isolation variables for the duration of the session."""
    saved = {name: os.environ.get(name) for name in _DEPLOYMENT_ENV_VARS}
    for name in _DEPLOYMENT_ENV_VARS:
        os.environ.pop(name, None)
    try:
        yield
    finally:
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
