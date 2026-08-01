# Track Isolation

Document version: 1.0
Date: 2026-07-31
Applies to: the MSI migration work described in `MIGRATION_PLAN.md`

---

## 1. Purpose

The MSI migration is carried out without interrupting the running application.
This is achieved by operating two deployments from one repository, isolated so
that no action in the migration environment can affect a live student.

This document defines that isolation and is the reference for anyone configuring
either deployment.

---

## 2. The two tracks

| | Track A: Production | Track B: Migration |
|---|---|---|
| Git branch | `main` | `msi-hybrid` |
| Baseline tag | `pre-msi-baseline` | n/a |
| Deployment | Existing Streamlit Community Cloud application | Second Streamlit Community Cloud application |
| Inference | Groq, per-student API keys | Groq initially, then MSI vLLM |
| Access code sheet | Production Google Sheet | Separate test sheet |
| Outbound email | Enabled | Disabled |
| Students | Real cohorts | Implementer, then one pilot cohort |
| Change policy | Frozen: security and live-defect fixes only | Active development |

Track A remains authoritative until an explicit cutover decision. If the
migration is abandoned, there is nothing to roll back.

---

## 3. Environment variables

All isolation is controlled by environment variables read in `app_env.py`. Every
variable defaults to production behaviour, so an unconfigured deployment behaves
exactly as the application did before this module existed.

| Variable | Default | Track A value | Track B value |
|---|---|---|---|
| `MI_SHEET_ID` | Production sheet ID | Unset, or the production sheet ID | The test sheet ID |
| `MI_SHEET_NAME` | `Sheet1` | Unset | Worksheet name in the test sheet |
| `MI_ENVIRONMENT` | `production` | Unset | `test` |
| `MI_SMTP_ENABLED` | `true` | Unset | `false` |

On Streamlit Community Cloud these are set per application under Settings, then
Secrets.

### 3.1 `MI_SHEET_ID`

The single most important isolation control. The access code sheet is the
system of record, and redeeming a code writes `TRUE` to its `Used` column. If
Track B pointed at the production sheet, a test run would consume a real
student's access code and lock that student out.

The production sheet ID remains in `app_env.py` as the documented default so
that Track A behaviour is unchanged. A continuous integration check
(`.github/workflows/ci-msi-hybrid.yml`) fails the build if the production sheet
ID appears anywhere else in the Python source.

### 3.2 `MI_ENVIRONMENT`

Setting this to `test` displays a red banner on the portal, on all four bot
pages, and on the developer page, reading "TEST ENVIRONMENT. Not for student
use." This is the safeguard for a student who receives the wrong link.

The banner is rendered by `app_env.render_environment_banner()`, called from
`secret_code_portal.py`, `mi_session.run_practice_session`, and
`pages/developer_page.py`.

### 3.3 `MI_SMTP_ENABLED`

Setting this to `false` suppresses every outbound SMTP connection. It is checked
at five entry points in `email_utils.py`:

| Method | Behaviour when disabled |
|---|---|
| `SecureEmailSender.send_email_with_attachment` | Returns `False` without connecting |
| `SecureEmailSender.send_email_with_retry` | Returns a result with an explanatory error |
| `SecureEmailSender.test_connection` | Returns status `disabled` without connecting |
| `RobustEmailSender.send_with_guaranteed_delivery` | Returns without connecting **and without queueing** |
| `RobustEmailSender.process_failed_queue` | Returns an empty result set |

The check in `send_with_guaranteed_delivery` is placed before the retry loop
deliberately. If it were placed lower, a disabled deployment would fall through
to the retry queue, and `email_queue.py` would write a named student PDF to
disk. Suppressing that write is part of the point of the flag.

---

## 4. Shared resources

These are the actual coupling points between the two tracks.

| Resource | Status | Control |
|---|---|---|
| Google Sheet | **Decoupled** | `MI_SHEET_ID` |
| Outbound email and Box archive | **Decoupled** | `MI_SMTP_ENABLED` |
| Google service account | Shared credential, separate sheets | Grant the service account access to both sheets |
| Repository `main` branch | Protected | No merge from `msi-hybrid` until cutover |
| Groq account | Not shared | Track A uses per-student keys; Track B uses an operator key |
| Filesystem, process, session state | Not shared | Separate Streamlit Cloud applications |

---

## 5. Permitted production touches

Three items affect Track A. Each requires explicit approval.

| Item | Status | Notes |
|---|---|---|
| Google service-account key rotation | **Required** | A private key is recoverable from git history. Mint and deploy the new key, verify production, then disable the old key |
| `.github/workflows/deploy.yml` | Pending approval | Triggers on push to `main` and performs a live Gmail SMTP login on every push |
| `.gitignore` hardening | Pending approval | Applied to `msi-hybrid`. Applying it to `main` as well prevents a production hotfix from committing student PDFs |

Nothing else in the migration reaches production before cutover.

---

## 6. Branch discipline

- `main` was tagged `pre-msi-baseline` at the start of this work.
- Rebase `msi-hybrid` onto `main` after every commit that lands on `main`.
- Never merge `msi-hybrid` into `main` before the cutover decision.
- Track A accepts only security fixes and live-defect fixes for the duration.

---

## 7. Verification checklist

Run before allowing any traffic to Track B:

1. `MI_SHEET_ID` in the Track B application points at the test sheet.
2. Redeeming a code in Track B marks it used on the **test** sheet, and the
   production sheet is unchanged.
3. The test environment banner is visible on the portal and on a bot page.
4. `MI_SMTP_ENABLED` is `false` and completing a session produces no email and
   no file in the queue directory.
5. The production application is reachable and functioning normally.

Item 5 applies at the end of every working session, not only at setup.
