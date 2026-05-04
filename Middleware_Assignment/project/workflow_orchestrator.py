#!/usr/bin/env python3
"""
workflow_orchestrator.py
Middleware Assignment 1 — SLURM-based prime number pipeline orchestrator.

Usage:
    python workflow_orchestrator.py                        # run from project dir
    python workflow_orchestrator.py /path/to/project       # run from anywhere
"""

import os
import sys
import subprocess
import glob
import datetime


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def get_project_dir() -> str:
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    return os.getcwd()


def log(msg: str, log_fh) -> None:
    """Write a timestamped line to stdout and to the open log file handle."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_fh.write(line + "\n")
    log_fh.flush()


def sbatch(cmd: str) -> str:
    """Run an sbatch command and return the job-id string."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"sbatch failed (exit {result.returncode}):\n"
            f"  stdout: {result.stdout.strip()}\n"
            f"  stderr: {result.stderr.strip()}"
        )
    # sbatch prints "Submitted batch job <id>"
    job_id = result.stdout.strip().split()[-1]
    return job_id


def read_non_empty_lines(path: str):
    with open(path) as fh:
        return [l.strip() for l in fh if l.strip()]


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main():
    project_dir = get_project_dir()
    data_dir    = os.path.join(project_dir, "data")
    results_dir = os.path.join(project_dir, "results")
    logs_dir    = os.path.join(project_dir, "logs")
    scripts_dir = os.path.join(project_dir, "scripts")

    for d in (results_dir, logs_dir):
        os.makedirs(d, exist_ok=True)

    log_path = os.path.join(logs_dir, "ORCHEST_LOG.txt")

    with open(log_path, "a") as log_fh:

        log("=" * 60, log_fh)
        log("Middleware Orchestrator — START", log_fh)
        log(f"Project directory : {project_dir}", log_fh)
        log(f"Data directory    : {data_dir}", log_fh)
        log(f"Results directory : {results_dir}", log_fh)
        log(f"Logs directory    : {logs_dir}", log_fh)
        log(f"Scripts directory : {scripts_dir}", log_fh)
        log("=" * 60, log_fh)

        # ── 1. Discover sample folders ────────────────────────────────
        sample_dirs = sorted(glob.glob(os.path.join(data_dir, "sample_*")))
        if not sample_dirs:
            log("ERROR: No sample_* directories found under data/. Aborting.", log_fh)
            sys.exit(1)

        log(f"Found {len(sample_dirs)} sample folder(s): "
            f"{[os.path.basename(s) for s in sample_dirs]}", log_fh)

        all_job_ids = []          # collect every compute job-id
        slurm_compute = os.path.join(scripts_dir, "run_range.sh")
        prime_script  = os.path.join(scripts_dir, "count_tot_primes.py")

        # ── 2. Submit one SLURM array job per ranges file ─────────────
        for sample_dir in sample_dirs:
            sample_name = os.path.basename(sample_dir)
            ranges_files = sorted(glob.glob(os.path.join(sample_dir, "ranges_*.txt")))

            log(f"--- {sample_name}: {len(ranges_files)} ranges file(s) ---", log_fh)

            sample_results = os.path.join(results_dir, sample_name)
            os.makedirs(sample_results, exist_ok=True)

            for ranges_file in ranges_files:
                rname = os.path.basename(ranges_file).replace(".txt", "")
                lines = read_non_empty_lines(ranges_file)
                n     = len(lines)

                if n == 0:
                    log(f"  SKIP {rname}: file is empty.", log_fh)
                    continue

                log(f"  {rname}: {n} range(s)", log_fh)

                # One sub-directory per ranges file to hold intermediate results
                out_dir = os.path.join(sample_results, rname)
                os.makedirs(out_dir, exist_ok=True)

                cmd = (
                    f"sbatch "
                    f"--array=1-{n} "
                    f"--output={logs_dir}/slurm_%A_%a.out "
                    f"--error={logs_dir}/slurm_%A_%a.err "
                    f"{slurm_compute} "
                    f"{ranges_file} {out_dir} {prime_script}"
                )

                job_id = sbatch(cmd)
                all_job_ids.append(job_id)
                log(f"  → SLURM array job {job_id} submitted "
                    f"(tasks 1-{n}, ranges file: {rname})", log_fh)

        if not all_job_ids:
            log("No jobs submitted — nothing to do. Aborting.", log_fh)
            sys.exit(1)

        log(f"Total compute jobs submitted: {len(all_job_ids)} "
            f"({', '.join(all_job_ids)})", log_fh)

        # ── 3. Submit merge job — runs only when ALL compute jobs succeed ──
        dependency = "afterok:" + ":".join(all_job_ids)
        slurm_merge  = os.path.join(scripts_dir, "merge_primes.sh")
        merge_script = os.path.join(scripts_dir, "merge_primes.py")

        cmd = (
            f"sbatch "
            f"--dependency={dependency} "
            f"--output={logs_dir}/slurm_merge_%j.out "
            f"--error={logs_dir}/slurm_merge_%j.err "
            f"{slurm_merge} "
            f"{results_dir} {merge_script} {log_path}"
        )

        merge_id = sbatch(cmd)
        log(f"Merge job {merge_id} submitted "
            f"(dependency: {dependency})", log_fh)

        log("=" * 60, log_fh)
        log("Orchestrator finished — all jobs queued. "
            f"Final output: {os.path.join(results_dir, 'ALL_PRIMES.txt')}", log_fh)
        log("=" * 60, log_fh)


if __name__ == "__main__":
    main()
