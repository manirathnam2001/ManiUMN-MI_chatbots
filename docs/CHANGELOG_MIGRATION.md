# MSI Migration Changelog

One entry per phase of the migration described in `MIGRATION_PLAN.md`. Each
entry records what changed, which files, why, and how it was verified.

All entries apply to the `msi-hybrid` branch unless stated otherwise. Nothing in
this changelog reaches the production deployment before the Phase 12 cutover.

---

## Phase 1 safety review, 2026-08-01

A review of whether the branch can break the running application. One real
defect was found and fixed. Everything else was verified clean.

### Defect found and fixed: ambient environment leaked into the test suite

Five tests in `tests/test_email_utils.py` assert on the behaviour of
`send_email_with_attachment` and `test_connection`. The SMTP gate added in
Phase 1 returns early from both when `MI_SMTP_ENABLED=false`. A developer
working on the migration environment will have exactly that variable exported,
because it is the documented Track B setting. Running the suite in that shell
would have produced five failures unrelated to any code change.

Fixed by adding a repository-root `conftest.py` with a session-scoped autouse
fixture that clears the deployment isolation variables for the duration of the
run and restores them afterwards. Tests needing a non-default value set it
themselves, as `tests/test_app_env.py` does.

Five regression tests were added to pin the boundary the gate depends on: that
SMTP is enabled when the variable is unset, that it closes only on an explicit
false, that unparseable values fail safe to enabled, and that the sheet ID and
worksheet name defaults are exactly the production values.

### Verified clean

| Check | Method | Result |
|---|---|---|
| Production branch untouched | `git diff main pre-msi-baseline` | Empty |
| Nothing pushed | `git log origin/main..msi-hybrid` | Local only |
| No tracked file became ignored | `git ls-files \| git check-ignore --stdin` | Empty |
| No test references a deleted path | grep for `mi_sessions`, `end_control`, `test_php` across tests | Empty |
| No runtime import of the deleted module | grep across all `.py` | Only an explanatory docstring |
| No circular import | `app_env` imports only `os` at module scope; Streamlit is imported lazily and only in the test-environment branch | Safe |
| `self.logger` always set before the gate runs | `SecureEmailSender.__init__:60`; `RobustEmailSender.__init__:538` calls `super().__init__` | Safe |
| `app_env` resolves wherever `email_utils` does | Both at repository root; pytest inserts the package root because `tests/` has `__init__.py` | No new failure mode |

### Runtime behaviour with no environment variables set

Every added runtime line is either an import, a lookup that returns the previous
hardcoded value, or a call that returns immediately.

| Element | Default behaviour |
|---|---|
| `SHEET_ID` | The production sheet literal, unchanged |
| `SHEET_NAME` | `Sheet1`, unchanged |
| `render_environment_banner()` | Returns before importing Streamlit |
| SMTP gate | Open. No method short-circuits |
| Deleted modules | Never imported at runtime |

**One genuine difference remains:** `runtime.txt` moved from `python-3.10` to
`python-3.11`. Every pinned dependency supports 3.11, but this changes the
interpreter a deployment from this branch would build against. It does not
affect production, which is on `main` at 3.10.

### Test count after this review

| | Count |
|---|---|
| After Phase 1 | 230 |
| Added by this review | 5 |
| After | 235 |

### Suite executed, 2026-08-02

The branch was pushed and continuous integration ran the suite. To classify the
failures, the identical suite was also run against the frozen baseline from a
temporary branch created at the `pre-msi-baseline` tag. That branch has since
been deleted.

| Run | Result |
|---|---|
| Baseline (`pre-msi-baseline`, equals production `main`) | 17 failed, 226 passed, 2 skipped |
| Migration branch (`msi-hybrid`) | 17 failed, 216 passed, 2 skipped |

**The two failure sets are identical.** Comparing them in both directions
produced no differences:

```
comm -13 baseline_failures branch_failures   ->  empty
comm -23 baseline_failures branch_failures   ->  empty
```

**This branch introduces zero new test failures.** All 17 failures pre-date the
migration work and are present on production `main` today.

The passed count differs because of the deliberate test changes:
226 minus 31 removed with `end_control_middleware` plus 21 in
`tests/test_app_env.py` equals 216.

### Pre-existing failures inherited from earlier refactors

These are not caused by the migration and are not fixed by it. They are recorded
because a permanently red suite is a weak safety net, and Phase 6 depends on the
suite as its regression signal for scoring changes.

| Count | File | Cause |
|---|---|---|
| 1 | `tests/test_multipage_integration.py` | Asserts `AUTHENTICATION GUARD` appears in `pages/OHI.py`. Commit `1656112` made the bot pages thin shells, moving the guard into `mi_session._auth_guard` |
| 2 | `tests/test_path_resolution.py` | Assert `pages/OHI.py` imports `Path` and contains error handling. Same cause: the logic moved into `mi_session` |
| 14 | `tests/test_secret_code_googlesa.py` | Patch `secret_code_portal.gspread`, but that module never imported `gspread` directly. It uses `utils.access_control`, where the real client lives |

All 17 are stale assertions about code layout, not product defects. The
application behaves correctly; the tests describe a structure that no longer
exists. Recommended as a cleanup before Phase 6, so that a red suite means
something again.

---

## Phase 4: retire the per-student API key

Date: 2026-08-11
Branch: `msi/phase-4-api-keys`
Pull request: #123
Plan reference: `MIGRATION_PLAN.md` section 9
Result: **254 passed, 2 skipped, 0 failed.**

### Purpose

Move the LLM credential from each student to the operator, read from the
environment by `llm_provider`, in preparation for a single shared MSI endpoint.

### This closed a real defect

The key was held in Streamlit session state and then written to `os.environ`,
which is process-global and shared by every concurrent session. Two students
active at the same time could clobber each other's keys, so one student's
requests could be billed to another student's account, and which one won was
nondeterministic.

PR #117 had already removed the read side of that race, by passing the key to
the client explicitly instead of reading it back from the environment. This
phase removed the write side, and the concept.

### Removed

- The API key field, its validation branch, the session-state store and the
  `os.environ` write in `secret_code_portal.py`
- The now-unused `import os` there
- A pre-existing unused `import os` in `pages/developer_page.py`, which pyflakes
  had been reporting as advisory since Phase 2

### Changed

| Item | Change |
|---|---|
| `mi_session._auth_guard` | Requires `student_name` only |
| `pages/developer_page.py` guard | Same |
| Auth error message | No longer tells students to re-enter a key they never supplied. Points at the instructor, logs the detail for the operator |
| `run_practice_session` | Calls `load_settings()` with no argument, so the credential comes from `MI_LLM_API_KEY` |
| `tests/test_flow_simulation.py` | Narrated the old credential flow; now describes the operator-held one |

Reducing the guards mattered more than it looks. Leaving `groq_api_key` in the
condition would have bounced **every** student back to the portal, because
nothing populates that session key any more.

### Added

`tests/test_no_per_student_api_key.py`. The load-bearing test walks the AST of
every request-path module asserting there is no assignment into `os.environ`,
because the environment write is the actual defect rather than the input field.
A grep for the field name alone would not catch someone reintroducing the write
under a different name.

### One test inverted

`test_portal_credentials` asserted the portal **has** a Groq API key input. That
requirement no longer exists, so the assertion was inverted and the test renamed
to `test_portal_collects_only_the_student_name`, with a docstring explaining why,
so a future reader does not "fix" it by restoring the field and the race with it.

CI caught this on the first run. Against the old 17-failure baseline it would
have been lost in the noise, which is the argument for the zero-failure gate in
practice rather than in principle.

### Deliberately not touched

`config_loader.get_groq_api_key()` and its tests remain. It is dead code with no
callers that reads only environment variables, so it is harmless. Removing it
means removing its tests, which is outside this phase.

### Rollback

Operator-level: point `MI_LLM_BASE_URL` at Groq and set `MI_LLM_API_KEY` to one
operator key. Per the approved decision there is no per-student fallback path,
which is deliberate, since that path is the race.

### Coordination required at cutover, not before

This changes the student-facing form. Onboarding instructions telling students
to obtain their own Groq key must be updated at cutover. Production still runs
the old flow, so those instructions remain correct until then.

---

## Phase 3: LLM provider abstraction

Date: 2026-08-11
Branch: `msi/phase-3-llm-provider`
Pull request: #122
Plan reference: `MIGRATION_PLAN.md` section 8
Result: **250 passed, 2 skipped, 0 failed. No existing test edited.**

### Purpose

The keystone phase. It converts "move inference to MSI" from a rewrite into a
deployment: switching Groq for a self-hosted vLLM server becomes a change of
`MI_LLM_BASE_URL`.

### Added

`llm_provider.py`, providing `LLMSettings`, a `MODELS` registry replacing four
scattered literals, `load_settings()` reading `MI_LLM_*` with Groq-shaped
defaults, `make_client()` returning an `openai.OpenAI`, and provider-portable
error classifiers.

`tests/test_llm_provider.py`, 23 tests.

### Changed

The `groq` SDK was replaced by `openai`. The openai SDK speaks to any
OpenAI-compatible endpoint, which both Groq and vLLM are, and accepts
`base_url` and `api_key` as explicit constructor arguments.

| File | Change |
|---|---|
| `mi_session.py` | Client built by `make_client(load_settings(...))`; annotations to `Any`; models resolved from settings; auth branch uses `is_auth_error` |
| `mi_evaluation.py` | Model defaults from the registry; `_call_llm` accepts `max_tokens` and `timeout`; classifiers delegate to `llm_provider` |
| `requirements.txt` | `groq==1.6.0` replaced by `openai==2.53.0` |
| `conftest.py` | `MI_LLM_*` added to the neutralised set |

### The defect this phase fixes before it could bite

`_looks_like_unknown_model` matched only Groq's error text. vLLM returns
``The model `X` does not exist.``

On vLLM the extractor fallback in `_extract_evidence` would therefore **never
have triggered**. Instead of quietly retrying with the scoring model, the entire
evaluation would have failed. That would almost certainly have been
misdiagnosed as a vLLM problem during Phase 9, which is why the plan made this a
prerequisite for it.

Classification now inspects typed `openai` exceptions and status codes first,
with substring matching only as a last resort, because the suite raises plain
exceptions through its fake client. Tests pin both the Groq and vLLM shapes.

### Bounds that did not previously exist

The evaluator calls carried no `max_tokens` at all. Survivable against Groq, not
against a self-hosted 70B: vLLM defaults generation to the remaining context
window, so a degenerate response can run for minutes.

| Call | Before | After |
|---|---|---|
| Chat turn | `max_tokens=250`, no timeout | plus `timeout=30s` |
| Evaluator, scorer | none | `max_tokens=1500`, `timeout=180s` |
| Evaluator, extractor | none | `max_tokens=1200`, `timeout=180s` |
| Client | no retries | `max_retries=2` |

Both are omitted from the request when `None`, so callers that do not set them
are unaffected.

### Two decisions worth recording

**The client duck type was preserved deliberately.** `make_client` returns an
object exposing `chat.completions.create` unchanged, because
`test_evaluation.py`'s `FakeClient` drives that exact path and more than twenty
tests depend on it. A `generate()` facade would have broken them and hidden the
provider differences this module exists to normalise.

That no existing test needed editing is the acceptance test for the abstraction,
and it is the reason the plan stated the constraint up front.

**`SessionConfig.chat_model` and `eval_model` became `Optional[str] = None`**
rather than defaulting to the registry literals. The pages construct
`SessionConfig` at import time, so a literal default would have silently won
over the environment and made the endpoint unconfigurable, quietly defeating the
purpose of the phase.

### Switching provider

```
MI_LLM_BASE_URL=http://<node>:8000/v1
MI_LLM_API_KEY=<any non-empty value>
MI_LLM_CHAT_MODEL=chat-8b
MI_LLM_EVAL_MODEL=eval-70b
```

No code change.

### Incident during this phase

A `git add -A` committed `.claude/worktrees`, three embedded git repositories
that would have broken clones of this repository. Removed from the index in the
following commit and added to `.gitignore`.

### Verification

| Check | Result |
|---|---|
| No `groq` import or construction remains | grep, clean |
| No model literal outside the registry | grep, clean |
| `groq` absent from `requirements.txt` and the lockfile | Confirmed |
| Existing tests edited | **None** |
| Pins match the lockfile | CI, all eight |
| No undefined names | pyflakes, CI |
| Suite | 250 passed, 0 failed |

---

## Phase 2: dependency prune, pin, and lock

Date: 2026-08-11
Branch: `msi/phase-2-deps`
Pull request: #121
Plan reference: `MIGRATION_PLAN.md` section 7

### Purpose

Reduce the runtime surface before it is baked into an Apptainer image in
Phase 8. Building the image first would produce a roughly 6 GB artifact with
CUDA layers that is then discarded.

### Removed

| Package | Reason |
|---|---|
| `torch>=2.5.1` | Imported nowhere |
| `sentence-transformers` | Imported nowhere |
| `faiss-cpu` | Imported nowhere |
| `numpy` | Not imported directly. Still installed transitively via `streamlit` |
| `google-auth-oauthlib` | **Not identified in the plan.** Imported nowhere, and there is no interactive OAuth flow: credentials are service-account based. Still installed transitively via `gspread` |

The first four supported a RAG pipeline that no longer exists. PR #117 removed
its last vestige, `_load_rubric_text`, which read rubric text and immediately
discarded it.

Note that removing `numpy` and `google-auth-oauthlib` drops a *declaration*, not
a package: both remain in the install as transitive dependencies. The value is
that the file now lists only what the code imports.

### Moved to `requirements-dev.txt`

`gTTS`, imported only by `speech_text/tts_handler.py`, which is imported only by
tests. This also drops an outbound runtime dependency on
`translate.google.com`.

### Runtime set

Eight direct packages, each confirmed imported by application code:
`streamlit`, `groq`, `reportlab`, `pytz`, `python-dotenv`, `python-dateutil`,
`gspread`, `google-auth`. All pinned with `==`.

`requirements.lock` records the full resolved closure of 60 packages.

### Provenance of the pinned versions

The plan called for capturing `pip freeze` from the running production
deployment, so that today's behaviour could be reproduced. That was not
possible: the deployment could not be inspected from here.

The versions instead come from resolving the current requirements in a clean
isolated virtualenv on Python 3.11 in CI. Production has been installing
unpinned packages since it was first deployed, so its actual versions may
differ. **Verify on the Track B deployment before cutover.**

No Python interpreter is available on the authoring machine, so the resolution
had to be performed by CI and copied back.

### Impact

| | Before | After |
|---|---|---|
| Direct runtime packages | 14 | 8 |
| Approximate install size | ~6 GB, CUDA wheels | ~400 MB |
| Runtime outbound dependencies | plus `huggingface.co` and `translate.google.com` | neither |

Removing `huggingface.co` retires part of Help Desk question B4.

### A defect introduced and caught

Removing the dead `transformers` suppression block at the top of
`secret_code_portal.py` also removed the `import os` that line 728 still
depends on. That would have been a `NameError` at runtime.

The test suite could not have caught it: `secret_code_portal` is a Streamlit
script the suite never imports. The import was restored, and **pyflakes** was
added to CI, since undefined names are exactly the failure mode dependency
pruning creates.

The pyflakes gate is deliberately narrow. Its first run reported 17 findings,
none of which were undefined names: unused imports, f-strings without
placeholders, and unused locals, all pre-existing. Failing on those would create
a permanently red gate that everyone learns to ignore, which is the problem
Phase 1a existed to fix. **Only undefined names fail the build.** The rest print
as advisory output.

Cleaning up those 17 is worth doing, but not inside a dependency change, and
several sit in files Phases 3 through 7 will rewrite.

### New CI steps

| Step | Purpose |
|---|---|
| Record runtime-only resolved versions | Resolves `requirements.txt` alone in a throwaway virtualenv. Source for the lockfile |
| Static check for undefined names | pyflakes, failing only on undefined names |
| Assert pins match the lockfile | The two files are maintained separately and can drift |

### Verification

| Check | Result |
|---|---|
| Four target packages imported nowhere | Confirmed by grep before removal |
| `google-auth-oauthlib` unused, no OAuth flow | Confirmed by grep |
| `gTTS` reachable only from tests | Confirmed by grep |
| No undefined names anywhere in the tree | pyflakes, CI |
| Every pin matches the lockfile | CI, all eight |
| Test suite | Green |

---

## Phase 1a: stale test cleanup

Date: 2026-08-11
Branch: `msi/phase-1a-stale-tests`
Pull request: #118
Result: **CI green. 221 passed, 2 skipped, 0 failed.**

### Purpose

Clear the 17 inherited failures recorded in the Phase 1 entry, so that a red
suite means something again before Phase 6 begins. Phase 6 relies on the suite
as its regression signal for silent scoring changes.

No runtime code changed.

### Changed

| File | Failures | Action |
|---|---|---|
| `tests/test_path_resolution.py` | 2 | Rewritten |
| `tests/test_multipage_integration.py` | 1 | Retargeted |
| `tests/test_secret_code_googlesa.py` | 14 | Deleted as superseded |
| `.github/workflows/ci-msi-hybrid.yml` | n/a | Guard false positive fixed |

### Why the failures stayed hidden

`tests/test_path_resolution.py` hardcoded the GitHub Actions runner path
`/home/runner/work/ManiUMN-MI_chatbots/ManiUMN-MI_chatbots`. Locally that path
does not exist, so every check took a `continue` branch and the file appeared to
pass. On CI the path exists, so the stale assertions ran and failed. Nobody saw
it because the previous workflow never ran pytest.

The repo root is now derived from `__file__`, so the tests behave identically in
both environments.

### Retargeting, not deletion

The properties these tests covered still matter. They moved when commit
`1656112` turned the bot pages into thin shells.

- Rubric path resolution moved to `mi_session._load_rubric_text`. Tests now
  assert it resolves relative to `__file__` rather than the working directory,
  which is what keeps it working under Apptainer and Slurm in Phase 8. Coverage
  extended from two rubric directories to all four.
- The authentication guard moved to `mi_session._auth_guard`. Tests now assert
  that every bot page delegates to `run_practice_session` and that the guard
  performs the checks. Coverage extended from two pages to all four. The new
  test deliberately does not assert on `groq_api_key`, so Phase 4 will not
  break it again.

### Deletion, where genuinely superseded

All 14 tests in `tests/test_secret_code_googlesa.py` patched
`secret_code_portal.gspread` and `secret_code_portal.Credentials`. Neither was
ever imported by that module; the credential logic lives in
`utils.access_control`. Every case is already covered by
`tests/test_access_control.py`, which passes and asserts the identical
credential-source strings at the correct layer. The full mapping is in the
commit message for `06e6b9d`.

One assertion was not carried over: that `get_google_sheets_client` writes
`googlesa_source` into `st.session_state`. That behaviour is unreliable in
production regardless, because the function is decorated `@st.cache_resource`,
so the write happens only on a cache miss and later users never observe it.
Recorded rather than re-asserted.

### The guard that had never run

The `Assert no hardcoded production sheet ID` step added in Phase 1 failed on
its first real execution, flagging `tests/test_app_env.py:20`. That line defines
the production sheet ID as the expected value, which is the check that stops the
default silently drifting. Pinning it is the point of the test.

The step had never executed before: CI steps run under `bash -e` in sequence,
and the previous run failed at the test suite, skipping everything after it. The
guard now exempts `tests/` and `test_*.py`.

### New baseline

| Branch | Result |
|---|---|
| `pre-msi-baseline` (equals `main`) | 17 failed, 226 passed, 2 skipped |
| `msi-hybrid` after Phase 1 | 17 failed, 216 passed, 2 skipped |
| `msi-hybrid` after Phase 1a | **0 failed, 221 passed, 2 skipped** |

**From this point, any test failure is a real regression.** Phase pull requests
are measured against zero, not against 17.

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
| Added in `tests/test_app_env.py` | 16 |
| After | 230 |

The reduction is expected and is recorded here so it is not later mistaken for
a regression.

Correction, 2026-08-01: this table originally recorded 18 added and 232 after.
The correct figures are 16 and 230, measured with
`cat tests/*.py test_evaluation.py | grep -c '^\s*def test_'`.

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
