"""LLM provider abstraction.

Lets the application talk to either Groq or a self-hosted vLLM server without
any change to calling code, so migrating inference to MSI is a configuration
change rather than a code change.

Both providers expose an OpenAI-compatible API, and the ``openai`` SDK accepts
``base_url`` and ``api_key`` as explicit constructor arguments. Switching
providers is therefore a matter of pointing ``MI_LLM_BASE_URL`` somewhere else.

Design constraints
------------------
The object returned by :func:`make_client` must expose
``client.chat.completions.create(...)`` unchanged. The evaluation test suite
drives that surface directly through its ``FakeClient``, and more than twenty
tests depend on it. Do not wrap the client in a bespoke ``generate()`` facade:
that would break the tests and, worse, hide the provider differences this
module exists to normalise.

Every default reproduces current Groq behaviour, so an unconfigured deployment
behaves exactly as it did before this module existed.

Environment variables
---------------------
MI_LLM_BASE_URL
    OpenAI-compatible endpoint. Defaults to Groq. For MSI, point at the vLLM
    server, for example ``http://cn1234:8000/v1``.

MI_LLM_API_KEY
    Credential for that endpoint. vLLM commonly ignores the value but still
    requires one to be present.

MI_LLM_CHAT_MODEL, MI_LLM_EVAL_MODEL, MI_LLM_EXTRACTOR_MODEL
    Model names. Under vLLM these are the ``--served-model-name`` values, which
    will not match the Groq names.

MI_LLM_TIMEOUT_S, MI_LLM_EVAL_TIMEOUT_S
    Request timeouts in seconds. The evaluator gets a longer one: a 70B model on
    shared HPC is markedly slower than Groq.

MI_LLM_MAX_RETRIES
    Passed to the SDK, which retries connection failures, 429s and 5xx with
    backoff.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Optional

import openai


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

# Single source of truth for model names, replacing four literals that were
# previously scattered across mi_session and mi_evaluation.
#
# These defaults are Groq model names and are asserted verbatim by
# test_evaluation.py and tests/test_mi_evaluation.py. Changing them without
# updating those tests will fail the suite, which is the intended safeguard.
MODELS = {
    # Patient turns and evidence extraction. Small and fast.
    "chat": "llama-3.1-8b-instant",
    "extractor": "llama-3.1-8b-instant",
    # MI scoring. Large and slow, and the quality-critical call.
    "eval": "llama-3.3-70b-versatile",
}

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LLMSettings:
    """Resolved configuration for one LLM endpoint."""

    base_url: str = GROQ_BASE_URL
    api_key: Optional[str] = None

    chat_model: str = MODELS["chat"]
    eval_model: str = MODELS["eval"]
    extractor_model: str = MODELS["extractor"]

    # Chat turns are short and interactive, so they fail fast.
    timeout_s: float = 30.0
    chat_max_tokens: int = 250

    # Evaluation is a single long blocking call. On a self-hosted 70B this can
    # take minutes, and a cold vLLM start adds several more.
    eval_timeout_s: float = 180.0
    eval_max_tokens: int = 1500
    extractor_max_tokens: int = 1200

    max_retries: int = 2

    @property
    def is_groq(self) -> bool:
        return "api.groq.com" in self.base_url


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def load_settings(api_key: Optional[str] = None) -> LLMSettings:
    """Build settings from the environment.

    An explicit ``api_key`` wins over the environment. That preserves today's
    behaviour, where each student supplies their own key through the portal and
    it is held in Streamlit session state. When the shared-endpoint model
    replaces per-student keys, callers simply stop passing it and the
    environment value is used instead.
    """
    resolved_key = (
        api_key
        or os.environ.get("MI_LLM_API_KEY")
        # Accepted so an existing deployment keeps working unchanged.
        or os.environ.get("GROQ_API_KEY")
    )

    return LLMSettings(
        base_url=os.environ.get("MI_LLM_BASE_URL", GROQ_BASE_URL),
        api_key=resolved_key,
        chat_model=os.environ.get("MI_LLM_CHAT_MODEL", MODELS["chat"]),
        eval_model=os.environ.get("MI_LLM_EVAL_MODEL", MODELS["eval"]),
        extractor_model=os.environ.get(
            "MI_LLM_EXTRACTOR_MODEL", MODELS["extractor"]
        ),
        timeout_s=_env_float("MI_LLM_TIMEOUT_S", 30.0),
        eval_timeout_s=_env_float("MI_LLM_EVAL_TIMEOUT_S", 180.0),
        max_retries=_env_int("MI_LLM_MAX_RETRIES", 2),
    )


def make_client(settings: Optional[LLMSettings] = None) -> openai.OpenAI:
    """Return a configured OpenAI-compatible client.

    The returned object exposes ``chat.completions.create(...)``, which is the
    surface every call site and the test suite relies on.
    """
    settings = settings or load_settings()

    return openai.OpenAI(
        base_url=settings.base_url,
        # vLLM usually ignores the credential but the SDK requires a non-empty
        # value, so a placeholder is supplied when none is configured.
        api_key=settings.api_key or "not-required",
        timeout=settings.timeout_s,
        max_retries=settings.max_retries,
    )


def with_api_key(settings: LLMSettings, api_key: Optional[str]) -> LLMSettings:
    """Return a copy of ``settings`` carrying a different credential."""
    return replace(settings, api_key=api_key)


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------
#
# These replace substring matching on exception text. The previous strings were
# written against Groq's error messages and do not match what vLLM returns, so
# on vLLM the extractor fallback in mi_evaluation would have stopped working
# silently: the fallback would never trigger and the error would surface as an
# outright failure instead.
#
# Typed SDK exceptions are checked first. String matching is retained only as a
# last resort, because the test suite raises plain exceptions through its fake
# client and because a provider may return an unexpected shape.


def _message_of(exc: BaseException) -> str:
    return str(exc).lower()


def is_unknown_model(exc: BaseException) -> bool:
    """True when the endpoint does not recognise the requested model."""
    if isinstance(exc, openai.NotFoundError):
        return True
    status = getattr(exc, "status_code", None)
    if status == 404:
        return True

    # Substring fallback. "does not exist" covers vLLM, whose message reads
    # "The model `X` does not exist."
    msg = _message_of(exc)
    return (
        "model_not_found" in msg
        or "does not exist" in msg
        or "unknown model" in msg
        or "not available" in msg
    )


def is_unsupported_response_format(exc: BaseException) -> bool:
    """True when the endpoint rejected the JSON response_format request."""
    if isinstance(exc, openai.BadRequestError):
        body = getattr(exc, "body", None)
        if isinstance(body, dict) and body.get("param") == "response_format":
            return True

    msg = _message_of(exc)
    return "response_format" in msg or "json_object" in msg


def is_auth_error(exc: BaseException) -> bool:
    """True when the credential was rejected."""
    if isinstance(exc, openai.AuthenticationError):
        return True
    status = getattr(exc, "status_code", None)
    if status in (401, 403):
        return True

    msg = _message_of(exc)
    return (
        "401" in msg
        or "invalid api key" in msg
        or "invalid_api_key" in msg
        or "authentication" in msg
    )


def is_retryable(exc: BaseException) -> bool:
    """True for transport and capacity failures worth retrying.

    The SDK already retries these internally according to ``max_retries``. This
    predicate exists for call sites that need to distinguish a transient
    failure from a permanent one when deciding what to show a student.
    """
    return isinstance(
        exc,
        (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
        ),
    )


def describe_endpoint(settings: Optional[LLMSettings] = None) -> str:
    """Short human-readable description, for logs and developer tooling."""
    settings = settings or load_settings()
    provider = "Groq" if settings.is_groq else "self-hosted"
    return f"{provider} at {settings.base_url}"
