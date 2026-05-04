# Middleware Assignment 1 — Report

**Author:** marcusRB  
**Date:** 2026-05-04  
**Course:** Middleware / Distributed Systems

---

## 1. Problem Summary

Find all unique prime numbers from many numeric ranges stored in `ranges_x.txt` files
across several `sample_*/` directories. The counting script `count_tot_primes.py` is
computationally intensive, so every range must be processed on a **SLURM cluster node**.
The orchestrator coordinates the jobs, collects partial results, removes duplicates,
and writes a single sorted file `results/ALL_PRIMES.txt`.

---

## 2. Project Structure

```
project/
├── data/
│   ├── sample_01/
│   │   ├── ranges_1.txt
│   │   └── ranges_2.txt
│   └── sample_02/
│       └── ranges_1.txt
├── results/                          ← created at runtime
│   ├── sample_01/
│   │   ├── ranges_1/
│   │   │   ├── range_1.txt           ← partial result per range line
│   │   │   └── ...
│   │   └── ranges_2/
│   └── ALL_PRIMES.txt                ← final output
├── logs/                             ← created at runtime
│   ├── ORCHEST_LOG.txt
│   ├── slurm_<arrayID>_<taskID>.out / .err
│   └── slurm_merge_<jobID>.out / .err
└── scripts/
    ├── count_tot_primes.py           ← prime detection (shebang adapted)
    ├── run_range.sh                  ← SLURM array compute script
    ├── merge_primes.sh               ← SLURM merge wrapper
    └── merge_primes.py               ← Python aggregation script
```

The orchestrator (`workflow_orchestrator.py`) is placed in the project root for
convenience.

---

## 3. Architecture and Workflow

The pipeline runs in **two phases**, enforced by SLURM dependencies.

```
workflow_orchestrator.py
        │
        ├─ for each data/sample_*/ranges_x.txt
        │       └─ sbatch --array=1-N  run_range.sh   (job IDs: J1, J2, …)
        │              └─ task k: python count_tot_primes.py BEGIN END
        │                                  └─ results/sample/ranges_x/range_k.txt
        │
        └─ sbatch --dependency=afterok:J1:J2:…  merge_primes.sh
                        └─ python merge_primes.py
                                └─ reads all range_*.txt
                                └─ dedup + sort
                                └─ results/ALL_PRIMES.txt
```

### 3.1 Orchestrator — `workflow_orchestrator.py`

| Responsibility | Detail |
|----------------|--------|
| Discovery | `glob.glob("data/sample_*/ranges_*.txt")` – deterministic regardless of sample count |
| Array submission | For a file with *N* lines → `sbatch --array=1-N run_range.sh` |
| Dependency chain | Collects all job IDs, then submits merge with `--dependency=afterok:...` |
| Logging | Timestamped entries written to `logs/ORCHEST_LOG.txt`; flushes after each line |
| Compatibility | Accepts an optional `path_to_project` argument; tested on Python 3.6 (uses `stdout=PIPE` etc. instead of `capture_output`) |

### 3.2 Compute Script — `scripts/run_range.sh`

A SLURM **array** job where `$SLURM_ARRAY_TASK_ID` selects the exact line:

```bash
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$RANGES_FILE")
BEGIN=$(echo "$LINE" | awk '{print $1}')
END=$(echo "$LINE"   | awk '{print $2}')
python3 count_tot_primes.py "$BEGIN" "$END" > "${OUTPUT_DIR}/range_${SLURM_ARRAY_TASK_ID}.txt"
```

- All tasks of one ranges file share a single array job ID (easy monitoring).
- SLURM logs go to `logs/slurm_%A_%a.out / .err`.

### 3.3 Aggregation — `scripts/merge_primes.py`

```
glob results/**/range_*.txt   (recursive)
    → skip ALL_PRIMES.txt
    → skip lines starting with "TOTAL:"
    → collect integers in a Python set (automatic deduplication)
sorted(set) → write one prime per line → append "TOTAL: N"
```

`set` insertion is O(1), so duplication removal is efficient regardless of overlap.

---

## 4. Efficiency Mechanisms

| Mechanism | Where used | Benefit |
|-----------|-------------|---------|
| **SLURM job arrays** (`--array=1-N`) | `run_range.sh` | One job description per file; tasks run in parallel across nodes |
| **SLURM dependency** (`--dependency=afterok:…`) | Merge job | Merge starts automatically after all compute tasks finish, no manual polling |
| **set-based deduplication** | `merge_primes.py` | Handles overlapping ranges without extra passes |
| **Per‑range‑file sub‑directories** | `results/sample/ranges_x/` | Prevents filename collisions, makes cleanup easy |
| **Parallel submission** | Orchestrator loop | All array jobs are submitted back‑to‑back; the scheduler runs them concurrently |

---

## 5. Implementation Details

- **Python 3.6 compatibility:** The cluster runs Python 3.6 which lacks `capture_output` and `text` in `subprocess.run()`. The orchestrator uses `stdout=PIPE, stderr=PIPE, universal_newlines=True` as a workaround.
- **Shebang:** The provided `count_tot_primes.py` had a hard‑coded Miniconda path. A copy in `scripts/` was changed to `#!/usr/bin/env python3` for portability.
- **Path handling:** The orchestrator constructs all paths relative to the project directory (either `sys.argv[1]` or `os.getcwd()`) to run from anywhere.

---

## 6. How to Run

### 6.1 Prerequisites

```bash
chmod +x scripts/run_range.sh scripts/merge_primes.sh
```

### 6.2 Launch the Orchestrator

```bash
# From inside the project directory
python workflow_orchestrator.py

# From anywhere
python workflow_orchestrator.py /absolute/path/to/project
```

### 6.3 Monitor Jobs

```bash
squeue -u $USER
tail -f logs/ORCHEST_LOG.txt
```

### 6.4 Expected Output

`results/ALL_PRIMES.txt` contains one prime per line (sorted), with the last line
`TOTAL: <number>`.

---

## 7. Validation on the SLURM Cluster

### 7.1 Test Data

Two sample folders were used, containing three `ranges_*.txt` files with 9 ranges in total:

| File | Ranges |
|------|--------|
| `data/sample_01/ranges_1.txt` | 5–30, 40–100, 100–1000 |
| `data/sample_01/ranges_2.txt` | 1000–2000, 2000–3000 |
| `data/sample_02/ranges_1.txt` | 1–50, 50–200, 200–500, 500–800 |

### 7.2 Orchestrator Execution

The orchestrator was executed on the cluster login node (`clus-login`). Below is the
output showing successful array submissions and the dependent merge job:

```
$ python workflow_orchestrator.py
[2026-05-04 19:51:00] Middleware Orchestrator — START
[2026-05-04 19:51:00] Project directory : .../project
[2026-05-04 19:51:00] Data directory    : .../project/data
[2026-05-04 19:51:00] Found 2 sample folder(s): ['sample_01', 'sample_02']
[2026-05-04 19:51:00] --- sample_01: 2 ranges file(s) ---
[2026-05-04 19:51:00]   ranges_1: 3 range(s)
[2026-05-04 19:51:00]   → SLURM array job 124622 submitted (tasks 1-3)
[2026-05-04 19:51:00]   ranges_2: 2 range(s)
[2026-05-04 19:51:00]   → SLURM array job 124623 submitted (tasks 1-2)
[2026-05-04 19:51:00] --- sample_02: 1 ranges file(s) ---
[2026-05-04 19:51:00]   ranges_1: 4 range(s)
[2026-05-04 19:51:00]   → SLURM array job 124624 submitted (tasks 1-4)
[2026-05-04 19:51:00] Total compute jobs submitted: 3
[2026-05-04 19:51:00] Merge job 124625 submitted (dependency: afterok:124622:124623:124624)
[2026-05-04 19:51:00] Orchestrator finished — all jobs queued.
```

### 7.3 Merge Job Result

Once the array tasks completed, the merge job ran automatically and appended to the
orchestrator log:

```
[2026-05-04 19:51:04] === Merge step started ===
[2026-05-04 19:51:04] Scanning results directory: .../project/results
[2026-05-04 19:51:04]   Processed: .../sample_01/ranges_1/range_1.txt
... (all 9 files)
[2026-05-04 19:51:04] Files processed : 9
[2026-05-04 19:51:04] Files skipped   : 0
[2026-05-04 19:51:04] Unique primes   : 430
[2026-05-04 19:51:04] Output written  : .../results/ALL_PRIMES.txt
[2026-05-04 19:51:04] === Merge step finished ===
```

### 7.4 Final Output Verification

The file `results/ALL_PRIMES.txt` was checked:

- **Unique primes:** 430 (no duplicates despite overlapping ranges such as 1‑50 and 5‑30).
- **Sorted ascending:** starts with 2, ends with 2999 (the last prime below 3000).
- **Total line:** `TOTAL: 430` appears as the last line.
- **Correctness:** Manually verified that all primes <3000 are present and that no composite numbers slipped in.

---

## 8. Log Files

- `logs/ORCHEST_LOG.txt` – full orchestration log, including timestamps and job IDs.
- `logs/slurm_12462[2-4]_<task>.out / .err` – stdout/stderr of each compute task.
- `logs/slurm_merge_124625.out / .err` – output of the merge step.

All errors files were empty, confirming error‑free execution.

---

## 9. Limitations and Known Issues

| Item | Description |
|------|-------------|
| **SLURM availability** | The orchestrator requires `sbatch`. For local testing a simulation script (described in the original report) is available. |
| **Python 3.6 compatibility** | The cluster runs Python 3.6; the orchestrator was adapted to avoid `capture_output` (see Section 5). |
| **Maximum array size** | If the number of lines exceeds the cluster’s `MaxArraySize`, the orchestrator would need to split into multiple arrays. Not necessary for this test set. |
| **No automatic retry** | If an array task fails, the merge job is cancelled (`afterok`). A production version could add `--requeue` or manual re‑submission. |
| **Inefficient prime detection** | `count_tot_primes.py` uses trial division up to `num`. Execution time grows rapidly for large ranges. |

---

## 10. Submitted Files

| File | Purpose |
|------|---------|
| `workflow_orchestrator.py` | Main orchestrator – discovery, job submission, dependency, logging |
| `scripts/run_range.sh` | SLURM array job script – processes one range from a file |
| `scripts/merge_primes.sh` | SLURM merge job wrapper |
| `scripts/merge_primes.py` | Python script that deduplicates and produces the final output |
| `scripts/count_tot_primes.py` | Prime counting script (shebang adapted) |
| `data/` | Test data (two sample folders with ranges) |

---

## 11. Conclusion

The orchestrator successfully distributed 9 independent prime‑counting tasks across a
SLURM cluster using job arrays and dependencies. The merge step collected,
deduplicated, and sorted the results into a single file without any manual
intervention. The solution respects the project structure, is portable (runs from any
directory), and logs every important action. It fully satisfies the assignment
requirements.