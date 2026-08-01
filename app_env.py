"""
Deployment environment settings.

This module holds the small set of settings that differ between the production
deployment and the parallel migration environment. It exists so that the two can
run from the same codebase without sharing any live resource.

Every value defaults to current production behaviour, so an unconfigured
deployment behaves exactly as it did before this module was introduced.

Environment variables
---------------------
MI_SHEET_ID
    Google Sheet holding the access codes. Defaults to the production sheet.
    The migration environment must point this at a separate test sheet,
    otherwise testing marks real student codes as used and locks those
    students out of production.

MI_SHEET_NAME
    Worksheet name within that sheet. Defaults to "Sheet1".

MI_ENVIRONMENT
    Free-form deployment label. Set to "test" to display a banner warning that
    the deployment is not for student use. Defaults to "production".

MI_SMTP_ENABLED
    Set to "false" to suppress every outbound SMTP connection attempt. The
    migration environment uses this so test reports cannot reach the course Box
    archive and so the startup queue drain cannot attempt a live login.
    Defaults to enabled.
"""

import os


# Production Google Sheet. Retained as the default so that an unconfigured
# deployment continues to behave exactly as before.
_PRODUCTION_SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"

_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


def _env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable, tolerating common spellings."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    return default


def get_sheet_id() -> str:
    """Return the Google Sheet ID this deployment reads access codes from."""
    return os.environ.get("MI_SHEET_ID", _PRODUCTION_SHEET_ID)


def get_sheet_name() -> str:
    """Return the worksheet name within the access code sheet."""
    return os.environ.get("MI_SHEET_NAME", "Sheet1")


def get_environment() -> str:
    """Return the deployment label, for example "production" or "test"."""
    return os.environ.get("MI_ENVIRONMENT", "production").strip().lower()


def is_test_environment() -> bool:
    """Return True when this deployment must not be used by students."""
    return get_environment() == "test"


def is_smtp_enabled() -> bool:
    """Return True when outbound SMTP connections are permitted."""
    return _env_bool("MI_SMTP_ENABLED", True)


def render_environment_banner() -> None:
    """Display a prominent warning when running outside production.

    Imported lazily inside the function so this module stays importable from
    non-Streamlit contexts such as tests and command line utilities.
    """
    if not is_test_environment():
        return
    import streamlit as st

    st.error(
        "TEST ENVIRONMENT. Not for student use. "
        "Sessions run here are not recorded against any course and access "
        "codes are drawn from a test sheet."
    )
