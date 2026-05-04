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