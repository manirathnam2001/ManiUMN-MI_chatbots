# MSI Migration Changelog

One entry per phase of the migration described in `MIGRATION_PLAN.md`. Each
entry records what changed, which files, why, and how it was verified.

All entries apply to the `msi-hybrid` branch unless stated otherwise. Nothing in
this changelog reaches the production deployment before the Phase 12 cutover.

---

## Phase 1: Track B setup, safety net, and dead code removal

Date: 2026-07-31
Branch: `msi-hybrid`
Baseline: `main` tagged `pre-msi-baseline`

### Purpose

Isolate the migration environment from production data, and remove dead code
before any refactoring begins so that the baseline test count reflects the
post-deletion state.

### Added

| File | Purpose |
|---|---|
| `app_env.py` | Deployment isolation layer. Resolves the Google Sheet target, the environment label, and the outbound email switch from environment variables, defaulting in every case to current production behaviour |
| `tests/test_app_env.py` | 18 tests covering production defaults, test overrides, boolean parsing, and banner inertness |
| `.github/workflows/ci-msi-hybrid.yml` | Continuous integration for the migration branch. Requires no secrets and makes no network calls. Includes a guard that fails the build if the production sheet ID appears outside `app_env.py` |
| `docs/TRACK_ISOLATION.md` | Reference for configuring both deployments |
| `docs/MSI_MIGRATION_RESEARCH.md` | MSI capability research (written before Phase 1) |

### Changed

| File | Change | Reason |
|---|---|---|
| `secret_code_portal.py` | `SHEET_ID` and `SHEET_NAME` now resolve through `app_env`; module docstring updated; environment banner rendered after `set_page_config` | The hardcoded sheet ID meant any test run would mark a real student access code as used |
| `pages/developer_page.py` | Two hardcoded sheet ID literals replaced; hardcoded `"Sheet1"` replaced; environment banner added | Same |
| `mi_session.py` | Environment banner rendered in `run_practice_session`, covering all four bot pages; docstring updated to reflect the removal of `end_control_middleware` | A student reaching a bot page directly must still see the test warning |
| `email_utils.py` | Added `_smtp_disabled()` and applied it at five entry points | Prevents the migration environment from emailing test reports to the course Box archive, and prevents student PDFs being written to the on-disk retry queue |
| `.gitignore` | Added rules for `git_logs/`, rotated logs, `failed_emails.json`, `queued_*.pdf`, `.streamlit/secrets.toml`, and service account JSON files | None of these were previously ignored. The missing JSON rule is how a Google private key was committed to this repository |
| `runtime.txt` | `python-3.10` to `python-3.11` | Resolves a conflict with the devcontainer. The pressure toward 3.10 came from `torch`, which Phase 2 removes |
| `.devcontainer/devcontainer.json` | `postAttachCommand` now runs `secret_code_portal.py`; removed `--server.enableCORS false --server.enableXsrfProtection false`; `openFiles` corrected | The command referenced a nonexistent root-level `HPV.py`, and disabling CORS and XSRF protection is not an acceptable default |
| `docs/ADMIN_GUIDE.md` | Sheet ID section rewritten to document `MI_SHEET_ID` | The guide instructed administrators to hardcode a sheet ID |

### Removed

| File | Lines | Reason |
|---|---|---|
| `end_control_middleware.py` | 1419 | Dead module. Not imported by any runtime code, only mentioned in a docstring. Contained unsynchronized module-level mutable state that would have been a concurrency defect if reactivated |
| `database/mi_sessions.sql` | 231 | MySQL schema with no driver in `requirements.txt` and no connection code anywhere in the repository. Encoded an obsolete 30-point 4-category rubric while the live rubric is 40 points across 6 categories |
| `test_php_pdf_new_rubric.php` | 178 | Fossil of the same abandoned LAMP direction |
| `tests/test_end_control_middleware.py` | 332 | Tests for the removed module |
| `tests/test_end_control_integration.py` | 316 | Tests for the removed module |
| `tests/test_mutual_intent.py` | 275 | Tests for the removed module |
| `tests/test_semantic_ending.py` | 273 | Tests for the removed module |
| `tests/test_e2e_mutual_intent.py` | 150 | Tests for the removed module |

### Test count

| | Count |
|---|---|
| Before | 245 |
| Removed with `end_control_middleware` | 31 |
| Added in `tests/test_app_env.py` | 18 |
| After | 232 |

The reduction is expected and is recorded here so it is not later mistaken for
a regression.

### Verification

| Check | Result |
|---|---|
| Production sheet ID appears only as the default in `app_env.py` | Confirmed by grep across all Python sources |
| `git_logs/chatbot.log.1` ignored | Confirmed via `git check-ignore` |
| `SMTP logs/failed_emails.json` ignored | Confirmed via `git check-ignore` |
| `SMTP logs/queued_*.pdf` ignored | Confirmed via `git check-ignore` |
| `smtp_queue/queued_*.pdf` ignored | Confirmed via `git check-ignore` |
| `.streamlit/secrets.toml` ignored | Confirmed via `git check-ignore` |
| `umnsod-mibot-*.json` ignored | Confirmed via `git check-ignore` |
| `*service-account*.json` ignored | Confirmed via `git check-ignore` |
| No dangling references to deleted modules | Confirmed by grep; only an explanatory docstring mention remains |
| Test suite passes | **Not run.** No Python interpreter is available on the authoring machine. See below |

### Outstanding

**The test suite has not been executed for this phase.** The authoring machine
has no Python interpreter installed, so `python -m pytest tests/ test_evaluation.py -q`
could not be run. The static checks above were performed instead.

Before Phase 2 begins, the suite must be run on a machine with Python 3.11, and
the result recorded here. The continuous integration workflow added in this
phase will also run it automatically once the branch is pushed.

---
