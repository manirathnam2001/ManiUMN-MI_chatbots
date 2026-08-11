"""Test rubric directory path resolution.

This file previously hardcoded the GitHub Actions runner path
`/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots`. Locally that path
does not exist, so every check silently took a `continue` branch and the suite
looked green. On CI the path did exist, so the assertions ran and failed. The
failures went unnoticed because the previous CI workflow never ran the suite.

The repo root is now derived from this file's own location, so the tests behave
identically everywhere.

The assertions also used to target `pages/OHI.py` and `pages/HPV.py` directly.
Rubric loading moved into `mi_session._load_rubric_text` when the bot pages
became thin shells, so the tests now target that function.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

RUBRIC_DIRS = ("ohi_rubrics", "hpv_rubrics", "perio_rubrics", "tobacco_rubrics")


def test_repo_root_is_discoverable():
    """The derived repo root must actually be the repo root."""
    assert (REPO_ROOT / "mi_session.py").exists(), \
        f"Expected mi_session.py under the derived repo root {REPO_ROOT}"
    assert (REPO_ROOT / "secret_code_portal.py").exists(), \
        f"Expected secret_code_portal.py under the derived repo root {REPO_ROOT}"


def test_resolution_logic_works_from_root_and_from_pages():
    """The candidate-list strategy must find rubrics from either location.

    `_load_rubric_text` resolves against its own file location and tries both
    `<dir>/<name>` and `<dir>/../<name>`. This reproduces that logic against
    real paths, so it stays honest if the module ever moves.
    """
    for rubric_name in RUBRIC_DIRS:
        # Resolving from a module sitting at the repo root.
        here = REPO_ROOT
        candidates = [here / rubric_name, here.parent / rubric_name]
        resolved = next((p for p in candidates if p.exists() and p.is_dir()), None)
        assert resolved is not None, \
            f"{rubric_name} not resolvable from the repo root"

        # Resolving from a module sitting one level down, as pages/ modules do.
        here = REPO_ROOT / "pages"
        candidates = [here / rubric_name, here.parent / rubric_name]
        resolved = next((p for p in candidates if p.exists() and p.is_dir()), None)
        assert resolved is not None, \
            f"{rubric_name} not resolvable from pages/"


def test_rubric_loader_uses_file_relative_resolution():
    """`_load_rubric_text` must not depend on the process working directory.

    A bare relative path here would break under Apptainer, under Slurm, and any
    time the app is launched from another directory.
    """
    source = (REPO_ROOT / "mi_session.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    loader = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name == "_load_rubric_text"),
        None,
    )
    assert loader is not None, "mi_session must define _load_rubric_text"

    body = ast.get_source_segment(source, loader) or ""
    assert "__file__" in body, \
        "_load_rubric_text must resolve relative to __file__, not the working directory"
    assert "Path(" in body, "_load_rubric_text must use pathlib"


def test_rubric_loader_fails_gracefully():
    """A missing rubric directory must produce a message, not a traceback."""
    source = (REPO_ROOT / "mi_session.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    loader = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name == "_load_rubric_text"),
        None,
    )
    assert loader is not None, "mi_session must define _load_rubric_text"

    body = ast.get_source_segment(source, loader) or ""
    assert "st.error" in body, \
        "_load_rubric_text must surface a user-facing error"
    assert "st.stop" in body, \
        "_load_rubric_text must halt rendering rather than continue with no rubric"
    assert "not found" in body or "Configuration error" in body, \
        "_load_rubric_text must explain what is missing"


def test_rubric_directories_exist_and_have_content():
    """All four rubric directories must exist and contain .txt files."""
    for rubric_name in RUBRIC_DIRS:
        rubric_dir = REPO_ROOT / rubric_name
        assert rubric_dir.exists(), f"{rubric_name} directory not found at {rubric_dir}"
        assert rubric_dir.is_dir(), f"{rubric_name} is not a directory"

        txt_files = list(rubric_dir.glob("*.txt"))
        assert txt_files, f"{rubric_name} contains no .txt files"
