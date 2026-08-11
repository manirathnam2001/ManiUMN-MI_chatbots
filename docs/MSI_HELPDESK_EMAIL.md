# Draft email to the MSI Help Desk

Prepared: 2026-08-11
Source: `MSI_HELPDESK_QUESTIONS.md`
Send to: `help@msi.umn.edu` (or via <https://msi.umn.edu/helpdesk>)

## Before sending, fill in

| Placeholder | What to supply |
|---|---|
| `[YOUR NAME]` | Your name and role |
| `[PI NAME]` | The faculty Principal Investigator who will own the MSI project |
| `[DEPARTMENT]` | For example, School of Dentistry, Division of Dental Hygiene |
| `[COHORT SIZE]` | Approximate students per term, and sessions per student |
| `[TERM]` | The term you are targeting, for example Spring 2027 |

Two notes on strategy.

The preamble matters more than it looks. Help Desk answers improve markedly when
they understand the workload shape, and stating up front that no
student-identifying data would reach MSI reframes question 1 from "may we store
student records" into "is this still a student record at all".

Question 1 should go to the UMN privacy and compliance office in parallel. MSI
can state its own policy but cannot make a FERPA determination on the
University's behalf.

---

## Subject

Hosting LLM inference and a pseudonymised data store for a School of Dentistry teaching application

---

## Body

Dear MSI Help Desk,

I am writing to ask about hosting part of a teaching application on MSI, and to
confirm several constraints before we commit to a design.

**Background**

We run a Motivational Interviewing training application used by [DEPARTMENT]
students. Students hold a practice conversation with an AI simulated patient,
and the application then produces a structured assessment of the student's
interviewing technique against a six-category rubric, together with a PDF
feedback report. It is a Python web application, currently hosted externally and
using a commercial hosted LLM API for inference.

We would like to move the inference workload, and a backend data store, onto
University infrastructure at MSI. The faculty Principal Investigator for the
project would be [PI NAME].

**What we would like to run**

Two vLLM servers on MSI GPUs, exposing an OpenAI-compatible API:

- Llama 3.1 8B, serving conversational turns and an evidence-extraction pass.
  This is latency-sensitive, since a student is waiting on each turn.
- Llama 3.3 70B, serving the scoring pass. One long call per completed session,
  roughly 1,000 to 1,500 output tokens.

Expected load is approximately [COHORT SIZE], concentrated around assignment
deadlines rather than spread evenly.

We would also like to store conversation transcripts, evaluation results and
application logs in MSI project storage. We estimate well under 1 TB per year,
as it is all text.

**Important point about the data**

We are not asking to store student records on MSI.

The student-facing web front end would remain outside MSI, on a
University-approved host, and would hold the only copy of any identifying
information. Before anything is sent to or stored on MSI, transcripts are
pseudonymised: student names are replaced with per-session aliases, an opaque
session identifier becomes the only key, and a pattern sweep removes UMN email
addresses and student ID numbers. The mapping from session identifier back to
student would exist only on the front end, never on MSI.

Graded PDF reports are archived in Box and would never be written to MSI.

**Questions**

Four questions determine whether this design is viable, and we would be grateful
for answers to these first.

1. The MSI User Agreement prohibits storing data protected by FERPA. Our data
   would be pseudonymised as described above before it reaches MSI, with no
   direct identifiers of any kind. Does data of this kind fall outside that
   prohibition, or is it still treated as FERPA-protected? If it remains
   restricted, is `/projects/regulated/` the appropriate location, and what is
   the approval process?

2. Is there a supported way for a web application running outside MSI to make
   sustained HTTPS requests to a vLLM server running in a Slurm job on a compute
   node, across a full semester? For example a reverse proxy, a published
   service endpoint, an API gateway, or a persistent tunnel. If there is no
   supported path, what would you recommend instead?

3. What is the supported mechanism for a process running outside MSI to write
   to Tier 1 project storage as data is produced? We are looking for something
   suited to frequent small writes rather than bulk transfer. If nothing
   suitable exists, would you recommend buffering externally and pushing to MSI
   on a schedule?

4. Is the Stratus Protected Data Cloud still offered? Its pages are no longer
   reachable and it does not appear in the new user documentation. If it has
   been retired, is there a replacement offering persistent virtual machines,
   and does any current MSI service support a long-running, publicly reachable
   web application?

The following are not urgent, but will shape the build.

5. What is the recommended approach for running vLLM with Llama 3.3 70B on MSI?
   Which partition and GPU allocation would you suggest, and do you recommend
   AWQ or FP8 quantisation to reduce the GPU count? Is there a reference job
   script we should start from?

6. What is the supported pattern for a service that must remain available across
   a 16-week semester, given the 37-day limit on `msilong` and 96 hours on
   `a100-4-long`? Is `scrontab` available, or a self-resubmitting job, or would
   Dedicated Computing be the better answer?

7. Can a job on one partition reach a service running on another over TCP,
   without an SSH tunnel? We may run the 8B and 70B models on different
   partitions.

8. Do compute nodes have outbound HTTPS access to `huggingface.co` for model
   weight downloads?

9. For well under 1 TB per year of text data, is the default Tier 1 project
   allocation sufficient, and what retention applies? We intend to use
   `/projects/standard/` rather than `/scratch.global/`, given the 30-day purge.

10. Is there a managed MySQL, MariaDB or PostgreSQL service? If not, we will use
    flat files on Tier 1 rather than run a database inside a Slurm job.

11. Where should API keys and service credentials be stored for a job running on
    MSI? We would prefer to avoid placing them on shared project storage.

12. What is the cadence and typical duration of maintenance windows, and how
    much notice is given? We need to schedule around them for a student-facing
    service.

**Where we are**

The application has already been refactored so that the inference provider is a
configuration setting rather than a code change, and so that all writable paths
are relocatable. In practice that means we can point it at an MSI-hosted
endpoint without further development work once the questions above are settled.

We are targeting [TERM], and would value an early indication on questions 1 to 4
even if the remainder takes longer.

We would be glad to meet if that would be easier than answering by email.

Thank you for your time.

Kind regards,

[YOUR NAME]
[DEPARTMENT]
University of Minnesota

---

## What each answer changes, for your own reference

Not part of the email.

| Answer | Consequence |
|---|---|
| 1 restricts pseudonymised data | Drop the MSI data store. Use MSI for inference only, and keep transcripts on the front end |
| 2 has no supported path | The hybrid design fails. Either move the front end onto MSI and accept VPN-only student access, or keep live inference on a commercial API and use MSI for batch work only |
| 3 has no supported path | Buffer on the front end and push to MSI on a schedule instead of writing per turn |
| 4 confirms a VM service exists | Prefer it over the hybrid split. It may resolve 2 and 3 at once |
| 6 offers no long-running pattern | Price Dedicated Computing, roughly 9,700 to 12,200 US dollars per year |
