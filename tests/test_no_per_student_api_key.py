"""Guards the removal of the per-student LLM credential.

Before this change each student pasted their own Groq API key into the portal.
It was stored in Streamlit session state and then written to ``os.environ``,
which is process-global and shared by every concurrent session. Two students
active at once could clobber each other's keys, so one student's requests could
be billed to another student's account, nondeterministically.

The credential is now operator-held and read from the environment by
``llm_provider.load_settings``. These tests assert the old path cannot come
back by accident, since reintroducing it would restore a real cross-user defect
rather than merely undoing a refactor.
"""

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


REPO_ROOT = Path(__file__).resolve().parent.parent

# Modules that run in a request path, where a process-global write would be
# visible to other concurrent users.
REQUEST_PATH_MODULES = (
    "secret_code_portal.py",
    "mi_session.py",
    "pages/developer_page.py",
    "pages/OHI.py",
    "pages/HPV.py",
    "pages/Perio.py",
    "pages/Tobacco.py",
)


def _source(relative_path):
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_no_module_reads_a_per_student_key_from_session_state():
    """``st.session_state.groq_api_key`` must not reappear."""
    for module in REQUEST_PATH_MODULES:
        source = _source(module)
        assert "groq_api_key" not in source, (
            f"{module} references groq_api_key. The LLM credential is "
            f"operator-held; read it through llm_provider.load_settings()."
        )


def test_no_module_writes_the_environment_in_a_request_path():
    """No ``os.environ[...] = ...`` assignment in any request-path module.

    This is the actual defect, not the key field itself. A per-request write to
    a process-global mapping races across concurrent Streamlit sessions.
    """
    for module in REQUEST_PATH_MODULES:
        tree = ast.parse(_source(module))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Subscript):
                    continue
                value = target.value
                is_environ = (
                    isinstance(value, ast.Attribute)
                    and value.attr == "environ"
                ) or (isinstance(value, ast.Name) and value.id == "environ")
                assert not is_environ, (
                    f"{module} line {node.lineno} assigns into os.environ. "
                    f"That is process-global and races across concurrent "
                    f"users; pass configuration explicitly instead."
                )


def test_portal_does_not_ask_students_for_an_api_key():
    source = _source("secret_code_portal.py")
    lowered = source.lower()
    assert "api key" not in lowered, (
        "The portal must not prompt for an API key. The credential is "
        "supplied by the operator through MI_LLM_API_KEY."
    )
    assert "console.groq.com" not in lowered, (
        "The portal must not direct students to obtain their own key."
    )


def test_auth_guards_require_only_the_student_name():
    """The guards must not gate on a credential that no longer exists.

    If they did, every student would be bounced back to the portal, because
    nothing populates that session key any more.
    """
    for module in ("mi_session.py", "pages/developer_page.py"):
        source = _source(module)
        assert "student_name" in source, f"{module} should still require student_name"
        assert "groq_api_key" not in source, (
            f"{module} still gates on groq_api_key, which is never set now"
        )
