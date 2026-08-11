# MSI Migration Tracker

Document version: 1.1
Date: 2026-08-11
Tracks: `MIGRATION_PLAN.md` version 2.1
Integration branch: `msi-hybrid`
Baseline tag: `pre-msi-baseline` (historical; `main` has moved once, for PR #117)

Update the status table in section 3 as each phase lands. This file is the
single place to look for where the migration stands.

---

## 1. Branch and pull request strategy

### 1.1 The rule

**No pull request targets `main` until Phase 12.**

Each phase gets its own branch off `msi-hybrid` and its own pull request **into
`msi-hybrid`**. At cutover, one final pull request merges `msi-hybrid` into
`main`.

```
main  (frozen, production)
  |
  |  <-- one PR, at Phase 12 cutover only
  |
msi-hybrid  (integration branch)
  ^   ^   ^
  |   |   |  <-- one PR per phase
  |   |   msi/phase-4-api-keys
  |   msi/phase-3-llm-provider
  msi/phase-2-deps
```

### 1.2 Why not a pull request to `main` now

Three reasons, in order of weight:

1. **`main` has no branch protection.** Confirmed on 2026-08-02: the GitHub API
   returns "Branch not protected". A pull request against `main` is a live merge
   button on a branch that must not reach production until the Phase 12 decision.
   One misclick ends the isolation guarantee.
2. **The repository is public.** A large open pull request against `main` reads
   to any observer as the intended next state of production. It is not.
3. **Nothing is ready to merge.** Phase 1 is isolation scaffolding. It has value
   only in combination with Phases 2 through 11.

If a review surface against `main` is wanted before cutover, open it as a
**draft** pull request titled `DO NOT MERGE`, and enable branch protection on
`main` first. Enabling protection is worth doing regardless.

### 1.3 Naming

| Item | Convention |
|---|---|
| Phase branch | `msi/phase-<n>-<slug>`, for example `msi/phase-3-llm-provider` |
| Pull request title | `Phase <n>: <goal>` |
| Pull request base | `msi-hybrid`, always, until Phase 12 |

### 1.4 Every phase pull request must state

- Which plan section it implements.
- The CI result. The suite is green as of Phase 1a, so the expected figure is
  zero failures.
- Confirmation that production remains reachable.
- Its rollback posture.

---

## 2. Merge gates

A phase pull request may merge into `msi-hybrid` when all of these hold.

| Gate | Requirement |
|---|---|
| CI | **Green. Zero failures.** Since Phase 1a cleared the inherited 17, any failure is a real regression and blocks the merge |
| Production untouched | The pull request targets `msi-hybrid`, never `main`. `main` moves only by a deliberately approved Track A fix, as PR #117 was |
| Plan reference | The pull request names the section it implements |
| Changelog | A `CHANGELOG_MIGRATION.md` entry is included in the same pull request |
| Ordering | Every hard prerequisite in plan section 4.1 is satisfied |

---

## 3. Status

Legend: Done, In progress, Blocked, Not started.

| Phase | Title | Branch | PR | Status | Gate |
|---|---|---|---|---|---|
| 0 | Unblock: security, accounts, environment | n/a | n/a | **In progress** | Key rotation and Help Desk answers outstanding |
| 1 | Track B setup, safety net, dead code removal | `msi-hybrid` direct | none | **Done** 2026-08-02 | CI run, zero new failures |
| 1a | Clear the 17 stale test failures | `msi/phase-1a-stale-tests` | #118 | **Done** 2026-08-11 | Merged. CI green |
| - | Integrate PR #117 from main | `msi-hybrid` direct | #117 | **Done** 2026-08-11 | Merged + semantic fix. CI green, 228 passed |
| 2 | Dependency prune, pin, lock | `msi/phase-2-deps` | not opened | Not started | None. Ready to start |
| 3 | LLM provider abstraction | `msi/phase-3-llm-provider` | not opened | Not started | None. Ready to start |
| 4 | Retire per-student API keys | `msi/phase-4-api-keys` | not opened | Not started | After Phase 3. PR #117 now merged, overlap resolved |
| 5 | Path externalization | `msi/phase-5-paths` | not opened | Not started | Blocks Phase 8 |
| 6 | FERPA de-identification boundary | `msi/phase-6-deident` | not opened | Not started | **Blocked** on the A1 FERPA answer. Blocks Phase 7 |
| 7 | Data persistence: Box archiving and MSI store | `msi/phase-7-persistence` | not opened | Not started | After Phase 6. Needs A3 answer for the MSI half |
| 8 | Containerization with Apptainer | `msi/phase-8-container` | not opened | Not started | **Blocked** on MSI account. After Phases 2 and 5 |
| 9 | vLLM service jobs and endpoint registry | `msi/phase-9-vllm` | not opened | Not started | **Blocked** on MSI answers A2, B1 |
| 10 | Streamlit service job (conditional) | `msi/phase-10-frontend` | not opened | Not started | **Conditional.** Skipped unless A2 or A4 allows it |
| 11 | Capacity and load testing | `msi/phase-11-load` | not opened | Not started | After Phase 9 |
| 12 | Parallel run, decision, cutover | `msi-hybrid` to `main` | not opened | Not started | Everything above, plus a written FERPA determination |

### 3.1 Phase 0 detail

| Item | Status | Owner |
|---|---|---|
| Rotate Google service-account key | **Outstanding. Urgent** | User |
| Send Help Desk questions (`MSI_HELPDESK_QUESTIONS.md`) | Outstanding | User |
| Written FERPA determination from UMN privacy office | Outstanding | User |
| Faculty PI creates MSI project via MyMSI | Outstanding | User |
| Create test Google Sheet | Outstanding | User |
| Deploy Track B Streamlit app from `msi-hybrid` | Outstanding | User |
| Decide the two optional production touches | Outstanding | User |

**On the key rotation.** The repository is public, confirmed 2026-08-02. The
Google service-account private key in commits `0ebde65`, `d6ea9e5`, and
`64dbfe2` is therefore recoverable by anyone on the internet, not only by
collaborators. This raises the rotation from required to urgent, and it is
independent of the migration.

---

## 4. Conflict watch

Work in flight that will collide with a migration phase.

### PR #117: RESOLVED, merged 2026-08-11

Merged into `main` at `486b51e`, then merged into `msi-hybrid` at `ad9f6e5`.
Both branches now carry all three fixes. The follow-up in `8deba8f` repaired the
semantic conflict described in section 5.1.

The original analysis is retained below for context.

### PR #117, `claude/heuristic-bohr-05a3c6`, targeting `main`

Touches `email_queue.py`, `mi_session.py`, `tests/test_email_queue.py`. Three
fixes, all overlapping this plan:

| Fix in #117 | Overlaps |
|---|---|
| Groq client race: pass `Groq(api_key=...)` instead of mutating `os.environ` | Phase 3 (`make_client`) and Phase 4 (removing the key entirely) |
| Dead rubric load removed | Phase 2 section 7.5, same recommendation |
| `EmailQueue.remove()` double-load bug | Phase 5 and Phase 7, which both touch the queue |

**Recommendation: merge #117 into `main`.** The Groq race is a live defect that
can bill one student's requests to another student's key, so it qualifies as a
production bug fix under the Track A freeze. It also makes production safer
while the migration runs.

**Then rebase `msi-hybrid` onto `main` immediately.** Expect a conflict in
`mi_session.py` around the client construction at lines 408 to 410, which both
#117 and Phase 3 rewrite. Resolve in favour of the Phase 3 abstraction, which
supersedes #117's fix by removing the `os.environ` write entirely.

### Older open pull requests

`#105`, `#104`, `#102` are stale, from January to March 2026. Close them or
merge them before the migration proceeds, so the conflict surface stops growing.

---

## 5. Integration discipline

- **Merge `main` into `msi-hybrid` after every commit that lands on `main`.**
  Earlier versions of this document said rebase. That was written before
  `msi-hybrid` was pushed and before PR #120 existed. Rebasing now would mean
  force-pushing published history under an open pull request, so merge instead.
  It reaches the same state without rewriting anything.
- Phase branches, which are short-lived and unpushed until their pull request,
  may still be rebased onto `msi-hybrid` freely.
- Never merge `msi-hybrid` into `main` before the Phase 12 decision.
- `pre-msi-baseline` marks the original frozen state. It is now historical:
  `main` has deliberately moved once, for PR #117. Compare against `origin/main`
  from here, not against the tag.

### 5.1 Watch for semantic conflicts

A clean textual merge does not mean a correct one. When PR #117 landed, git
merged it into `msi-hybrid` with a single trivial docstring conflict, yet the
result failed two tests: #117 deleted `mi_session._load_rubric_text`, while
tests added in Phase 1a asserted that function exists. The changes were in
different files, so git could not see the contradiction.

**After every merge from `main`, run CI before assuming the branch is healthy.**
This is also the clearest argument for the zero-failure gate: against the old
17-failure baseline, two new failures would have been lost in the noise.

---

## 6. Test baseline

| Branch | Result |
|---|---|
| `pre-msi-baseline` (equals `main`) | 17 failed, 226 passed, 2 skipped |
| `msi-hybrid` after Phase 1 | 17 failed, 216 passed, 2 skipped |
| `msi-hybrid` after Phase 1a | 0 failed, 221 passed, 2 skipped |
| `msi-hybrid` after merging PR #117 (`ad9f6e5`) | 2 failed, 227 passed, 2 skipped |
| `msi-hybrid` after the semantic fix (`8deba8f`) | **0 failed, 228 passed, 2 skipped** |

**The suite is green. Any failure from this point is a real regression and
blocks the merge.**

Note that `main` itself is still red at 17 failures. That is expected and is not
a defect in production: the failures are stale assertions about code layout, and
they are fixed only on `msi-hybrid`. They will reach `main` at the Phase 12
cutover along with everything else.

Detail in `CHANGELOG_MIGRATION.md` under "Phase 1a: stale test cleanup".
