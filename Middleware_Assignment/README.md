# Middleware Assignment 1 — Report

**Author:** marcusRB  
**Date:** 2026-05-04  
**Course:** Middleware / Distributed Systems

---

## 1. Problem Summary

The goal is to find all prime numbers that appear across an arbitrary number of
numeric ranges defined in `ranges_x.txt` files, organised under several `sample_*/`
directories.  Because the prime-counting program (`count_tot_primes.py`) is
computationally expensive, each range must be executed on a **SLURM cluster node**.
The orchestrator coordinates the whole pipeline and produces a single deduplicated,
sorted file `results/ALL_PRIMES.txt`.

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
│   ├── slurm_<arrayID>_<taskID>.out
│   └── slurm_merge_<jobID>.out
└── scripts/
    ├── count_tot_primes.py           ← provided
    ├── run_range.sh                  ← SLURM compute array script
    ├── merge_primes.sh               ← SLURM merge wrapper
    └── merge_primes.py              ← Python aggregation script
```

---


## 3. Architecture and Workflow

The pipeline runs in **two phases**, enforced by SLURM dependencies.

```
workflow_orchestrator.py
        │
        ├─ for each sample_*/ranges_x.txt
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
|---|---|
| Discovery | `glob.glob("data/sample_*/ranges_*.txt")` — works regardless of how many samples/ranges files exist |
| Array submission | For a file with *N* lines → `sbatch --array=1-N run_range.sh` |
| Dependency chain | Collects all job-IDs, then submits the merge job with `--dependency=afterok:J1:J2:…` |
| Logging | Timestamped entries written to `logs/ORCHEST_LOG.txt` via an open file handle flushed after each write |
| Portability | Accepts an optional `path_to_project` argument; falls back to `os.getcwd()` |

### 3.2 Compute Script — `scripts/run_range.sh`

A SLURM **array** job where `$SLURM_ARRAY_TASK_ID` selects the line to process:

```bash
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$RANGES_FILE")
BEGIN=$(echo "$LINE" | awk '{print $1}')
END=$(echo "$LINE"   | awk '{print $2}')
python count_tot_primes.py "$BEGIN" "$END" > "${OUTPUT_DIR}/range_${SLURM_ARRAY_TASK_ID}.txt"
```

- All tasks for one ranges file share the **same array job ID**, making monitoring easy (`squeue -j <arrayID>`).
- `stdout` and `stderr` go to `logs/slurm_<A>_<t>.out / .err` (SLURM `%A` = array ID, `%a` = task index).

### 3.3 Aggregation — `scripts/merge_primes.py`

```
glob results/**/*.txt   (recursive)
    → skip ALL_PRIMES.txt
    → skip lines starting with "TOTAL:"
    → collect integers into a Python set  (automatic deduplication)
sort(set) → write one prime per line → append "TOTAL: N"
```

Using a Python `set` guarantees **O(1)** insertion and automatic deduplication,
regardless of how many ranges overlap.

---

## 4. Efficiency Mechanisms

| Mechanism | Where used | Benefit |
|---|---|---|
| **SLURM job arrays** (`--array=1-N`) | `run_range.sh` | All ranges in a file share one job description; tasks are scheduled in parallel on available nodes |
| **SLURM dependency** (`--dependency=afterok:…`) | Merge job | Merge starts automatically and only if **all** compute tasks succeeded — no manual polling |
| **set-based deduplication** | `merge_primes.py` | O(1) insert; handles arbitrarily large overlap between ranges without extra sorting passes |
| **Parallel SLURM submission** | Orchestrator loop | All array jobs are submitted back-to-back before the orchestrator exits; the scheduler runs them concurrently |
| **Per-range-file sub-directories** | `results/sample/ranges_x/` | Avoids file-name collisions across samples; intermediate files can be cleaned independently |

---

## 5. How to Run

### 5.1 Prerequisites

```bash
# Ensure scripts are executable
chmod +x scripts/run_range.sh scripts/merge_primes.sh

# Verify Python is available on compute nodes (adjust shebang if needed)
python3 --version
```

### 5.2 Launching the Orchestrator

```bash
# Option A — from inside the project directory
cd /path/to/project
python workflow_orchestrator.py

# Option B — from any location
python workflow_orchestrator.py /path/to/project
```

### 5.3 Monitoring Jobs

```bash
# View queued / running jobs
squeue -u $USER

# Follow the orchestrator log in real time
tail -f logs/ORCHEST_LOG.txt

# Check a specific array job
squeue -j <arrayJobID>
```

### 5.4 Expected Output

```
results/ALL_PRIMES.txt
2
3
5
7
...
<last prime>
TOTAL: <N>
```