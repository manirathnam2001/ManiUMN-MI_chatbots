# Migrating the MI Chatbots to UMN / Minnesota Supercomputing Institute (MSI)

Research date: 2026-07-29
Primary sources: <https://msi.umn.edu/consulting-and-research/ai-resources-msi>, <https://userdocs.msi.umn.edu/>

---

## 1. Bottom line first

MSI is an **excellent fit for the AI/compute half** of this application and a **poor fit, as currently
offered, for the "public web app" half.**

| Need | MSI verdict |
|---|---|
| Run Llama 3.1 8B + Llama 3.3 70B inference (replace Groq) | **Strong yes**: A100/H100/L40S + vLLM/Ollama are supported |
| Sentence-transformers + FAISS RAG embeddings | **Strong yes**: GPU or CPU, trivially supported |
| Batch/offline evaluation, rubric re-scoring, test suites | **Strong yes**: Slurm, 96h to 37day partitions |
| Bulk storage of transcripts, PDFs, rubrics, models | **Strong yes**: Tier 1 + Tier 2 (S3) |
| Free expert consulting + GenAI community | **Strong yes** |
| **Persistent, publicly reachable Streamlit service** | **No supported product.** MSI requires UMN network/VPN; no VM/cloud offering is currently advertised |
| **Storing FERPA-protected student records** | **Explicitly prohibited by the MSI User Agreement** |

The two red rows are hard constraints, not tuning problems. They shape the whole migration, so they are
covered in §5 before any architecture is proposed.

---

## 2. What this application actually requires

Inventory taken from `requirements.txt`, `config.json`, `mi_session.py`, `mi_evaluation.py`,
`email_utils.py`, `secret_code_portal.py`.

### Compute & AI
- **Chat model:** `llama-3.1-8b-instant` via Groq (`mi_session.py:98`)
- **Evaluator model:** `llama-3.3-70b-versatile` via Groq (`mi_session.py:99`, `mi_evaluation.py:260`)
- **Embeddings/RAG:** `sentence-transformers` + `faiss-cpu` over `*_rubrics/` corpora
- **Torch:** `torch>=2.5.1` (CPU today, pulled in by sentence-transformers)
- **Python:** 3.10 (`runtime.txt`)

### Runtime shape
- **Long-lived HTTP service**: Streamlit, multi-page (`pages/HPV.py`, `OHI.py`, `Perio.py`, `Tobacco.py`)
- **Concurrent interactive users**: dental students in a course, session state per user
- **Must stay up across a semester**, not for a 24-hour job window

### Outbound network dependencies (all currently required)
| Dependency | Endpoint | Purpose |
|---|---|---|
| Groq | `api.groq.com` | LLM inference |
| Gmail SMTP | `smtp.gmail.com:587` | Feedback delivery |
| Box inbound email | `*.u.box.com` | PDF archiving (4 course mailboxes) |
| Google Sheets | `spreadsheets.google.com`, `oauth2.googleapis.com` | Secret-code portal |
| gTTS | Google Translate TTS | Speech fallback |
| HuggingFace | `huggingface.co` | Model weight download at first run |

### Data sensitivity: the critical one
The app generates named per-student MI performance evaluations, transcripts, and PDF score reports, and
emails them to course Box folders. Under U.S. law that is a **student educational record → FERPA**.

### Persistence
- `database/mi_sessions.sql` schema
- `SMTP logs/`, `git_logs/` on local disk
- Google Sheets as an external system of record

---

## 3. Complete MSI capability inventory

### 3.1 Clusters and compute

**Agate** is the current production cluster (Mesabi retired June 2024). Login nodes `ahl0[1-4]`;
compute nodes `acn*`, `aga*`, `cn*`, `n*`. **Login nodes kill any process over the heavy-compute
threshold after 15 minutes**: never run the app there.

Per-user global limits: 5,000 concurrent jobs, 5,000 submissions/hour, job arrays to 100,001,
**1 job at a time** on `interactive` and `interactive-gpu`.

#### Shared partitions (the full menu)

| Partition | Cores | Memory | GPU | Max walltime | Max nodes | Relevance here |
|---|---|---|---|---|---|---|
| `msismall` | 128 | 248 to 755 GB | None | **96 h** | 1 | Batch eval jobs |
| `msilarge` | 128 | 248 to 755 GB | None | 24 h | 32 | Parallel sweeps |
| `msibigmem` | 128 | 1995 GB | None | 24 h | 1 | Large index builds |
| `msigpu` | 24 to 128 | 374 to 1002 GB | V100 / A100 / H100 | 24 h | 4 | 70B inference |
| **`msilong`** | 32 | 128 GB | None | **37 days** | unlimited | **Long-running CPU service** |
| `interactive` | 128 | 499 GB | None | 24 h | 2 | Dev / debugging |
| `interactive-gpu` | 64 to 128 | 499 to 755 GB | A40 / L40S | 24 h | 1 | Interactive GPU dev |
| **`interactive-long`** | 2 | 32 GB | None | **37 days** | 1 | **Long-running front end** |
| `preempt` | 128 | 248 to 755 GB | None | 24 h | 1 | Free-tier, killable |
| `preempt-gpu` | 64 to 128 | 499 to 755 GB | A40 / L40S | 24 h | 1 | Free-tier GPU, killable |
| `a100-4-long` | 128 | 499 GB | 4× A100 | **96 h** | 1 | Ticket required |
| `a100-8-long` | 128 | 499 GB | 8× A100 | **96 h** | 1 | Ticket required |
| `a100-4-profile` | 64 | 512 GB | 4× A100 | 24 h | 1 | Profiling |

`msilong` (37 days, 32 cores, 128 GB) and `interactive-long` (37 days, 2 cores, 32 GB) are the only
partitions that can span most of a semester. Note `interactive-long` is 2 cores: enough for Streamlit
serving, not for local model inference.

#### GPU hardware available for AI

| GPU | VRAM | Host cores | Walltime | Max nodes | Fits our models? |
|---|---|---|---|---|---|
| **H100** | 80 GB | 128 | 24 h | 4 | Llama 3.3 70B on 2 to 4 GPUs |
| **A100** | 40 GB | 64 to 128 | 24 to 96 h | 1 to 4 | 70B on 4× (AWQ/FP8 helps) |
| **L40S** | 48 GB | 128 | 24 h | 2 | 8B easily; 70B quantized |
| **A40** | 48 GB | 128 | 24 h | 1 | 8B easily |
| **V100** | 32 GB | 24 | 24 h | 1 | 8B only |

**Llama 3.1 8B fits comfortably on a single A40 or L40S.** Llama 3.3 70B needs 4× A100 or 2 to 4× H100
at bf16, or fewer GPUs with AWQ/GPTQ/FP8 quantization.

### 3.2 AI/ML software stack (all pre-supported)

- **Generative AI / LLM:** **Ollama, vLLM, ChromaDB, FlashAttention, LangChain, LlamaIndex,
  HuggingFace, rollama**: MSI lists these explicitly on its AI Resources page
- **Deep learning:** PyTorch, TensorFlow, Keras, Caffe, MATLAB Deep Learning Toolbox
- **CUDA stack:** CUDA, CUDA SDK, cuDNN
- **Python:** Python 3.x (primary support), conda / mamba / anaconda (secondary support)
- **Containers:** Apptainer (formerly Singularity) is supported, including **custom Jupyter kernels
  built from Apptainer images**: the cleanest way to reproduce this app's exact Python 3.10 env
- **Bio/vision (not needed here):** AlphaFold 3, Evo2, OpenCV, Cellpose, Qiskit

Two facts worth noting: **vLLM is already on MSI's supported list**, and **`sentence-transformers`
and `faiss` are not**: those go in a conda env or Apptainer image.

### 3.3 Storage

| Tier | Path | Default quota | Snapshots | Backups |
|---|---|---|---|---|
| Home | `/users/[0-9]/$USER` | 200 GB / 1M files | 6 daily + 4 weekly | disaster_recovery only |
| Tier 1 project | `/projects/standard/PROJECT` | 150 GB / 5M files (to 20 TB on request) | yes | tape, 60 days |
| Tier 1 regulated | `/projects/regulated/PROJECT` | as allocated | yes | **no tape backups** (as of Dec 2025) |
| Global scratch | `/scratch.global/$USER` | 40 TB / 10 to 13.2M files | none | none |
| Tier 2 (S3/Ceph) | S3 endpoint | 120 TB per PI, 5 GB per member | **none** | **none** |

**Scratch purge is now enforced: files are deleted 30 days after creation, with a 40 TB per-user
quota on top of the group quota** (June 2026 bulletin). Never put session data or the SQLite/SQL
store on scratch.

Tier 2 is S3-compatible (`s3cmd`, `rclone`, Globus): a natural home for the archive of generated
PDFs, replacing or supplementing the Box email flow. Note the total absence of backups on Tier 2.

Pricing (FY27): Tier 1 $106.82/TB/yr internal; Tier 2 $28.05/TB/yr internal.

### 3.4 Interactive access

- **Open OnDemand** at `https://ondemand.msi.umn.edu/` is the preferred route. Apps: Desktop, Jupyter
  (Python 2/3, R, and now Qiskit), RStudio, IGV, COMSOL, IDL, ANSYS. Includes a file browser and
  in-browser shell (`/pun/sys/shell/ssh/<node>.agate.msi.umn.edu`). Supports group/project selection.
- **`srun`** interactive sessions, e.g. `srun -N 1 -n 1 -t 4:00:00 -p interactive --tmp 20gb --pty bash`
- **Citrix** for Windows-only software (not relevant here)
- **Retired:** NICE, NX/NoMachine: do not plan around them
- **Access requirement: UMN campus network (eduroam) or UMN VPN. Non-negotiable for OOD and SSH.**

### 3.5 Consulting, training, and community: genuinely valuable here

- **Consulting**: `/consulting-and-research/consulting`. Listed rate $250/hr, but MSI staff
  consultation for supported research groups is normally included; confirm scope with them.
- **Portals and Databases group**: MSI states it "will develop and host portals and databases
  specific to research projects supported by MSI consultants," historically deploying them in an
  OpenStack environment (Galaxy, Galaxy-P, SMRT portal, NCFP, DMRF). **This is the single most
  promising path for hosting a Streamlit app at MSI** and it is a conversation, not a self-service
  product. Start here.
- **GenAI+ Interest Group**: `/consulting-and-research/gen-ai-interest-group`. Zoom community,
  monthly newsletter, speakers (Dr. Zirui Liu, Dr. Guichuan Yu). Join by emailing Ham Lam.
- **Tutorials**: "Introduction to Deep Learning," and **"Deep Learning II at MSI," which is
  specifically about running an LLM for RAG on Agate**: directly on-point for this app.
- **Proposal support**: `/consulting-and-research/proposal-support`, if this becomes grant-funded.
- **ALCF Lighthouse Initiative**: MSI-brokered access to Argonne's exascale/AI hardware for
  experimental work.
- **Help Desk**: 599 Walter Library, 117 Pleasant St SE; 612-626-0802; `/helpdesk`.

### 3.6 Accounts

- A **UMN faculty PI** must own the project; the PI or a Group Admin then adds members via
  **MyMSI** (`https://mymsi.msi.umn.edu/`).
- Non-UMN collaborators need a **POI** designation.
- **Class accounts** exist (faculty request ≥2 weeks before term, 3 TB shared group storage) but
  **auto-close two weeks after the semester ends and the data is unrecoverable.** Usable for
  student *logins*, unusable as the home of a persistent service or of session records.
- Authentication is password + **Duo**; SSH keys are recommended to reduce prompts.

---

## 4. Component-by-component migration map

| Current | MSI target | Confidence |
|---|---|---|
| Groq `llama-3.1-8b-instant` | **vLLM** serving Llama 3.1 8B on 1× A40/L40S, OpenAI-compatible endpoint | High |
| Groq `llama-3.3-70b-versatile` | **vLLM** serving Llama 3.3 70B on 4× A100 (`a100-4-long`, 96 h) or 2 to 4× H100; quantized to cut GPU count | High |
| `sentence-transformers` + `faiss-cpu` | Same packages in conda/Apptainer; pre-download weights to Tier 1; optionally `faiss-gpu` | High |
| `torch>=2.5.1` | MSI PyTorch module, or pinned in the Apptainer image | High |
| Python 3.10 env | **Apptainer image** built from `requirements.txt`: best reproducibility | High |
| Rubric corpora (`*_rubrics/`) | Tier 1 `/projects/standard/<project>/` | High |
| Generated PDFs archive | Tier 2 S3 via `s3cmd`/`rclone` | High |
| `database/mi_sessions.sql` | No managed DB service found. Options: SQLite on Tier 1, or self-run Postgres/MySQL inside the service job, or ask the Portals & Databases group | Medium: needs MSI input |
| Streamlit HTTP service | **No supported product.** See §5.2 and §6 | **Low** |
| Gmail SMTP → Box | Needs outbound SMTP from compute nodes; also consider UMN-sanctioned mail relay instead of a personal Gmail app password | **Unconfirmed** |
| Google Sheets secret-code portal | Needs outbound HTTPS from compute nodes | **Unconfirmed** |
| gTTS speech fallback | Needs outbound HTTPS; alternatively run a local TTS model on MSI GPUs | **Unconfirmed** |

### The headline win: dropping Groq

Both production models are **open-weight Llama models that MSI can host locally.** Standing up vLLM
with an OpenAI-compatible API means the change in application code is roughly a base-URL and API-key
swap: the `groq` client is already OpenAI-shaped. That would:

- eliminate the external Groq dependency and its per-token cost
- keep every student transcript inside UMN infrastructure (a real privacy improvement)
- remove a third-party data-processing relationship from the FERPA analysis
- give control over model version pinning, which currently drifts with Groq's deprecations

The cost is operational: a vLLM server must be kept running, and it lives under a 24 to 96 hour
walltime ceiling unless dedicated hardware is leased.

---

## 5. The three real blockers

### 5.1 FERPA: the MSI User Agreement forbids this data class

MSI's User Agreement states users will **not** store data protected by HIPAA, FISMA, **FERPA**, ITAR,
or EAR. MSI states plainly that its systems are not HIPAA-compliant and that data should be
de-identified before transfer. Enforcement is explicit: **policy breach results in immediate account
closure and removal of the non-compliant data.** The PI carries the compliance responsibility.

Named MI evaluations of enrolled students are educational records. As written, storing them on MSI
appears to violate the agreement.

Three ways forward, in order of preference:

1. **De-identify.** Keep only opaque session IDs on MSI; hold the ID→student mapping in a
   UMN-approved FERPA-appropriate system. MSI then only ever sees pseudonymous transcripts. This is
   the cleanest fit with MSI policy and preserves all functionality.
2. **Use `/projects/regulated/`** under an explicit agreement with MSI. Note this space has no tape
   backups as of December 2025, and FERPA is not listed among the data types MSI accommodates.
3. **Split the system**: identified data stays off MSI entirely (§6, Option A).

**This must be settled with the MSI Help Desk and the UMN privacy/compliance office before any
migration work starts.** Do not treat it as a detail to sort out later.

### 5.2 No public-facing hosting product

- OOD and SSH both require **UMN campus network or VPN**.
- The Stratus Protected Data Cloud: the OpenStack IaaS that historically supported long-running
  (>30 day) VMs with persistent volumes and protected data: **is no longer advertised on
  `/computing`, its pages now return "Access denied," and it has no section in the new
  `userdocs.msi.umn.edu`.** Treat Stratus as retired or restricted **until MSI confirms otherwise**;
  that confirmation is question #1 for the Help Desk, because if Stratus (or a successor) is
  available, it is the single best fit for this application.
- MSI's Portals and Databases service does host web portals, but as a consultant-mediated,
  project-specific arrangement.

If students must reach the chatbot from off-campus without a VPN, **MSI as currently offered cannot
serve the front end.**

### 5.3 Walltime vs. semester

Slurm's longest shared partitions are 37 days (`msilong`, `interactive-long`) and 96 hours for GPU
(`a100-*-long`). A semester is ~16 weeks. Any Slurm-hosted service therefore needs either:

- a **restart/checkpoint strategy** (chained jobs, a supervisor, health-check-driven resubmission), with
  session state externalized to Tier 1 so restarts are non-destructive; or
- **Dedicated Computing**: leased hardware, no shared-partition walltime pressure.

Dedicated Computing pricing, FY27 annual:

| Option | Spec | Cost/yr |
|---|---|---|
| 1 | 128 AMD Milan cores, 512 GB | $3,034.04 |
| 2 | 128 Milan cores, 2048 GB | $4,483.94 |
| 3 | 64 Milan cores, 512 GB, **4× A100** | $9,723.22 |
| 5 | 128 Milan cores, 512 GB, **8× A40** | $10,511.89 |
| 6 | 128 AMD Genoa cores, 384 GB | $4,911.91 |
| 7 | 128 Genoa cores, 768 GB | $5,306.49 |
| 9 | 128 Genoa cores, 768 GB, **4× L40S** | $12,219.17 |
| 4 | 128 Milan, 1024 GB, 8× A100 | $16,722.71 (unavailable) |
| 8 | 128 Genoa, 768 GB, 4× H100 | $29,509.39 (unavailable) |

**Option 9 (4× L40S, $12,219/yr)** or **Option 3 (4× A100, $9,723/yr)** would host both models plus
the app with room to spare, and removes the walltime problem entirely.

---

## 6. Three candidate architectures

### Option A: Hybrid (recommended starting point)

```
Students ──HTTPS──> Streamlit front end          MSI Agate
                    (UMN-approved web host,      ┌──────────────────────────┐
                     public, FERPA-appropriate)  │ vLLM: Llama 3.1 8B       │
                          │                      │ vLLM: Llama 3.3 70B      │
                          └───internal HTTPS────> │ FAISS/embeddings         │
                                                 │ Tier 1: rubrics, indexes │
                                                 │ Tier 2: PDF archive      │
                                                 └──────────────────────────┘
```

Front end stays on a platform designed to be public and to hold student records; MSI does the AI
heavy lifting on de-identified session payloads. Groq is eliminated. Nothing about the student
experience changes.

**Pros:** works within every MSI constraint today; largest cost saving; strongest privacy story.
**Cons:** two environments to operate; needs a stable MSI-side endpoint, so still bumps into §5.3.

### Option B: All-MSI, VPN-only

Streamlit on `interactive-long` or `msilong`, vLLM on a GPU partition, reached through OOD or an SSH
tunnel. **Only acceptable if every student is on UMN network/VPN and MSI clears the data question.**
Simplest architecture, most restrictive access. Good for a pilot with a small cohort.

### Option C: Dedicated Computing

Lease Option 9 or Option 3. No walltime ceiling, predictable performance, room for both models. Still
does **not** by itself solve public reachability (§5.2) or FERPA (§5.1): confirm both with MSI before
committing a five-figure annual spend.

---

## 7. Questions for the MSI Help Desk: send these first

Nothing should be built before these are answered. Help Desk: `/helpdesk` · 612-626-0802 ·
599 Walter Library.

1. **Is Stratus (or any successor VM/cloud/OpenStack service) still available?** If yes: floating/public
   IPs, GPU flavors, subscription cost, and whether a service may be exposed off-VPN.
2. **Can MSI host a persistent, student-facing Streamlit application**: via the Portals and Databases
   group or otherwise? What is the intake process?
3. **Can any MSI service be reached from off-campus without a UMN VPN?**
4. **FERPA:** given named student MI evaluations, what is the required posture? Is `/projects/regulated/`
   applicable, or is de-identification mandatory?
5. **Do compute nodes have outbound internet access?** Specifically HTTPS to `huggingface.co` and
   Google APIs, and SMTP on port 587. Is there a proxy? *(This determines whether the Box email flow,
   the Google Sheets portal, and gTTS survive the move at all.)*
6. **Longest supported walltime for a service-style job**, and MSI's recommended pattern for a service
   that must survive a full semester across maintenance windows.
7. **Managed database?** Any MySQL/MariaDB/PostgreSQL offering, or must we self-host in-job?
8. **How do we get an approved vLLM/Ollama setup** for Llama 3.3 70B: which partition, which
   quantization, is there a reference recipe?
9. **Maintenance windows**: cadence and duration, since they will interrupt any hosted service.
10. **Secrets management**: where should API keys and SMTP credentials live? (`config.json` currently
    has an empty `smtp_app_password` field; `.streamlit/secrets.toml` is not appropriate on shared
    storage.)

Also worth doing in parallel, at no cost: **join the GenAI+ Interest Group** (email Ham Lam), and
**register for the "Deep Learning II at MSI" tutorial**: it covers running an LLM for RAG on Agate,
which is exactly the vLLM + FAISS piece of this migration.

---

## 8. Suggested sequence

**Phase 0: Clear the blockers (do first, no code)**
Get a faculty PI to own an MSI project; submit the §7 questions; get a written answer on FERPA.

**Phase 1: Prove the AI half**
Request an interactive GPU session. Build an Apptainer image from `requirements.txt`. Stand up vLLM
with Llama 3.1 8B. Point `mi_session.py` at it via base-URL override. Verify persona behavior and
`mi_evaluation.py` strict-JSON output are unchanged. Then repeat for 70B on `a100-4-long`.
*Success criterion: `tests/` and `test_evaluation.py` pass against MSI-hosted models.*

**Phase 2: Move data and storage**
Rubrics and FAISS indexes to Tier 1. PDF archive to Tier 2 S3. Decide the DB story. Confirm the
outbound-network answers and adjust the email/Sheets/TTS paths accordingly.

**Phase 3: Decide the front end**
Based on the Help Desk answers, commit to Option A, B, or C. Only now touch deployment.

**Phase 4: Cut over**
Run MSI and the current environment in parallel for one course cycle before decommissioning anything.

---

## 9. Sources

- [AI Resources at MSI](https://msi.umn.edu/consulting-and-research/ai-resources-msi)
- [MSI User Documentation (userdocs)](https://userdocs.msi.umn.edu/)
- [Compute Need to Know](https://userdocs.msi.umn.edu/compute/cluster_info.html)
- [Shared Partitions](https://userdocs.msi.umn.edu/compute/shared_partitions.html)
- [Interactive HPC](https://userdocs.msi.umn.edu/compute/interactive_compute.html)
- [Open OnDemand Support](https://userdocs.msi.umn.edu/compute/open-ondemand-support.html)
- [Connecting to Compute](https://userdocs.msi.umn.edu/connect/connect_compute.html)
- [File Storage](https://userdocs.msi.umn.edu/storage/storage.html)
- [Available Software](https://userdocs.msi.umn.edu/software/package_docs/index.html)
- [Our Services](https://msi.umn.edu/about-msi-services)
- [Portals and Databases](https://msi.umn.edu/about-msi-services/portals-and-databases)
- [Service Catalog](https://msi.umn.edu/about-msi-services/service-catalog)
- [Computing](https://msi.umn.edu/computing)
- [Interactive (Real-Time) Computing](https://msi.umn.edu/computing/interactive-real-time-computing)
- [Getting Started and Access](https://msi.umn.edu/getting-started/getting-started-and-access)
- [Applying for Class Accounts](https://msi.umn.edu/getting-started/applying-for-class-accounts)
- [MSI User Agreement](https://msi.umn.edu/about-msi/policies/msi-user-agreement)
- [Data Retention and Protection](https://msi.umn.edu/about-msi/policies/data-retention-and-protection)
- [GenAI+ Interest Group](https://msi.umn.edu/consulting-and-research/gen-ai-interest-group)
- [Deep Learning II at MSI](https://msi.umn.edu/tutorials/deep-learning-ii-msi)
- [Users Bulletin: June 2026](https://msi.umn.edu/getting-started/help/users-bulletin/users-bulletin/june-2026-bulletin)
- [Stratus Protected Data Cloud (currently access-restricted)](https://msi.umn.edu/about-msi-services/stratus-protected-data-cloud)
- [MyMSI](https://mymsi.msi.umn.edu/) · [Open OnDemand](https://ondemand.msi.umn.edu/) · [Help Desk](https://msi.umn.edu/helpdesk)
