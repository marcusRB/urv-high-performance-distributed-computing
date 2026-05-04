#!/usr/bin/env python3
"""
scripts/merge_primes.py
Aggregation step (run after all SLURM compute tasks finish).

- Walks results/ recursively for every partial *.txt file.
- Collects all integer prime values, ignoring "TOTAL:" lines.
- Deduplicates and sorts.
- Writes results/ALL_PRIMES.txt with one prime per line + final TOTAL.
- Appends a summary entry to ORCHEST_LOG.txt.

Usage:
    python merge_primes.py <results_dir> <log_file>
"""

import os
import sys
import glob
import datetime


def timestamp() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_log(log_file: str, msg: str) -> None:
    line = f"[{timestamp()}] {msg}"
    print(line)
    with open(log_file, "a") as fh:
        fh.write(line + "\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: merge_primes.py <results_dir> <log_file>")
        sys.exit(1)

    results_dir = sys.argv[1]
    log_file    = sys.argv[2]

    append_log(log_file, "=== Merge step started ===")
    append_log(log_file, f"Scanning results directory: {results_dir}")

    primes: set[int] = set()
    files_processed  = 0
    files_skipped    = 0

    # Recursively find all partial result files (exclude ALL_PRIMES.txt itself)
    pattern = os.path.join(results_dir, "**", "*.txt")
    for txt_file in sorted(glob.glob(pattern, recursive=True)):
        if os.path.basename(txt_file) == "ALL_PRIMES.txt":
            continue

        files_processed += 1
        try:
            with open(txt_file) as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.upper().startswith("TOTAL:"):
                        continue
                    try:
                        primes.add(int(line))
                    except ValueError:
                        pass  # ignore any non-integer lines
            append_log(log_file, f"  Processed: {txt_file}")
        except OSError as exc:
            files_skipped += 1
            append_log(log_file, f"  SKIP (error): {txt_file} — {exc}")

    sorted_primes = sorted(primes)
    total         = len(sorted_primes)

    output_path = os.path.join(results_dir, "ALL_PRIMES.txt")
    with open(output_path, "w") as fh:
        for p in sorted_primes:
            fh.write(f"{p}\n")
        fh.write(f"TOTAL: {total}\n")

    append_log(log_file, f"Files processed : {files_processed}")
    append_log(log_file, f"Files skipped   : {files_skipped}")
    append_log(log_file, f"Unique primes   : {total}")
    append_log(log_file, f"Output written  : {output_path}")
    append_log(log_file, "=== Merge step finished ===")


if __name__ == "__main__":
    main()
