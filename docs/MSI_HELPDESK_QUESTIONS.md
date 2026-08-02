# Questions for the MSI Help Desk

Document version: 1.0
Date: 2026-08-02
Supersedes: the ten questions in `MSI_MIGRATION_RESEARCH.md` section 7
Contact: `https://msi.umn.edu/helpdesk`, 612-626-0802, 599 Walter Library

This list is rewritten against plan version 2.1 (hybrid architecture, storage
split). Two questions are blocking. One is new and did not exist in the earlier
list.

---

## How to use this

Send Group A first. Those four answers determine whether the project proceeds as
designed. Groups B and C can follow in the same ticket or a second one, but do
not wait on them: Phases 1 through 7 of the migration need none of these
answers.

A ready-to-paste version is in section 5.

---

## 1. Context to give MSI

Include this preamble. Help Desk answers are much more useful when they know the
shape of the workload.

> We run a Motivational Interviewing training application for School of
> Dentistry students. It is a Python web application that currently uses a
> commercial hosted LLM API. We want to move the AI inference and the backend
> data store to MSI, while the student-facing web front end stays on a
> University-approved public host.
>
> Concretely we want to run two vLLM servers on MSI GPUs, serving Llama 3.1 8B
> and Llama 3.3 70B, reachable from that external front end. We also want to
> store conversation transcripts, evaluation results, and application logs in
> MSI project storage. No student-identifying information would be sent to or
> stored on MSI: transcripts are pseudonymised before they leave the front end.
> Graded PDF reports are archived in Box and never written to MSI.

---

## 2. Group A: Blocking

These four gate the design. Nothing built for MSI should start before they are
answered.

### A1. FERPA and pseudonymised educational records

> The MSI User Agreement prohibits storing data protected by FERPA. Our
> application produces per-student Motivational Interviewing evaluations, which
> are educational records.
>
> We intend to pseudonymise before anything reaches MSI: student names replaced
> with per-session aliases, an opaque session identifier as the only key, and a
> regex sweep for UMN email addresses and student ID numbers. MSI would hold
> conversation transcripts, evaluation scores, and application logs, none of
> which would contain a name or any direct identifier. The mapping from session
> identifier to student would exist only on the external front end.
>
> Does pseudonymised data of this kind fall outside the User Agreement
> prohibition, or is it still treated as FERPA-protected? If it is still
> restricted, is `/projects/regulated/` the correct location, and what is the
> approval process?

**Why this is blocking.** If the answer is that pseudonymised transcripts are
still prohibited, MSI can host inference but cannot host the data store, and the
storage half of the plan is withdrawn.

**Also required:** the same question in writing to the UMN privacy and
compliance office. MSI can state its own policy but cannot make the FERPA
determination on the University's behalf.

### A2. Reaching an MSI-hosted service from outside MSI

> Our web front end runs outside MSI, on a University-approved public host. It
> needs to make HTTPS requests to a vLLM inference server running in a Slurm job
> on an MSI compute node, for the duration of a semester.
>
> Is there a supported way to do this? For example a reverse proxy, a published
> service endpoint, an API gateway, or a persistent tunnel. If not, what is the
> supported pattern for exposing a compute-node service to a client outside the
> UMN network?

**Why this is blocking.** This is the single largest unknown in the hybrid
design. If no supported path exists, the architecture must change: either the
front end moves onto MSI and becomes VPN-only for students, or MSI is used for
batch work only and live inference stays with a commercial API.

### A3. Writing to MSI project storage from an external host

> We want conversation transcripts, evaluation results, and application logs
> written to MSI Tier 1 project storage as they are produced, by a process
> running outside MSI.
>
> What is the supported mechanism? Is there an S3 endpoint, a WebDAV or HTTPS
> interface, or a Globus endpoint suitable for frequent small writes rather than
> bulk transfer? Would you instead recommend buffering on the front end and
> pushing to MSI periodically?

**Why this is blocking, and why it is new.** Earlier versions of this plan
assumed the application ran on MSI, so storage was a local filesystem write.
Under the hybrid architecture the writer is external, and Tier 1 is a POSIX
filesystem normally reached over SSH from inside MSI. There may be no clean
answer, in which case a periodic push replaces continuous journaling.

### A4. Stratus or any current VM service

> Is the Stratus Protected Data Cloud still offered? Its pages are no longer
> reachable and it does not appear in the new user documentation. If it has been
> retired, is there a replacement service offering persistent virtual machines,
> and does any current MSI service support a long-running, publicly reachable
> web application?

**Why this matters.** If a VM service with a public address exists, it is a
better fit than the hybrid split and would simplify the architecture
considerably. Worth confirming before building around its absence.

---

## 3. Group B: Design-shaping

Needed before the MSI-side build, not before the decision to proceed.

### B1. Running vLLM for a 70B model

> What is the recommended way to run a vLLM OpenAI-compatible server on MSI for
> Llama 3.3 70B? Which partition, which GPU allocation, and do you recommend
> quantisation such as AWQ or FP8 to reduce the GPU count? Is there a reference
> job script or module we should start from?

### B2. Service lifetime across the semester

> The longest shared partitions we can see are `msilong` and `interactive-long`
> at 37 days, and `a100-4-long` at 96 hours for GPU work. A semester is about 16
> weeks.
>
> What is the supported pattern for a service that must stay available across
> that period? Is `scrontab` available, or a self-resubmitting job, or would you
> recommend Dedicated Computing instead?

### B3. Cross-partition reachability

> If we run the 8B model on one partition and the 70B on another, can a job on
> one partition reach a service on the other over TCP without an SSH tunnel?

### B4. Outbound network access from compute nodes

> Do compute nodes have outbound internet access? Specifically, HTTPS to
> `huggingface.co` for model weight downloads. We do not need outbound SMTP or
> Google API access from MSI, since email and spreadsheet access remain on the
> external front end.

Note that this question is much less critical than it was in earlier planning.
The storage split moved SMTP and Google Sheets off MSI entirely.

### B5. Storage allocation and retention

> For pseudonymised transcripts, evaluation results, and logs, we expect well
> under 1 TB per year. Is the default Tier 1 project allocation sufficient, and
> what retention applies? We also want to confirm that data is not subject to
> the 30-day scratch purge, since we intend to use `/projects/standard/` rather
> than `/scratch.global/`.

### B6. Managed database

> Is there any managed MySQL, MariaDB, or PostgreSQL service? If not, we will
> use flat files on Tier 1 rather than running a database inside a Slurm job.

---

## 4. Group C: Operational

Needed before go-live, not before building.

### C1. Secrets management

> Where should API keys and service credentials be stored for a job running on
> MSI? We want to avoid placing them on shared project storage.

### C2. Maintenance windows

> What is the cadence and typical duration of maintenance windows, and how much
> notice is given? We need to schedule around them for a student-facing service.

### C3. Consulting scope

> Is consultant support included for a supported research group, or is it billed
> at the published rate? We may want help with the vLLM deployment specifically.

### C4. Accounts for the project

> We will have a faculty Principal Investigator create the project. Do the
> developers working on this need individual MSI accounts, and is a Person of
> Interest designation required for anyone without a UMN Internet ID?

Do not request class accounts for this. They close automatically two weeks after
the semester ends and their data is unrecoverable.

---

## 5. Ready-to-send version

Paste this into a single Help Desk ticket.

---

Subject: Hosting AI inference and a pseudonymised data store for a School of Dentistry teaching application

We run a Motivational Interviewing training application for School of Dentistry
students. It is a Python web application that currently uses a commercial hosted
LLM API. We would like to move the AI inference and the backend data store to
MSI, while the student-facing web front end remains on a University-approved
public host.

Concretely: two vLLM servers on MSI GPUs serving Llama 3.1 8B and Llama 3.3 70B,
reachable from that external front end, plus conversation transcripts,
evaluation results, and application logs in MSI project storage. No
student-identifying information would be sent to or stored on MSI. Transcripts
are pseudonymised before they leave the front end, and graded PDF reports are
archived in Box and never written to MSI.

Four questions determine whether this design is viable. We would appreciate
answers to these first.

1. The User Agreement prohibits FERPA-protected data. Our data would be
   pseudonymised before reaching MSI: names replaced with per-session aliases,
   an opaque session identifier as the only key, and no direct identifiers of
   any kind. The identifier-to-student mapping would exist only on the external
   front end. Does data of this kind fall outside the prohibition, or is it
   still treated as FERPA-protected? If restricted, is `/projects/regulated/`
   the right location and what is the approval process?

2. Is there a supported way for a web application running outside MSI to make
   HTTPS requests to a vLLM server running in a Slurm job on a compute node,
   sustained across a semester? For example a reverse proxy, a published
   endpoint, an API gateway, or a persistent tunnel.

3. What is the supported mechanism for a process running outside MSI to write
   to Tier 1 project storage as data is produced? We are looking for something
   suited to frequent small writes rather than bulk transfer. If none exists,
   would you recommend buffering externally and pushing periodically?

4. Is the Stratus Protected Data Cloud still offered? Its pages are no longer
   reachable and it does not appear in the new user documentation. If retired,
   is there a replacement offering persistent virtual machines, and does any
   current MSI service support a long-running, publicly reachable web
   application?

Further questions, which are not urgent:

5. Recommended approach for running vLLM with Llama 3.3 70B: which partition,
   what GPU allocation, and do you recommend AWQ or FP8 quantisation to reduce
   the GPU count? Is there a reference job script?

6. Supported pattern for a service that must remain available across a 16-week
   semester, given the 37-day limit on `msilong` and 96 hours on `a100-4-long`.
   Is `scrontab` available, or a self-resubmitting job, or is Dedicated
   Computing the right answer?

7. Can a job on one partition reach a service on another over TCP without an SSH
   tunnel?

8. Do compute nodes have outbound HTTPS access to `huggingface.co` for model
   weight downloads?

9. For well under 1 TB per year of text data, is the default Tier 1 project
   allocation sufficient, and what retention applies?

10. Is there any managed MySQL, MariaDB, or PostgreSQL service?

11. Where should API keys and service credentials be stored for a job on MSI?

12. What is the cadence and duration of maintenance windows, and how much notice
    is given?

Thank you.

---

## 6. What each answer changes

| Answer | Consequence |
|---|---|
| A1 restricts pseudonymised data | Drop the MSI data store. Inference only. Transcripts stay on the front end |
| A2 has no supported path | Hybrid fails. Either move the front end onto MSI and accept VPN-only student access, or keep live inference on a commercial API and use MSI for batch work only |
| A3 has no supported path | Buffer on the front end, push to MSI on a schedule rather than per turn |
| A4 confirms a VM service exists | Prefer it over the hybrid split. Simpler, and it may solve A2 and A3 at once |
| B2 says no supported long-running pattern | Price Dedicated Computing, roughly 9,700 to 12,200 US dollars per year |
