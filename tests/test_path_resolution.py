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
became thin shells.

That loader has since been removed by PR #117, because it read the rubric text
and immediately discarded it: the strict-JSON evaluator carries its own
self-contained prompt. Nothing loads rubrics at runtime today.

What survives is a configuration invariant. Every bot page still declares a
`rubric_dir_name` on its `SessionConfig`, and those directories are retained so
retrieval can be reinstated later. The tests below assert that the declared
names actually exist on disk with content, which is the part that can still
silently rot.

If rubric loading is ever restored, restore file-relative resolution with it:
resolve against `__file__`, never the process working directory, or it will
break under Apptainer and Slurm.
"""

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

PAGES = ("OHI.py", "HPV.py", "Perio.py", "Tobacco.py")


def _declared_rubric_dirs():
    """Return the rubric_dir_name declared by each bot page.

    Parsed from the source rather than hardcoded, so a page that renames or
    drops its rubric directory is caught rather than silently diverging from
    this test's own list.
    """
    declared = {}
    for page in PAGES:
        path = REPO_ROOT / "pages" / page
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "rubric_dir_name":
                if isinstance(node.value, ast.Constant):
                    declared[page] = node.value.value
    return declared


def test_repo_root_is_discoverable():
    """The derived repo root must actually be the repo root."""
    assert (REPO_ROOT / "mi_session.py").exists(), \
        f"Expected mi_session.py under the derived repo root {REPO_ROOT}"
    assert (REPO_ROOT / "secret_code_portal.py").exists(), \
        f"Expected secret_code_portal.py under the derived repo root {REPO_ROOT}"


def test_every_page_declares_a_rubric_dir():
    """All four bot pages must declare a rubric_dir_name."""
    declared = _declared_rubric_dirs()
    missing = [p for p in PAGES if p not in declared]
    assert not missing, f"pages missing a rubric_dir_name declaration: {missing}"


def test_declared_rubric_dirs_exist_with_content():
    """Every declared rubric directory must exist and hold .txt files.

    Nothing reads these at runtime since PR #117 removed the loader, so a typo
    or a rename would otherwise go unnoticed until retrieval is reinstated.
    """
    for page, rubric_name in sorted(_declared_rubric_dirs().items()):
        rubric_dir = REPO_ROOT / rubric_name
        assert rubric_dir.exists(), \
            f"{page} declares {rubric_name}, but {rubric_dir} does not exist"
        assert rubric_dir.is_dir(), \
            f"{page} declares {rubric_name}, which is not a directory"

        txt_files = list(rubric_dir.glob("*.txt"))
        assert txt_files, \
            f"{page} declares {rubric_name}, which contains no .txt files"


def test_declared_rubric_dirs_resolve_from_root_and_from_pages():
    """Rubric directories must be reachable from either module location.

    A module at the repo root and a module in pages/ must both be able to find
    them by trying `<dir>/<name>` then `<dir>/../<name>`. This is the resolution
    strategy any restored loader should use, anchored on `__file__` rather than
    the process working directory.
    """
    for rubric_name in sorted(set(_declared_rubric_dirs().values())):
        for origin in (REPO_ROOT, REPO_ROOT / "pages"):
            candidates = [origin / rubric_name, origin.parent / rubric_name]
            resolved = next(
                (p for p in candidates if p.exists() and p.is_dir()), None
            )
            assert resolved is not None, \
                f"{rubric_name} not resolvable from {origin}"
