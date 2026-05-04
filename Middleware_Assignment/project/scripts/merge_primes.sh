#!/bin/bash
# scripts/merge_primes.sh
# Thin SLURM wrapper that triggers the Python aggregation script.
#
# Arguments (passed by the orchestrator via sbatch):
#   $1  RESULTS_DIR   — top-level results/ directory
#   $2  MERGE_SCRIPT  — path to merge_primes.py
#   $3  LOG_FILE      — path to ORCHEST_LOG.txt (for appending the merge entry)

#SBATCH --job-name=merge_primes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --time=00:30:00
#SBATCH --mem=2G

set -euo pipefail

RESULTS_DIR="$1"
MERGE_SCRIPT="$2"
LOG_FILE="$3"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Merge job started on $(hostname)"

python "$MERGE_SCRIPT" "$RESULTS_DIR" "$LOG_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Merge job finished."
