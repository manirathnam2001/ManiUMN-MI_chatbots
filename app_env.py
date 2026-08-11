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

Writable paths
--------------
MI_LOG_DIR, MI_QUEUE_DIR, MI_STATE_DIR
    Directories the application writes to at runtime. Each defaults to a
    location beside this file, reproducing today's layout, and each resolves to
    an absolute path.

    These exist because the application previously used bare relative paths,
    resolved against the process working directory. That works only when the app
    is launched from the repository root. Under Apptainer the application
    directory is read-only and the first write fails outright, so Phase 8 cannot
    proceed until every writable path can be pointed somewhere else.

MI_CONFIG_PATH
    Location of config.json.

MI_GOOGLE_SA_FILE
    Google service account JSON, for local development only. Deployments should
    use the GOOGLESA secret instead.
"""

import os


# Production Google Sheet. Retained as the default so that an unconfigured
# deployment continues to behave exactly as before.
_PRODUCTION_SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"

# Resolved from this file rather than the working directory, so behaviour does
# not depend on where the process was started.
_APP_ROOT = os.path.dirname(os.path.abspath(__file__))

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


# ---------------------------------------------------------------------------
# Writable and configured paths
# ---------------------------------------------------------------------------


def _resolve_dir(env_name: str, default_basename: str) -> str:
    """Return an absolute directory path from ``env_name``.

    Falls back to ``default_basename`` beside this file, which reproduces the
    previous layout for an unconfigured deployment. A relative value in the
    environment is resolved against the application root rather than the
    working directory, because the working directory is exactly the variable
    this function exists to remove.
    """
    raw = os.environ.get(env_name)
    if not raw:
        return os.path.join(_APP_ROOT, default_basename)
    return os.path.abspath(os.path.join(_APP_ROOT, os.path.expanduser(raw)))


def get_log_dir() -> str:
    """Directory for application logs."""
    return _resolve_dir("MI_LOG_DIR", "git_logs")


def get_queue_dir() -> str:
    """Directory for the outbound email retry queue.

    Historically named "SMTP logs", with a space. That space had to be quoted
    in every shell command, Slurm script and Apptainer bind argument that
    touched it, so the default is now "smtp_queue". See
    ``get_legacy_queue_dir`` for the migration path.
    """
    return _resolve_dir("MI_QUEUE_DIR", "smtp_queue")


def get_legacy_queue_dir() -> str:
    """Previous queue location, read once so pending items are not stranded.

    Retained for one release. Anything still queued under the old directory
    when this version deploys would otherwise never be sent.
    """
    return os.path.join(_APP_ROOT, "SMTP logs")


def get_state_dir() -> str:
    """Directory for durable session state.

    Introduced here so the path layer is complete in one change. It is consumed
    in Phase 7, where conversation transcripts and evaluation results are
    journaled. On MSI this points at Tier 1 project storage, never
    /scratch.global, which purges files 30 days after creation.
    """
    return _resolve_dir("MI_STATE_DIR", "session_state")


def get_config_path() -> str:
    """Absolute path to config.json."""
    raw = os.environ.get("MI_CONFIG_PATH")
    if not raw:
        return os.path.join(_APP_ROOT, "config.json")
    return os.path.abspath(os.path.join(_APP_ROOT, os.path.expanduser(raw)))


def get_google_sa_file() -> str:
    """Absolute path to the Google service account JSON, for local use only.

    Deployments should supply the GOOGLESA secret instead of a file on disk.
    """
    raw = os.environ.get("MI_GOOGLE_SA_FILE")
    if not raw:
        return os.path.join(_APP_ROOT, "umnsod-mibot-ea3154b145f1.json")
    return os.path.abspath(os.path.join(_APP_ROOT, os.path.expanduser(raw)))


def ensure_writable_dirs() -> None:
    """Create the writable directories if they are missing.

    Called once at startup. Failure is deliberately not swallowed: if these
    cannot be created the application cannot log or queue, and discovering that
    at startup is far better than discovering it when a student finishes a
    session.
    """
    for path in (get_log_dir(), get_queue_dir()):
        os.makedirs(path, exist_ok=True)


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
