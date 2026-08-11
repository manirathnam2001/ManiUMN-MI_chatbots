# MI Chatbots: MSI Migration Implementation Plan

Document version: 2.1
Date: 2026-07-31
Status: Approved; Phase 1 complete
Supersedes: version 2.0
Related research: `docs/MSI_MIGRATION_RESEARCH.md`
Related: `docs/TRACK_ISOLATION.md`, `docs/CHANGELOG_MIGRATION.md`

Change from version 1.0: the migration is structured as two isolated tracks. The existing
production deployment is frozen and remains authoritative. All migration work happens in a
parallel environment that shares no live resource with production.

Change from version 2.0: the storage split is now explicit. Feedback PDFs are archived to Box
and are never stored on MSI. MSI holds the conversation history, the evaluation results, and
the application logs, as a backend store. Because Box archiving is currently dormant in the
session flow, restoring it becomes new in-scope work rather than a preserved behaviour. See
sections 1.3 and 12.

---

## 1. Context

### 1.1 Why this migration is being done

The MI (Motivational Interviewing) training chatbots are currently deployed on Streamlit
Community Cloud and depend on the Groq hosted API for all language model inference. The
University of Minnesota School of Dentistry wants this application running on University
infrastructure, specifically the Minnesota Supercomputing Institute (MSI), without any loss
of functionality for students.

### 1.2 What research established

Research into MSI (documented in `docs/MSI_MIGRATION_RESEARCH.md`) produced three findings
that shape every decision in this plan:

1. MSI can host the AI workload very well. Both production models (`llama-3.1-8b-instant`
   and `llama-3.3-70b-versatile`) are open-weight Llama models, and MSI explicitly supports
   vLLM on A100, H100, L40S, A40 and V100 GPUs.
2. MSI cannot host a public student-facing web application today. All MSI access requires
   the UMN campus network or VPN, and the Stratus OpenStack cloud that previously offered
   persistent virtual machines is no longer advertised.
3. The MSI User Agreement explicitly prohibits storing FERPA-protected data. Named student
   MI evaluations are educational records under FERPA.

### 1.3 Chosen architecture

**Hybrid.** The Streamlit front end remains on a public, FERPA-appropriate host. MSI runs
the vLLM inference endpoints and the backend data store, and receives only pseudonymous
data. The Groq dependency is eliminated.

```
Students ---- HTTPS ----> Streamlit front end
                          (public host, holds student identity)
                             |                    |
                             |                    | identified PDF
       pseudonymous data     |                    | over SMTP
       over UMN network      |                    v
                             |            Box course folders
                             v            - feedback PDF, named
                    MSI Agate cluster       (the only PDF archive)
                    - vLLM: Llama 3.1 8B  (chat turns, evidence extraction)
                    - vLLM: Llama 3.3 70B (MI scoring)
                    - Tier 1: conversation history
                    - Tier 1: evaluation results
                    - Tier 1: application logs
```

### 1.3.1 The storage split

This split is deliberate and is the governing rule for every persistence decision in this
plan.

| Artifact | Destination | Carries student identity? |
|---|---|---|
| Feedback PDF | **Box only** | Yes. Box is the system of record for graded output |
| Conversation history | **MSI Tier 1** | No. Pseudonymous |
| Evaluation results (scores, rationales, recommendations) | **MSI Tier 1** | No. Pseudonymous |
| Application logs | **MSI Tier 1** | No. Scrubbed before write |
| Access codes and redemption state | Google Sheets | Yes. Unchanged |

**No PDF is ever written to MSI.** MSI is a backend store and a fallback, not a document
archive. This keeps the one artifact that must carry a student name entirely within a
UMN-sanctioned system, and keeps MSI clear of the MSI User Agreement prohibition on
FERPA-protected data.

### 1.3.2 Stated assumption: session identifiers

For the MSI store to function as a fallback, a specific student's session must be locatable
in it. The plan therefore assumes an opaque session identifier is generated per session,
used as the MSI record key, and printed in the footer of the Box PDF.

This gives recovery without giving MSI an identity: anyone holding the Box PDF can find the
matching MSI record, while MSI alone holds nothing that identifies anybody. If this linkage
is not wanted, drop the PDF footer line; the MSI store still works, but individual sessions
become unrecoverable by student.

### 1.4 Intended outcome

On completion:

- No dependency on the Groq hosted API. Inference runs on University hardware.
- No student identity ever leaves the front end or reaches MSI storage.
- **Every completed session archives its feedback PDF to the correct course Box folder.**
  This does not happen today.
- **Conversation history, evaluation results, and application logs are retained on MSI**,
  pseudonymously. Today none of them are retained anywhere.
- Switching inference providers is a configuration change, not a code change.
- The application survives process restarts without destroying in-flight student sessions.
- Student-visible behaviour, scoring, and PDF output are unchanged.
- **The existing deployment was never interrupted at any point during the work.**

### 1.5 Current-state facts this plan depends on

All of the following were verified directly against the codebase.

| Fact | Evidence |
|---|---|
| Deployed to Streamlit Community Cloud, entry point `secret_code_portal.py` | `README.md:329-351`, `docs/ADMIN_GUIDE.md:15` |
| `.github/workflows/deploy.yml` is named "Deploy" but deploys nothing; it performs a live Gmail SMTP login on every push to main | `.github/workflows/deploy.yml:20-21` |
| Only one Groq import and one client construction exist | `mi_session.py:34`, `mi_session.py:409-410` |
| Each student types their own Groq API key, which is written to the process-global `os.environ` | `secret_code_portal.py:688-693, 726, 730`; `mi_session.py:409` |
| `mi_evaluation.py` is already provider-agnostic (`client: Any`) | `mi_evaluation.py:259` |
| Four model name literals, no central registry | `mi_session.py:98,99`; `mi_evaluation.py:260,297` |
| Provider detection is done by string matching on error messages | `mi_evaluation.py:633-635, 638-645`; `mi_session.py:247-250` |
| No timeouts, no retries, no `max_tokens` on evaluator calls, no streaming anywhere | `mi_evaluation.py:595-615` |
| `torch`, `sentence-transformers`, `faiss-cpu`, `numpy` are imported nowhere | verified by repository-wide grep |
| `database/mi_sessions.sql` is a MySQL schema with no driver and no connection code, encoding an obsolete 30-point 4-category rubric against a live 40-point 6-category rubric | `database/mi_sessions.sql:50, 86-91` |
| Log and queue directories are bare relative paths resolved against the process working directory | `logger_config.py:35`; `config.json:21,26,29,30` |
| Named student PDFs are written to `SMTP logs/queued_<uuid>.pdf` on SMTP failure, and are not gitignored | `email_queue.py:188-192` |
| No Dockerfile, no shell scripts, no healthcheck, no process supervision, no startup script exist | verified by exhaustive file listing |
| All state is `st.session_state`, in-process, lost on restart | `mi_session.py:115-138` |
| The Google Sheet ID is hardcoded in three places | `secret_code_portal.py:83`; `pages/developer_page.py:104, 275` |
| A Google service-account private key remains recoverable in git history | commits `0ebde65`, `d6ea9e5`, `64dbfe2`, deleted in `566b679` |

---

## 2. Isolation strategy: two parallel tracks

This section governs every phase that follows. Where any other section appears to conflict
with it, this section wins.

### 2.1 Principle

**Track A (Production) is frozen and authoritative. Track B (Migration) is built alongside it
and shares no live resource with it.** Nothing in Track B may cause a student in Track A to
see an error, lose a session, or have an access code consumed.

| | Track A: Production | Track B: Migration |
|---|---|---|
| Git branch | `main` | `msi-hybrid` (long-lived) |
| Deployment | Existing Streamlit Cloud app | Second Streamlit Cloud app, deployed from `msi-hybrid` |
| Inference | Groq, per-student API keys | MSI vLLM, operator credential |
| Access code sheet | Live Google Sheet | Separate test Google Sheet |
| Student population | Real cohorts | Implementer, then one small pilot cohort |
| Change policy | Frozen: security fixes only | Active development |
| Status at end of plan | Remains live until an explicit cutover decision | Candidate replacement |

Streamlit Community Cloud supports deploying a specific branch of a repository as a separate
application. This gives two independently running applications from one repository with no
shared process, no shared filesystem, and no shared configuration.

### 2.2 Shared resources and how each is decoupled

These are the actual coupling points between the two tracks. Each must be explicitly
decoupled before Track B accepts any traffic.

| Shared resource | Risk if not decoupled | Decoupling action | Phase |
|---|---|---|---|
| Google Sheet of access codes | Track B testing marks real student codes as used, locking students out of production | Create a separate test sheet. Make the sheet ID configurable via `MI_SHEET_ID` instead of the three hardcoded literals | 1 |
| Google service account | Track B credential problems could affect Track A Sheets access | Use one service account with read and write on both sheets, or provision a second service account for Track B. Rotation is handled separately in Phase 0 | 0 |
| Gmail SMTP account | Track B could emit real email during testing | Set `MI_SMTP_ENABLED=false` in Track B, or point Track B at a disposable mailbox | 1 (done) |
| Box intake addresses | Track B PDFs could land in the real course archive | Two controls. `MI_SMTP_ENABLED=false` blocks sending outright. When Track B needs to exercise the restored Box flow, `MI_BOX_EMAIL_OVERRIDE` redirects all four course addresses to a single test mailbox | 1 (partial), 7 |

**The Box exposure grows in Phase 7.** In the current code the only exposure is the startup
queue drain, because the session-flow send was lost in commit `1656112` (see section 12.1).
Once Phase 7 restores it, every completed Track B session would email a real course folder if
SMTP were enabled without an override. `MI_BOX_EMAIL_OVERRIDE` must land in the same change as
the restoration, not after it.
| Repository `main` branch | Merging Track B work early would change production | No merge to `main` until the cutover decision in Phase 12 | All |
| GitHub Actions on `main` | Existing workflow performs a live SMTP login on every push to main | Add a workflow that runs on `msi-hybrid` only. See section 2.4 regarding the existing workflow | 1 |
| Groq account and billing | None. Track A uses per-student keys; Track B uses an operator key or MSI | No action | n/a |

### 2.3 Track A change freeze

For the duration of this work, `main` accepts only:

- Security fixes.
- Bug fixes for defects affecting live students.
- The permitted production touches enumerated in section 2.4.

No refactoring, no dependency changes, no dead code removal on `main`. All of that happens on
`msi-hybrid`.

### 2.4 Permitted production touches

Three items unavoidably or advisably touch Track A. Each requires explicit approval before
execution and is listed here so nothing touches production by accident.

| Item | Why it touches production | Risk | Recommendation |
|---|---|---|---|
| **Google service-account key rotation** | Production reads the same credential. Rotating it requires updating the production secret in the same operation | Low. A secret value swap with no code change. Brief Sheets outage if mistimed | **Required.** The key is recoverable from git history. Perform during a low-traffic window, verify production immediately after |
| **`.github/workflows/deploy.yml`** | It runs on push to `main` and performs a live Gmail SMTP login on every push | Very low. CI only, no runtime effect on the deployed app | **Recommended.** Either disable the workflow or restrict it to the test suite. If declined, it stays as-is and Track B adds its own workflow |
| **`.gitignore` hardening** | The file is shared by both branches; leaving `main` unhardened means student PDFs can still be committed from a production hotfix | Very low. Affects git only, not runtime | **Recommended.** Apply the same rules to both branches |

Everything else in this plan happens on `msi-hybrid` and never reaches production until
Phase 12.

### 2.5 Branch drift management

`msi-hybrid` will be long-lived, on the order of months. Drift is managed by the Track A
change freeze: with `main` accepting only security and bug fixes, the merge surface stays
small.

Discipline:

- Rebase `msi-hybrid` onto `main` after every commit that lands on `main`.
- Never merge `msi-hybrid` into `main` before the Phase 12 decision.
- Tag `main` at the start of the work as `pre-msi-baseline` so the frozen state is
  unambiguous and recoverable.

### 2.6 Consequence for the phase plan

Phases 1 through 7 were described in version 1.0 as host-agnostic work "testable on Streamlit
Cloud." That remains true, with one correction: they are tested on the **Track B** Streamlit
Cloud application deployed from `msi-hybrid`, not on the production application.

---

## 3. Approved decisions

These were confirmed before writing this plan and are not open for re-litigation during
implementation.

| Decision | Choice | Consequence |
|---|---|---|
| Target architecture | Hybrid: MSI for AI only | Phases 10 and 11 apply only if MSI later clears public hosting |
| Deployment approach | Two isolated tracks; production frozen | No merge to `main` until Phase 12; a second Streamlit Cloud app is required |
| Per-student API keys | Remove the key field entirely, no fallback flag | Applies to Track B only. Track A keeps per-student keys until cutover. Rollback after cutover remains available at the operator level by pointing `MI_LLM_BASE_URL` back at Groq |
| Unused dependencies | Remove `torch`, `sentence-transformers`, `faiss-cpu`, `numpy` | Track B only. Container image drops from roughly 6 GB to roughly 400 MB; the `huggingface.co` outbound dependency disappears |
| `database/mi_sessions.sql` | Delete | Track B only. Removes an obsolete rubric definition |
| `end_control_middleware.py` | Delete | Track B only. Also removes approximately five test files; scheduled in Phase 1 so the Track B baseline test suite reflects the post-deletion state |
| Feedback PDF storage | **Box only.** Never MSI | The one artifact carrying a student name stays in a UMN-sanctioned system, keeping MSI clear of the User Agreement prohibition |
| MSI storage contents | Conversation history, evaluation results, application logs | All pseudonymous. MSI acts as a backend store and fallback, not a document archive |
| Box session-flow archiving | **Restore it** (Phase 7) | Regression from commit `1656112`. A known-good reference implementation exists at `1656112^:pages/OHI.py` |

---

## 4. Phase overview and ordering

Phases 1 through 7 are host-agnostic. They require no MSI account, are developed and tested
on the Track B Streamlit Cloud application, and should begin immediately. Phases 8 through 12
require MSI access and, in some cases, answers from the MSI Help Desk.

| Phase | Title | Track | Requires MSI? | Estimated effort |
|---|---|---|---|---|
| 0 | Unblock: security, accounts, environment provisioning | A and B | Started immediately, runs in parallel | Elapsed time, not effort |
| 1 | Track B setup, safety net, dead code removal | B | No | 1.5 days |
| 2 | Dependency prune, pin, lock | B | No | 0.5 day |
| 3 | LLM provider abstraction | B | No | 2 days |
| 4 | Retire per-student API keys | B | No | 0.5 day |
| 5 | Path externalization | B | No | 1 day |
| 6 | FERPA de-identification boundary | B | No | 2 to 3 days |
| 7 | Data persistence: Box archiving and the MSI backend store | B | No | 3 to 4 days |
| 8 | Containerization with Apptainer | B | Yes | 1 day |
| 9 | vLLM service jobs and endpoint registry | B | Yes, plus Help Desk answers | 2 to 3 days |
| 10 | Streamlit service job (conditional) | B | Yes, plus Help Desk clearance | 2 days |
| 11 | Capacity and load testing | B | Yes | 1 day |
| 12 | Parallel run, decision, and cutover | A and B | Yes | One course cycle |

### 4.1 Hard ordering constraints

These are not preferences. Violating them causes defined failures.

1. **Track B must be isolated (Phase 1) before any other Track B phase.** Specifically, the
   sheet ID must be configurable and pointed at a test sheet before any Track B session is
   run, or testing will consume real student access codes.
2. **Phase 5 must precede Phase 8.** Apptainer containers are read-only by default. Every
   bare relative path becomes a startup crash inside a container, not a warning.
3. **Phase 2 must precede Phase 8.** Building an image before pruning dependencies produces
   a 6 GB image with CUDA layers that is then discarded.
4. **Phase 6 must precede Phase 7.** The MSI store writes transcripts, evaluation results, and
   logs to Tier 1. Writing any of them before de-identification is in place would place
   FERPA-protected data on MSI, which is exactly the User Agreement violation this plan
   exists to avoid. This now applies to the log scrubbing filter as well as the transcript
   path; see section 12.2.
5. **`MI_BOX_EMAIL_OVERRIDE` must land in the same commit as the Box restoration.** Restoring
   the send without the override would cause every Track B test session to email a real
   course Box folder. See section 2.2.
6. **The error-classification work in Phase 3 must precede Phase 9.** The string matching at
   `mi_evaluation.py:638-645` is Groq-shaped. Against vLLM it will not match, and the
   extractor fallback at `mi_evaluation.py:342-350` will silently stop working. If this is
   not fixed first, it will be misdiagnosed as a vLLM problem.
7. **The endpoint registry in Phase 9 is mandatory, not optional.** vLLM jobs are capped at
   24 to 96 hours. A Streamlit job can run 37 days. Baking a static `MI_LLM_BASE_URL` into
   the front end means every vLLM restart takes the application down.

---

## 5. Phase 0: Unblock

**Goal.** Resolve items that gate the MSI-dependent phases, provision the Track B
environment, and close a security hole that exists independently of this migration.

This phase involves no application code and must start immediately, in parallel with
Phases 1 through 7.

### 5.1 Rotate the leaked Google service-account key

**This is the one item that necessarily touches production.** See section 2.4.

A Google service-account private key was committed to this repository and later deleted from
the working tree. Deletion does not remove it from git history. It remains recoverable from
commits `0ebde65`, `d6ea9e5`, and `64dbfe2`.

Actions, in order:

1. Schedule a low-traffic window and notify the course instructor.
2. Mint a replacement key in the Google Cloud console for project `umnsod-mibot`.
3. Update the `GOOGLESA` secret in the **production** Streamlit Cloud application.
4. Verify the production access-code portal reads and writes the live sheet correctly.
5. Only then, disable the old key.
6. Record the new credential for Track B use as well.

Ordering matters: minting and deploying the new key before disabling the old one avoids any
production outage. Rotation must happen before the credential is copied to any new location,
including MSI. Rewriting git history with `git filter-repo` is optional and secondary.
Rotation is what actually mitigates the exposure.

### 5.2 Provision the Track B environment

| Item | Action |
|---|---|
| Branch | Create `msi-hybrid` from `main`. Tag `main` as `pre-msi-baseline` |
| Test Google Sheet | Create a new sheet with the same column layout: `Table No, Name, Bot, Secret, Used`, plus the optional `Role` column. Populate with disposable test codes. Grant the service account edit access |
| Second Streamlit Cloud app | Deploy from branch `msi-hybrid`, main file `secret_code_portal.py`. Configure its own secrets independently of production |
| Track B secrets | `GOOGLESA` (may be the same credential), `MI_SHEET_ID` pointing at the test sheet, `MI_SMTP_ENABLED=false`, and later `MI_LLM_BASE_URL` and `MI_LLM_API_KEY` |
| Access restriction | If Streamlit Cloud permits, restrict the Track B application to named viewers so students cannot reach it by accident |

### 5.3 Submit questions to the MSI Help Desk

Send the ten questions in `docs/MSI_MIGRATION_RESEARCH.md` section 7, plus two more that the
current-state analysis produced:

11. Does MSI support `scrontab` or another sanctioned pattern for a self-resubmitting service
    job that survives maintenance windows?
12. Can a Slurm job on one partition reach a service running in a Slurm job on a different
    partition over TCP, without an SSH tunnel?

Question 5 (outbound internet access from compute nodes) is the highest priority. It
determines whether the SMTP and Google Sheets paths can function from MSI at all.

### 5.4 Obtain a written FERPA determination

Obtain written positions from both the MSI Help Desk and the UMN privacy and compliance
office. Phase 6 makes de-identification technically real, but only the compliance office can
state whether pseudonymous transcripts satisfy the MSI User Agreement.

### 5.5 Establish the MSI project

A UMN faculty member must act as Principal Investigator and create an MSI project through
MyMSI. **Do not use a class account.** Class accounts close automatically two weeks after the
semester ends and their data is unrecoverable.

**Acceptance criteria.** Production verified working on the new credential and the old key
disabled. `msi-hybrid` branch created and `pre-msi-baseline` tag applied. Track B Streamlit
application deployed and reachable, reading from the test sheet only. Help Desk ticket number
recorded. Written FERPA determination on file. MSI project created.

---

## 6. Phase 1: Track B setup, safety net, and dead code removal

**All changes in this phase and every subsequent phase through Phase 11 are committed to
`msi-hybrid` only.**

**Goal.** Isolate Track B from production data, make the test suite trustworthy before any
refactoring begins, and remove dead code now so the baseline test count reflects the
post-deletion state.

### 6.1 Make the Google Sheet target configurable

This is the highest-priority item in the phase. Until it is done, running a Track B session
consumes a real student access code.

The sheet ID is hardcoded in three places:

| File and line | Current |
|---|---|
| `secret_code_portal.py:83` | `SHEET_ID = "1x_MA3MqvyxN3p7v_mQ3xYB9SmEGPn1EspO0fUsYayFY"` |
| `pages/developer_page.py:104` | Same literal |
| `pages/developer_page.py:275` | Same literal |

Replace all three with a single module-level constant read from `MI_SHEET_ID`, defaulting to
the production literal so Track A behaviour is unchanged if this branch is ever merged. Set
`MI_SHEET_ID` to the test sheet in the Track B application secrets.

Add a visible banner to the Track B application, gated on an `MI_ENVIRONMENT=test` variable,
reading "TEST ENVIRONMENT. Not for student use." This prevents a student who receives the
wrong link from completing a graded session against the test environment.

### 6.2 Disable outbound email in Track B

Add an `MI_SMTP_ENABLED` flag, default `true`, checked before any SMTP connection attempt in
`email_utils.py`. Set it to `false` in Track B. This prevents test PDFs from reaching the
four Box intake addresses in `config.json:15-18` and prevents the startup queue drain from
attempting a live Gmail login.

### 6.3 Close the gitignore gaps

`.gitignore` currently covers `SMTP logs/*.log` and `*.log`. It does not cover the artifacts
that actually contain student identities. Add:

```
git_logs/
*.log.[0-9]*
SMTP logs/failed_emails.json
SMTP logs/queued_*.pdf
.streamlit/secrets.toml
*service-account*.json
umnsod-mibot-*.json
```

The absence of a `*.json` rule is the root cause of the credential leak in section 5.1. Per
section 2.4, applying this to `main` as well is recommended and requires approval.

### 6.4 Add a Track B CI workflow

The existing `.github/workflows/deploy.yml` triggers only on push to `main`, so it does not
run on `msi-hybrid`. Add a separate workflow triggered on `msi-hybrid` and on pull requests
targeting it, requiring no secrets and making no network calls:

```yaml
- run: pip install -r requirements.txt
- run: python -m pytest tests/ test_evaluation.py -q
- run: python -c "import secret_code_portal, mi_session, mi_evaluation"
```

Disabling or replacing the production workflow is a separate, approval-gated item under
section 2.4.

### 6.5 Reconcile the Python version

`runtime.txt` specifies `python-3.10`. `.devcontainer/devcontainer.json:4` specifies 3.11.
Standardise Track B on **3.11**. The pressure toward 3.10 came from `torch`, which Phase 2
removes.

Also fix `.devcontainer/devcontainer.json:22`, whose `postAttachCommand` references a
nonexistent root-level `HPV.py`. It should be `streamlit run secret_code_portal.py`. Remove
`--server.enableCORS false --server.enableXsrfProtection false` from that command; those
flags are not acceptable defaults for a student-facing service.

### 6.6 Remove dead code

| Item | Reason |
|---|---|
| `database/mi_sessions.sql` | MySQL schema with no driver, no connection code, and an obsolete 30-point 4-category rubric |
| `test_php_pdf_new_rubric.php` | Fossil of the same abandoned LAMP direction |
| `end_control_middleware.py` | 55 KB dead module with unsynchronized module-level mutable state at `:1348-1354` |
| Associated tests | `test_end_control_middleware.py`, `test_end_control_integration.py`, `test_semantic_ending.py`, `test_mutual_intent.py`, `test_e2e_mutual_intent.py` |

Record the test count before and after. The drop is expected and should be documented in the
commit message so it is not later mistaken for a regression.

**Verification.**

```bash
python -m pytest tests/ test_evaluation.py -q
```

Confirm the Track B application loads the test sheet and not the production sheet:

```bash
grep -rn "1x_MA3MqvyxN3p7v" --include=*.py .
```

This must return nothing outside a documented default constant.

Then run one complete session on the Track B application and confirm that a code is marked
used **on the test sheet**, and that the production sheet is unchanged.

**Rollback.** Configuration changes plus file deletions on a branch that is not deployed to
students. Revert the commit.

---

## 7. Phase 2: Dependency prune, pin, and lock

**Goal.** Reduce the runtime surface before it is baked into a container image.

### 7.1 Remove unused dependencies

Delete from `requirements.txt`: `sentence-transformers`, `faiss-cpu`, `numpy`, and
`torch>=2.5.1`. All four are imported nowhere. The RAG pipeline they supported was removed;
`mi_session.py:415-418` loads rubric text and immediately discards it into `_`.

### 7.2 Separate development dependencies

Create `requirements-dev.txt` and move `gTTS>=2.3.0` into it. The `speech_text/` package is
imported only by the test suite. Voice mode is a documented dormant feature
(`mi_session.py:11-12`). This also removes a `translate.google.com` outbound dependency from
the MSI question list.

### 7.3 Pin and lock

Before pinning, capture the versions currently running in **production** so today's behaviour
is reproducible in Track B:

```bash
pip freeze > requirements.observed.txt
```

Pin the nine remaining runtime packages with `==`: `streamlit`, `openai` (replacing `groq` in
Phase 3), `reportlab`, `pytz`, `python-dotenv`, `python-dateutil`, `gspread`, `google-auth`,
`google-auth-oauthlib`. Generate `requirements.lock` with `pip-compile` or `uv pip compile`.

Twelve of fourteen packages are currently unpinned with no lockfile. `gspread` in particular
matters, because `utils/access_control.py:338` branches on
`hasattr(gspread, 'service_account_from_dict')`, which is version-dependent.

### 7.4 Clean up the watcher blacklist

`.streamlit/config.toml:7-14` blacklists `transformers`, `torch`, `sentence_transformers`,
`faiss`, and `numpy` from the file watcher. Those entries become dead. Retain the `reportlab`
entry.

### 7.5 Risk to address in this phase

`mi_session.py:344-365` `_load_rubric_text` calls `st.stop()` when the rubric directory is
missing, so `hpv_rubrics/`, `ohi_rubrics/`, `perio_rubrics/`, and `tobacco_rubrics/` remain
hard startup requirements even though their contents are discarded.

Recommended resolution: **keep the directories, delete the call at `mi_session.py:418`, and
leave `_load_rubric_text` defined but unused.** This removes a startup failure mode and four
directories from the container image while preserving the option to reinstate RAG later.

**Verification.**

```bash
python -m venv .venv-check && .venv-check/Scripts/pip install -r requirements.lock
```

```bash
.venv-check/Scripts/python -c "import torch"
```

The second command must fail with `ModuleNotFoundError`. Then confirm the suite is green and
speech tests skip rather than error (add `pytest.importorskip("gtts")` where needed).

---

## 8. Phase 3: LLM provider abstraction

**Goal.** Make the Groq to vLLM transition a configuration change rather than a code change.
This is the keystone phase. It converts the migration from a rewrite into a deployment.

### 8.1 New module: `llm_provider.py`

The `openai` Python SDK is a drop-in client for both Groq (`https://api.groq.com/openai/v1`)
and vLLM (`http://<node>:<port>/v1`). Critically, it accepts `api_key` and `base_url` as
explicit constructor arguments, which eliminates the `os.environ` write entirely.

The module provides:

| Symbol | Responsibility |
|---|---|
| `LLMSettings` | Dataclass: `provider`, `base_url`, `api_key`, `chat_model`, `eval_model`, `extractor_model`, `timeout_s`, `max_retries`, `chat_max_tokens`, `eval_max_tokens` |
| `MODELS` | Central model registry, replacing four scattered string literals |
| `load_settings()` | Reads environment variables with a Groq-shaped default so nothing breaks on first deploy |
| `make_client(settings)` | Returns a configured `openai.OpenAI` instance |

Environment variables introduced: `MI_LLM_PROVIDER`, `MI_LLM_BASE_URL`, `MI_LLM_API_KEY`,
`MI_LLM_CHAT_MODEL`, `MI_LLM_EVAL_MODEL`, `MI_LLM_EXTRACTOR_MODEL`, `MI_LLM_TIMEOUT_S`,
`MI_LLM_MAX_RETRIES`.

Because the default is Groq-shaped, Track B remains fully functional against Groq throughout
Phases 3 through 7, before any MSI endpoint exists. That is what allows the entire
host-agnostic half of this plan to be completed and verified while waiting on MSI.

### 8.2 Constraint: preserve the client duck type

`test_evaluation.py:66` defines a `FakeClient` that drives `client.chat.completions.create`
and inspects `client.chat.completions.calls`. More than twenty-five tests depend on this
surface.

**The abstraction must return an object exposing `client.chat.completions.create(...)`
unchanged. Do not wrap the client in a custom `generate()` facade.** If any existing test
requires editing during this phase, the abstraction has leaked and the design is wrong.

### 8.3 Call-site changes

| File and line | Current | Change |
|---|---|---|
| `mi_session.py:34` | `from groq import Groq` | Remove; import from `llm_provider` |
| `mi_session.py:409-410` | `os.environ["GROQ_API_KEY"] = ...` then `Groq()` | `client = make_client(load_settings())`; delete the environment write |
| `mi_session.py:189` | `client: Groq` | `client: Any` |
| `mi_session.py:267` | `client: Groq` | `client: Any` |
| `mi_session.py:98` | `"llama-3.1-8b-instant"` | Registry default |
| `mi_session.py:99` | `"llama-3.3-70b-versatile"` | Registry default |
| `mi_evaluation.py:260` | `model: str = "llama-3.3-70b-versatile"` | Registry default |
| `mi_evaluation.py:297` | Hardcoded `"llama-3.1-8b-instant"` | Registry default |

`mi_evaluation.py` needs only the model-literal change, because it is already typed
`client: Any` at `:259`. That is the payoff for its existing provider-agnosticism.

### 8.4 Portable error classification

Replace the three string-matching sites with a classifier that inspects typed SDK exceptions
first and falls back to string matching only as a last resort.

| Site | Current detection | Replacement |
|---|---|---|
| `mi_evaluation.py:633-635` `_looks_like_unsupported_format` | Substring match on `"response_format"` or `"json_object"` | Check `openai.BadRequestError` and the `param` field first |
| `mi_evaluation.py:638-645` `_looks_like_unknown_model` | Substring match on `"model_not_found"`, `"does not exist"`, `"unknown model"`, `"not available"` | Check `openai.NotFoundError` and HTTP 404 first |
| `mi_session.py:247-250` | Substring match on `"401"`, `"invalid api key"`, `"authentication"` | Check `openai.AuthenticationError` |

Add a `retryable(exc)` predicate covering `APIConnectionError`, `APITimeoutError`,
`RateLimitError`, and `InternalServerError`.

**This subsection is a hard prerequisite for Phase 9.** The current strings are Groq-shaped.
vLLM returns a differently worded 404 body, so the extractor fallback at
`mi_evaluation.py:342-350` would silently stop working.

### 8.5 Timeouts, retries, and token limits

Today there are no timeouts, no retries, and no rate-limit handling on any of the four call
sites. Against Groq's low latency this is survivable. Against a self-hosted 70B model on
shared HPC it is not.

| Call site | Current | Target |
|---|---|---|
| `mi_session.py:239-244` (chat turn) | `max_tokens=250`, `temperature=0.7`, no timeout | Unchanged plus `timeout=30` |
| `mi_evaluation.py:595` (scorer) | `temperature=0.2`, **no `max_tokens`** | Add `max_tokens=1500`, `timeout=180` |
| `mi_evaluation.py` extractor path | No `max_tokens` | Add `max_tokens=1200`, `timeout=180` |

Set `max_retries=2` on the `openai.OpenAI` constructor. This handles connection failures,
5xx responses, and 429 responses with backoff.

**Do not add a custom retry loop on top of the existing schema retry at
`mi_evaluation.py:358-359`.** Stacking them yields a worst case of eight calls to a 70B model
for a single evaluation.

The absence of `max_tokens` on the evaluator is the most important item here. vLLM defaults
the generation cap to the remaining context window, so a degenerate response can run for
several minutes.

**Verification.**

```bash
python -m pytest tests/ test_evaluation.py -q
```

This must pass with zero test edits.

```bash
grep -rn "from groq" --include=*.py .
```

This must return nothing outside documentation. Then run a live end-to-end session on the
Track B application, still against Groq, and confirm a PDF downloads with correct scores.

**Rollback.** The module is additive and `load_settings()` defaults to Groq behaviour.

---

## 9. Phase 4: Retire per-student API keys

**Track B only. Production continues to use per-student keys until cutover.**

**Goal.** Eliminate the process-global credential race and prepare for a shared endpoint.

### 9.1 The defect being removed

Each student currently types their own Groq API key at `secret_code_portal.py:688-693`. It is
stored to session state at `:726` and then written to `os.environ` at `:730`. The environment
is process-global and shared across all concurrent Streamlit sessions. `mi_session.py:409`
rewrites it on every page render.

Consequence: two students active concurrently in the same server process can race, and one
student's requests can be billed to the other student's key. The outcome is nondeterministic.

**Note that this defect exists in production today.** It is not introduced by the migration.
If it is causing observed problems, fixing it on `main` is a candidate for the permitted
production touches in section 2.4, but that is a separate decision from this plan.

### 9.2 Changes

| File and line | Change |
|---|---|
| `secret_code_portal.py:688-693` | Remove the API key text input |
| `secret_code_portal.py:709-710` | Remove the empty-key validation branch |
| `secret_code_portal.py:726` | Remove the session-state assignment |
| `secret_code_portal.py:730` | Remove the `os.environ` write |
| `mi_session.py:162-166` | Reduce the guard to `student_name` only |
| `pages/developer_page.py:66` | Same guard reduction |
| `mi_session.py:246-251` | Replace the "Re-enter your Groq key" message with an operator-facing message such as "The evaluation service is currently unavailable. Please contact your instructor." |

The credential now comes exclusively from `load_settings()`, sourced from the Track B
application secrets.

### 9.3 Rollback posture

Per the approved decision, no per-student fallback flag is retained. After cutover, rollback
remains available at the operator level: set `MI_LLM_BASE_URL` back to
`https://api.groq.com/openai/v1` and `MI_LLM_API_KEY` to one operator-held Groq key. This is
a configuration change requiring no code deployment. Before cutover, the rollback is simply
that production is still running untouched.

### 9.4 Coordination requirement

This changes the student-facing login form. Onboarding instructions and any course
documentation that tells students to obtain a Groq key must be updated **as part of the
Phase 12 cutover**, not now. Until cutover, production instructions remain correct.

**Verification.**

```bash
grep -rn "os.environ\[" --include=*.py . | grep -v test
```

No assignment may appear in any request path. Then perform a manual concurrency check on the
Track B application: log in from two browsers simultaneously, run a turn in each, and confirm
both succeed.

---

## 10. Phase 5: Path externalization

**Goal.** The application must run correctly with an arbitrary working directory and a
read-only application directory.

This phase is a hard prerequisite for Phase 8. Apptainer containers are read-only by default,
so every bare relative path below becomes a startup crash rather than a warning.

### 10.1 Path inventory and remediation

| Anchor | Problem | Remediation |
|---|---|---|
| `logger_config.py:35` `DEFAULT_LOG_DIR = "git_logs"` | Relative to working directory | `MI_LOG_DIR`, absolute, with a `__file__`-relative default |
| `config.json:21, 26` | Relative log paths | Environment-overridable, absolute |
| `config.json:29-30` `"SMTP logs"` | Relative **and contains a space** | Rename to `smtp_queue`; introduce `MI_QUEUE_DIR` |
| `email_utils.py:69, 512, 812` | Default `"SMTP logs"` | Same |
| `email_utils.py:752, 866` bare `open('config.json')` | Working-directory dependent | Route through `ConfigLoader`; add `MI_CONFIG_PATH` |
| `utils/access_control.py:228` | Bare relative service-account filename | `MI_GOOGLE_SA_FILE`, absolute |
| `email_queue.py:188` | Inherits the relative queue directory | Resolved by `MI_QUEUE_DIR` |

Note that `config_loader.py:34` already resolves `config.json` correctly relative to
`__file__`. The two call sites in `email_utils.py` use a different and incorrect strategy for
the same file. This inconsistency is being removed.

### 10.2 The directory name with a space

`SMTP logs` contains a space. This is a genuine hazard for Slurm submission scripts,
Apptainer `--bind` arguments, and any `rsync` or `s3cmd` invocation, all of which require it
to be quoted in every occurrence.

Rename it to `smtp_queue`. Retain a one-release backward-compatible read of the old directory
name in `EmailQueue._load()` so that any queued PDFs are not stranded at cutover.

### 10.3 Move email queue processing out of module scope

`secret_code_portal.py:93-122` calls `sender.process_failed_queue()` at module import time.
With `retry_delays: [5, 10, 30, 60, 120]` (`config.json:12`) and a 30 second connection
timeout, a blocked SMTP path stalls application startup for several minutes per queued entry.

Outbound access on port 587 from MSI compute nodes is unconfirmed (Help Desk question 5). If
it is blocked, every restart of the front end would hang on startup.

Move this work behind `@st.cache_resource` with a hard deadline, or preferably into a separate
scheduled job. The `MI_SMTP_ENABLED` flag from Phase 1 already short-circuits it in Track B.

**Verification.**

```bash
cd / && MI_LOG_DIR=/tmp/mi/logs MI_QUEUE_DIR=/tmp/mi/queue python -m streamlit run "/abs/path/secret_code_portal.py"
```

The application must start cleanly and create its directories under `/tmp/mi`.

```bash
grep -rn "SMTP logs" --include=*.py --include=*.json .
```

This must return nothing.

**Rollback.** All defaults preserve current behaviour when the environment variables are
unset.

---

## 11. Phase 6: FERPA de-identification boundary

**Goal.** Ensure MSI only ever receives pseudonymous data. This is the highest-regression-risk
phase in the plan and requires the most careful testing.

### 11.1 The complete identity surface

Every one of these must be addressed. Item 2 is the one most commonly missed.

1. `student_name` passed to `evaluate_session` at `mi_session.py:274, 283`, interpolated into
   both the extractor and scorer prompts at `mi_evaluation.py:579`.
2. **The transcript itself.** Students routinely introduce themselves by name in the first
   turn. Replacing the name field alone is insufficient.
3. The PDF body at `mi_pdf.py:246` and the PDF filename at `mi_pdf.py:73`.
4. `smtp_queue/queued_<uuid>.pdf` and `failed_emails.json` written by
   `email_queue.py:188-192`.
5. The Name column in the Google Sheet.

### 11.2 New module: `deident.py`

| Symbol | Responsibility |
|---|---|
| `session_id()` | Opaque UUID4, held in session state and the URL query parameter |
| `Pseudonymizer` | Per-session forward map (real name to `"Student A"`) and reverse map, held in front-end memory only, never serialized |
| `scrub(text, mapping)` | Applies the map with word-boundary matching, plus a regex sweep for UMN email addresses and seven-digit UMN IDs |
| `rehydrate(result, reverse_map)` | Restores the real name in `rationale`, `evidence_quote`, and `recommendations` fields of the evaluation result |

### 11.3 Modified call flow

In `mi_session._generate_feedback` (`mi_session.py:267-293`):

```
raw_transcript  = "\n".join(transcript_parts)          # existing, :269-273
pmap            = Pseudonymizer(student_name)
safe_transcript = scrub(raw_transcript, pmap)
result          = evaluate_session(safe_transcript, ..., student_name=pmap.alias, ...)
result          = rehydrate(result, pmap.reverse)
st.session_state.evaluation_result = result
```

### 11.4 The regression trap

`mi_evaluation._verify_quotes` (`:446-455`) checks that every extracted evidence quote appears
verbatim in the transcript, and **silently drops quotes that do not match**. Meanwhile
`mi_pdf.generate_pdf_report` receives the raw chat history (`mi_session.py:319`).

Three failure modes follow:

1. Scrubbing the evaluator's transcript while comparing quotes against raw text breaks
   verification.
2. Scrubbing without rehydrating produces a PDF where evidence quotes say "Student A" while
   the transcript appendix shows the real name. This is a visible inconsistency in a graded
   artifact.
3. **Worst case:** scrubbing alters a string mid-quote, `_verify_quotes` drops that quote,
   `_check_extractor_schema` (`:413-443`) then sees fewer categories with supporting evidence,
   and **the student's score changes silently**.

### 11.5 Required tests, written before the implementation

**Golden-score regression test.** Freeze five representative transcripts, including at least
one where the student states their name in the first turn. Record the exact `EvaluationResult`
produced by the current code using the existing `FakeClient` harness. Then assert:

- With the name scrub disabled, results are byte-identical.
- With the name scrub enabled, scores are identical (rationale text may differ).

**Recording assertion test.** Wrap `FakeClient` so that every `messages` payload sent to the
model is captured. Run a full session with `student_name="Jane Q. Public"` and a transcript
containing "Hi, I'm Jane". Then assert:

```python
assert "Jane" not in json.dumps(captured_calls)
```

This single test is the machine-checkable statement of the FERPA posture and is the artifact
to present to the compliance office.

**Rollback.** Feature-flag as `MI_DEIDENTIFY`. When disabled, behaviour is identical to
production.

---

## 12. Phase 7: Data persistence (Box archiving and the MSI backend store)

**Goal.** Deliver the storage split defined in section 1.3.1. Feedback PDFs reach Box.
Conversation history, evaluation results, and application logs reach MSI, pseudonymously.
In-flight sessions survive process restarts.

This phase absorbs what version 2.0 of this plan called "session durability" and adds the Box
restoration.

### 12.1 Restore Box PDF archiving

**This is the repair of a regression, not new development.**

Box archiving was fully implemented and working. Each of the four bot pages carried its own
send block that called `RobustEmailSender.send_with_guaranteed_delivery` with a progress
callback and a retry and skip interface. It was lost in commit `1656112`, the refactor that
collapsed the four fat page files into thin shells over the shared runner
`mi_session.run_practice_session`. The send block did not make it into the shared runner.

Two artifacts of that refactor confirm the intent to restore it:

- `mi_session.py:12-13` records the omission explicitly as a known regression.
- `SessionConfig.enable_email_to_box` (`mi_session.py:105`) is the reserved hook, currently
  defaulting to `False`.

**Reference implementation:** `git show 1656112^:pages/OHI.py`, lines 356 to 440. The port
should follow it rather than reinvent it. Its behaviour:

| Element | Detail |
|---|---|
| Recipient | `email_config.get('<bot>_box_email')` from `config.json:15-18`, one address per bot |
| Transport | `RobustEmailSender.send_with_guaranteed_delivery`, which retries with backoff and queues persistently on failure |
| Progress | `progress_callback` driving a `st.progress` bar and a status line |
| State machine | `st.session_state.email_backup_status`, one of `pending`, `success`, `queued`, `failed`, `no_email`, `skipped` |
| Failure handling | "Retry Backup" and "Skip and Download Only" buttons |
| Download gating | **The download button appears only once backup resolves.** This is a deliberate design choice, not an accident: it stops a student walking away with the only copy of a report the course never received |

**Work required:**

1. Add a `box_email_key` field to `SessionConfig`, or derive it as
   `f"{session_type.lower()}_box_email"`. Set `enable_email_to_box = True` on all four pages.
2. Port the send block into `mi_session._render_feedback`, immediately after
   `generate_pdf_report` at `mi_session.py:317-323` and before the `st.download_button` at
   `:329-334`.
3. Preserve the download gating behaviour above.
4. Add `MI_BOX_EMAIL_OVERRIDE`, which when set replaces the resolved recipient for every bot.
   Track B sets this to a test mailbox. Without it, restoring the send would cause every
   Track B session to email a real course folder.

**Identity note.** The Box PDF carries the real student name, unchanged. Box is the sanctioned
system of record for graded output, and Phase 6 de-identification must not be applied to it.
The de-identification boundary sits between the front end and MSI, not between the front end
and Box.

**Risk.** This restores a live SMTP dependency in the student-facing path. `config.json:7`
currently holds an empty `smtp_app_password`, so the credential must be confirmed working
before this ships. It also reintroduces the failure mode where a Gmail outage blocks the
download button, which is why the skip control must be ported with it.

### 12.2 MSI backend store

MSI receives three record types per session, all keyed by the opaque session identifier from
section 1.3.2, all pseudonymous, all under Tier 1 project storage.

| Record | Path | Content |
|---|---|---|
| Conversation history | `$MI_STATE_DIR/<yyyy-mm>/<session_id>.jsonl` | One line per turn: timestamp, role, scrubbed content |
| Evaluation result | `$MI_STATE_DIR/<yyyy-mm>/<session_id>.eval.json` | The full `EvaluationResult`: scores, levels, rationales, evidence quotes, recommendations |
| Application logs | `$MI_LOG_DIR/` | Scrubbed application logs, rotated |

`MI_STATE_DIR` and `MI_LOG_DIR` point at `/projects/standard/<project>/`.

**Never use `/scratch.global`.** Files there are deleted 30 days after creation, which is
shorter than a semester.

**No PDF is written to MSI.** The PDF exists in exactly two places: the student's browser
download and the course Box folder.

**Log scrubbing is mandatory, not optional.** Application logs today are written by
`logger_config.py` and include `log_action` calls carrying student names. Writing them to MSI
unscrubbed would place FERPA-protected data on MSI just as surely as an unscrubbed transcript
would. The `scrub()` function from Phase 6 must be applied in a logging filter, not only in
the evaluation path. This is the single easiest way to breach the boundary by accident.

### 12.3 Session resume

Write `session_id` into `st.query_params` at session start. On page load, if the identifier is
present and `st.session_state.chat_history` is empty, replay the journal. This makes a browser
reconnection after a service restart non-destructive.

### 12.4 Fix the double-redemption race

`secret_code_portal.py` reads access codes through `@st.cache_data(ttl=300)` at `:230` and
performs a non-atomic read, check, then write against `update_cell` at `:514-517`. Two
students presenting the same code within the five-minute cache window both succeed.

This is a pre-existing defect in production that becomes worse on MSI, because
restart-and-resume patterns and any multi-process serving multiply the number of divergent
caches.

- Minimum fix: re-read the single target row uncached immediately before `update_cell` and
  abort if `Used` is already `TRUE`.
- Preferred fix: a dedicated redemption table with a unique constraint.

Because Track B uses a separate test sheet, this can be exercised destructively without any
risk to real student codes.

### 12.5 Database schema decision

`database/mi_sessions.sql` was deleted in Phase 1. The MSI store in section 12.2 is
file-based, which is sufficient for a fallback and avoids running a database service under a
Slurm walltime ceiling. If a relational store later proves necessary, author a **new** SQLite
schema generated from the actual `EvaluationResult` shape. Do not resurrect the old schema: it
encodes a 30-point 4-category rubric while the live rubric is 40 points across 6 categories,
and reviving it would introduce an incorrect rubric into a graded system.

**Verification.**

| Check | Method |
|---|---|
| Box archiving works | Complete a Track B session with `MI_BOX_EMAIL_OVERRIDE` set to a test mailbox. Confirm the PDF arrives and the download button appears only after backup resolves |
| Box failure is survivable | Point SMTP at an unreachable host. Confirm the queue accepts the entry, the warning renders, and the skip control releases the download |
| Transcript reaches MSI | Confirm the JSONL file exists, one line per turn |
| Evaluation reaches MSI | Confirm the `.eval.json` file matches the on-screen scores |
| **No PDF on MSI** | `find $MI_STATE_DIR -name '*.pdf'` must return nothing |
| **No identity on MSI** | Run a session as a distinctive test name, then `grep -ri "<name>" $MI_STATE_DIR $MI_LOG_DIR`. Must return nothing. This covers logs, not just transcripts |
| Session resume | Add turns, terminate the process, restart, reload the session URL, confirm history is intact |
| Redemption race | Redeem one test code from two simultaneous clients; exactly one succeeds |

The two checks in bold are the machine-checkable statement of the storage split and belong in
the compliance evidence alongside the Phase 6 recording assertion.

---

## 13. Phase 8: Containerization with Apptainer

**Prerequisites: Phases 2 and 5 must be complete.** See section 4.1.

**Goal.** A reproducible, read-only application image that runs on MSI.

1. Author a `Dockerfile` (none exists today) based on `python:3.11-slim`, installing from
   `requirements.lock`, running as a non-root user with `WORKDIR /app`.
2. Convert to Apptainer:

```bash
apptainer build mi-app.sif docker-daemon://mi-app:$(git rev-parse --short HEAD)
```

If a local Docker daemon is unavailable, author an Apptainer definition file and build
directly on MSI.

3. Declare bind mounts for every writable path, all outside the image:
   `--bind $MI_STATE_DIR --bind $MI_LOG_DIR --bind $MI_QUEUE_DIR --bind $MI_SECRETS_DIR:ro`.
4. Use the stock vLLM image (`docker://vllm/vllm-openai:<tag>`) rather than building one.

**Verification.**

```bash
apptainer exec mi-app.sif python -m pytest /app/tests -q
```

Then run the container with a read-only filesystem and no writable tmpfs. It must start
without a filesystem error. That assertion is precisely what Phase 5 buys.

---

## 14. Phase 9: vLLM service jobs and endpoint registry

**Prerequisites: MSI Help Desk answers to questions 5 and 8; the error-classification work in
Phase 3 complete.**

**Goal.** OpenAI-compatible inference endpoints that the front end can locate after every
restart.

### 14.1 Two model services

| Service | Model | Partition | Rationale |
|---|---|---|---|
| Chat and extraction | Llama 3.1 8B | `interactive-gpu` or `preempt-gpu` (A40 or L40S) | Fits comfortably on one GPU; serves the latency-sensitive path |
| Scoring | Llama 3.3 70B | `a100-4-long` (96 hours, ticket required) or `msigpu` (24 hours) | Requires 4 A100 GPUs at bf16, fewer if quantized |

Example submission for the scorer:

```bash
#SBATCH -p a100-4-long
#SBATCH --gres=gpu:a100:4
#SBATCH -t 96:00:00
apptainer run --nv vllm.sif --model <llama-3.3-70b-path> --port $PORT \
    --served-model-name eval-70b --gpu-memory-utilization 0.92
```

### 14.2 The endpoint registry

This is the most important design element in the phase.

vLLM jobs are capped at 24 to 96 hours. A front-end job can run 37 days. **The vLLM job will
restart on a different node many times during a single front-end lifetime.** A static
`MI_LLM_BASE_URL` therefore guarantees repeated outages.

Design:

1. The vLLM startup script polls its own `/health` endpoint until it returns HTTP 200.
2. It then atomically writes `<hostname>:<port>` to `$PROJ/run/eval-70b.endpoint` using
   write-to-temp followed by `os.replace`.
3. It removes the file in a shell `trap ... EXIT` handler.
4. `llm_provider.load_settings()` gains a registry mode: re-read the file on each client
   construction, with a short in-process TTL cache. This is inexpensive because
   `mi_session.py:410` already constructs a client per page render.
5. A missing registry file produces a clean message ("The evaluation service is starting up,
   please try again in a few minutes"), not a stack trace.

Because the Track B front end runs off MSI under the hybrid architecture, it reads the
registry through whichever mechanism the Help Desk sanctions for cross-network access. This is
the substance of Help Desk questions 3 and 12, and the answer determines whether the registry
is a shared filesystem read, a small HTTP shim, or a manually updated secret.

### 14.3 Cold-start behaviour

Loading a 70B model into vLLM takes three to ten minutes. The first request after a job start
will exceed any reasonable client timeout. This is not a client defect. It is the reason the
registry file must be written only after `/health` returns 200.

### 14.4 Graceful degradation

Because `mi_evaluation.py:342-350` already falls back from the extractor model to the scorer
model on a 404, an outage of the 8B service degrades gracefully. **This works only after the
Phase 3 error-classification fix**, because the current detection strings are Groq-shaped.

**Verification.**

```bash
curl -s $ENDPOINT/v1/models
```

Then point the Track B application at the endpoint and run:

```bash
python -m pytest tests/ test_evaluation.py -q
```

Follow with a live end-to-end session. **If any application code requires editing at this
point, Phase 3 was incomplete.** That is the acceptance test for the entire abstraction.

---

## 15. Phase 10: Streamlit service job (conditional)

**This phase applies only if the MSI Help Desk clears public reachability (questions 2, 3, 6,
and 11), or for a VPN-only pilot cohort.** Under the approved hybrid architecture the front
end otherwise stays off MSI and this phase is skipped entirely.

- **Partition: `msilong` (32 cores, 128 GB), not `interactive-long`.** The latter provides
  2 cores, and interactive partitions permit only one concurrent job per user, which would
  collide with debugging sessions.
- **Streamlit configuration.** The committed `.streamlit/config.toml` sets no port, address,
  headless flag, or base URL path. Do not mutate it. Add `.streamlit/config.msi.toml` or pass
  explicit flags: `--server.headless=true --server.port=$PORT --server.address=0.0.0.0
  --server.baseUrlPath=/mi --browser.gatherUsageStats=false`. If a reverse proxy is used,
  `enableCORS` and `enableXsrfProtection` require a deliberate decision.
- **Supervision.** None exists today. Add a `--signal=B:USR1@900` handler that resubmits the
  job before walltime expiry, plus an external watchdog polling `/_stcore/health`. Phase 7's
  journal makes the resulting restart non-destructive.
- **Maintenance windows** will interrupt the service regardless. Schedule around them.

**Verification.**

```bash
curl -f http://<node>:$PORT/_stcore/health
```

Terminate the job and confirm automatic resubmission. Reload a live session URL after restart
and confirm resume works.

---

## 16. Phase 11: Capacity and load testing

**Goal.** Size the system before any student traffic reaches Track B. This is not optional.

A 70B model at bf16 on four A100 GPUs delivers roughly 15 to 30 tokens per second per
concurrent stream. An evaluation response is approximately 1,000 to 1,500 tokens. A class of
thirty students finishing their sessions within the same ten minutes is a queueing problem.
There is no streaming anywhere in the application today and no progress indication beyond
`st.spinner`.

Mitigation levers, in order of preference:

1. Use the 8B model for evidence extraction (already the default at `mi_evaluation.py:297`).
2. Quantize the 70B model (AWQ or FP8) to fit two GPUs and raise `--max-num-seqs`.
3. Increase the Phase 3 timeout.
4. Add streaming to the chat turn so the 8B path feels immediate even while the 70B queue is
   deep.

**Verification.** Build a concurrency harness driving N simultaneous full evaluations. Record
p50 and p95 end-to-end latency and error rate at N = 10, 20, and 40. Compare against the
observed concurrency of the largest real cohort.

---

## 17. Phase 12: Parallel run, decision, and cutover

This is the only phase that touches production.

### 17.1 Parallel run

Run Track B alongside production for one full course cycle. Route a single small cohort, for
example the Perio bot, to the Track B application while every other cohort continues on
production untouched.

Requirements before any student is routed to Track B:

- Phase 11 load testing complete and within acceptable latency.
- Written FERPA determination on file (Phase 0).
- Track B pointed at a **production-equivalent** Google Sheet for the pilot cohort, not the
  test sheet, with real codes for those students only.
- `MI_SMTP_ENABLED` reviewed and set deliberately.
- The test-environment banner from Phase 1 removed for the pilot.

### 17.2 Score comparison

**Compare score distributions between the Groq-scored production cohorts and the vLLM-scored
pilot cohort.** Different model weights produce different scores, and this is a graded
artifact. Budget for a rubric calibration pass. This risk is not covered in the original
research document and is the most likely reason a technically successful migration would be
rejected.

### 17.3 Decision point

At the end of the parallel cycle, one of three outcomes:

| Outcome | Action |
|---|---|
| Track B performs equivalently | Proceed to cutover |
| Track B works but scores differ materially | Calibrate, then repeat the parallel cycle. Production continues untouched |
| Track B is not viable | Abandon or defer. Production continues untouched. Nothing to roll back |

The third outcome is the point of the two-track structure. If the migration fails, there is
no rollback to perform, because production was never modified.

### 17.4 Cutover, if approved

1. Merge `msi-hybrid` into `main`. Tag the merge commit.
2. Update the production Streamlit Cloud application configuration: `MI_LLM_BASE_URL`,
   `MI_LLM_API_KEY`, `MI_SHEET_ID` (production sheet), `MI_SMTP_ENABLED`, `MI_DEIDENTIFY`.
3. Update student onboarding instructions to remove the Groq API key step.
4. Rewrite `README.md`. It currently documents at least a dozen files that do not exist and
   instructs readers to run entry points that were removed.
5. Keep the Track B application deployed for one further cycle as a fallback.

**Post-cutover rollback.** Set `MI_LLM_BASE_URL` and `MI_LLM_API_KEY` back to Groq. If
Phase 3 was implemented correctly, that is the entire rollback and it takes under a minute.

---

## 18. Documentation deliverables

The user requirement is formal documentation of all changes. The following documents are
produced during implementation, not after. All are committed to `msi-hybrid` and reach `main`
only at cutover.

| Document | Created in | Content |
|---|---|---|
| `docs/MSI_MIGRATION_RESEARCH.md` | Complete | MSI capability research and constraints (already written) |
| `docs/MIGRATION_PLAN.md` | Phase 1 | This plan, committed to the repository |
| `docs/TRACK_ISOLATION.md` | Phase 1 | Section 2 of this plan, expanded: the two-track model, the shared-resource decoupling table, and the permitted production touches with their approval status |
| `docs/CHANGELOG_MIGRATION.md` | Every phase | One dated entry per phase: what changed, which files, why, and how it was verified |
| `docs/CONFIGURATION.md` | Phase 3 | Every environment variable: name, purpose, default, valid values, which track uses it, and which phase introduced it |
| `docs/ARCHITECTURE.md` | Phase 6 | The hybrid architecture, the trust boundary, and the data-flow diagram showing where identity stops |
| `docs/FERPA_COMPLIANCE.md` | Phase 6 | The identity surface inventory, the de-identification design, and the recording-assertion test as evidence |
| `docs/RUNBOOK_MSI.md` | Phase 9 | Job submission, endpoint registry operation, restart procedure, health checks, and troubleshooting |
| `docs/CUTOVER_CHECKLIST.md` | Phase 12 | The ordered production cutover steps from section 17.4, with a sign-off line per item |
| `README.md` rewrite | Phase 12 | The existing README is substantially inaccurate and must be rewritten, not patched |

Documentation standard for all of the above: no em dashes, no emoji, formal register,
declarative statements, tables in preference to prose where a table fits, and every claim
anchored to a file path.

---

## 19. Critical files

Primary:

- `mi_session.py` (client construction, model defaults, chat call, feedback orchestration)
- `mi_evaluation.py` (evaluator calls, error classification, schema validation)
- `secret_code_portal.py` (entry point, authentication, sheet ID, API key removal)
- `requirements.txt` and new `requirements.lock`
- `config.json` (paths, SMTP configuration, feature flags)

New modules:

- `llm_provider.py` (Phase 3)
- `deident.py` (Phase 6)

Supporting:

- `logger_config.py`, `email_utils.py`, `email_queue.py`, `config_loader.py`,
  `utils/access_control.py`, `mi_pdf.py`, `pages/developer_page.py`

Test contract:

- `test_evaluation.py` (the `FakeClient` harness at `:66` is the interface the Phase 3
  abstraction must not break)
- `tests/`

---

## 20. Verification summary

| Phase | Primary verification |
|---|---|
| 0 | Production reads and writes the live sheet on the rotated credential; Track B application reachable and reading the test sheet |
| 1 | Full suite green; a Track B session marks a code used on the **test** sheet with the production sheet unchanged |
| 2 | Fresh install from `requirements.lock`; `python -c "import torch"` must fail |
| 3 | Full suite green with **zero test edits**; live Groq session through the new abstraction on Track B |
| 4 | `grep -rn "os.environ\[" --include=*.py .` shows no request-path assignment; two-browser concurrency check |
| 5 | Start from a foreign working directory with `MI_LOG_DIR` and `MI_QUEUE_DIR` set |
| 6 | Golden-score regression test; recording assertion test |
| 7 | Box PDF arrives at a test mailbox; transcript and evaluation land on MSI; `find $MI_STATE_DIR -name '*.pdf'` returns nothing; grep for a test student name across `$MI_STATE_DIR` and `$MI_LOG_DIR` returns nothing; session resume works; single-redemption holds |
| 8 | `apptainer exec mi-app.sif python -m pytest /app/tests -q` with a read-only filesystem |
| 9 | `curl $ENDPOINT/v1/models`; full suite and a live session against vLLM |
| 10 | `curl -f .../_stcore/health`; forced restart and resume |
| 11 | Concurrency harness at N = 10, 20, 40 |
| 12 | Score distribution comparison between the production and pilot cohorts |

Throughout Phases 1 to 11, one standing verification applies: **the production application
must remain reachable and functional.** Check it at the end of every working session.

---

## 21. Risk register

| Risk | Phase | Severity | Mitigation |
|---|---|---|---|
| Track B testing consumes real student access codes | 1 | **High** | Configurable `MI_SHEET_ID` and a separate test sheet are the first item of Phase 1, before any Track B session is run |
| Credential rotation causes a production Sheets outage | 0 | Medium | Mint and deploy the new key before disabling the old one; verify production between the two steps; schedule in a low-traffic window |
| FERPA determination prohibits pseudonymous transcripts on MSI | 0 | Blocking for Phases 8 to 12 | Obtain the determination before Phase 8. Production is unaffected either way |
| De-identification silently changes student scores via `_verify_quotes` | 6 | High | Golden-score regression tests written before implementation |
| Groq-shaped error strings break the extractor fallback on vLLM | 9 | High | Fixed in Phase 3, ahead of Phase 9 |
| vLLM restart takes down the front end | 9 | High | Endpoint registry file, never a static base URL |
| Compute nodes lack outbound internet, breaking SMTP and Google Sheets | 5, 9 | High | Help Desk question 5; the hybrid architecture already keeps Sheets and SMTP on the front end, off MSI |
| Different model weights produce different scores on a graded artifact | 12 | High | Parallel cohort run, score distribution comparison, and a rubric calibration pass |
| Track B emails test PDFs to the real Box archive | 1, 7 | **High from Phase 7** | `MI_SMTP_ENABLED=false` today. Once archiving is restored, `MI_BOX_EMAIL_OVERRIDE` must ship in the same commit |
| Application logs carry student names onto MSI | 7 | **High** | The Phase 6 `scrub()` must be applied as a logging filter, not only in the evaluation path. Verified by grepping `$MI_LOG_DIR` for a distinctive test name |
| A PDF is written to MSI by accident | 7 | Medium | Explicit verification step: `find $MI_STATE_DIR -name '*.pdf'` must return nothing |
| Restored Box send blocks the download button during a Gmail outage | 7 | Medium | Port the "Skip and Download Only" control together with the send block; it exists in the reference implementation |
| SMTP credential is not actually working | 7 | Medium | `config.json:7` holds an empty `smtp_app_password`. Confirm the credential before shipping the restoration |
| 70B throughput inadequate for a full class finishing simultaneously | 11 | Medium | Load test before any student is routed to Track B |
| Leaked Google service-account key is used before rotation | 0 | Medium | Rotate immediately, before any credential is copied to MSI |
| `msi-hybrid` drifts far from `main` | All | Medium | Track A change freeze (section 2.3); rebase after every `main` commit |
| Container build fails on writable paths | 8 | Medium | Phase 5 is a hard prerequisite |
| Students receive the Track B URL by mistake | 1 | Medium | Test-environment banner; viewer restriction on the Track B application if supported |
| Streamlit or gspread version drift changes behaviour | 2 | Low | Capture `pip freeze` from the live deployment, then pin and lock |
| Removing `end_control_middleware` reduces the test safety net | 1 | Low | Scheduled in Phase 1, before any refactoring begins, and on a branch only |

---

## 22. Immediate next actions

1. Tag `main` as `pre-msi-baseline` and create the `msi-hybrid` branch.
2. Create the test Google Sheet and deploy the second Streamlit Cloud application from
   `msi-hybrid`.
3. Approve or decline the two optional production touches in section 2.4 (CI workflow and
   `.gitignore` hardening).
4. Schedule and perform the Google service-account key rotation, including production
   verification (Phase 0, section 5.1).
5. Send the twelve questions to the MSI Help Desk (Phase 0, section 5.3).
6. Request the written FERPA determination (Phase 0, section 5.4).
7. Identify the faculty PI and create the MSI project through MyMSI (Phase 0, section 5.5).
8. Begin Phase 1, starting with the configurable sheet ID.

Items 1, 2, and 8 require none of the others to complete and can begin immediately.
