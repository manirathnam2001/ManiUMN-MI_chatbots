# MSI Migration Changelog

One entry per phase of the migration described in `MIGRATION_PLAN.md`. Each
entry records what changed, which files, why, and how it was verified.

All entries apply to the `msi-hybrid` branch unless stated otherwise. Nothing in
this changelog reaches the production deployment before the Phase 12 cutover.

---

## Plan amendment, 2026-07-31 (plan version 2.1)

No code changed. Recorded here because it alters the scope of Phase 7.

### Storage split made explicit

Feedback PDFs are archived to Box and are **never** written to MSI. MSI holds
the conversation history, the evaluation results, and the application logs, as a
pseudonymous backend store and fallback.

Version 2.0 of the plan had proposed a Tier 2 S3 PDF archive on MSI. That is
withdrawn. Keeping the one artifact that must carry a student name inside Box,
a UMN-sanctioned system, is both simpler and a stronger position against the
MSI User Agreement prohibition on FERPA-protected data.

### Correction: Box archiving is a regression, not a missing feature

An earlier assessment in this work described Box archiving as "not wired into
the session flow" and treated restoring it as new development. The first half is
accurate for the current code. The second half was wrong, and the framing was
misleading.

Box archiving was fully implemented and working. Each of the four bot pages
carried its own send block calling `RobustEmailSender.send_with_guaranteed_delivery`,
with a progress bar, a persistent retry queue, retry and skip controls, and
download-button gating. It was lost in commit `1656112`, the refactor that
replaced the four fat page files with thin shells over `mi_session.run_practice_session`.
The send block was not carried into the shared runner.

Evidence:

| Item | Location |
|---|---|
| Reference implementation | `git show 1656112^:pages/OHI.py`, lines 356 to 440 |
| Same block in the other three bots | `1656112^:pages/HPV.py`, `Perio.py`, `Tobacco.py` |
| Regression recorded at the time | `mi_session.py:12-13` |
| Reserved hook left by the refactor | `SessionConfig.enable_email_to_box`, `mi_session.py:105` |

Consequence for the plan: Phase 7 ports a known-good implementation rather than
designing a new one. Lower risk, and the download-gating behaviour must be
preserved rather than reinvented.

### Phase 7 rescoped

Retitled from "Session durability and redemption race fix" to "Data persistence
(Box archiving and the MSI backend store)". Estimate raised from 2 days to 3 to
4 days. New requirements:

- `MI_BOX_EMAIL_OVERRIDE`, which must ship in the same commit as the Box
  restoration, otherwise every Track B session emails a real course folder.
- Log scrubbing as a logging filter. `logger_config.py` `log_action` calls carry
  student names, so writing logs to MSI unscrubbed breaches the FERPA boundary
  just as an unscrubbed transcript would.
- Two explicit negative verifications: no PDF under `$MI_STATE_DIR`, and no
  student name anywhere under `$MI_STATE_DIR` or `$MI_LOG_DIR`.

### Stated assumption

An opaque session identifier is generated per session, used as the MSI record
key, and printed in the Box PDF footer. Without it the MSI store cannot function
as a per-student fallback. If the linkage is unwanted, drop the footer line;
the store still works but individual sessions become unrecoverable by student.

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
