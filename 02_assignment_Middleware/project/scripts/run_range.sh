#!/bin/bash
# scripts/run_range.sh
# SLURM array script — each task processes ONE line from a ranges file.
#
# Arguments (passed by the orchestrator via sbatch):
#   $1  RANGES_FILE   — path to the ranges_x.txt file
#   $2  OUTPUT_DIR    — directory to write the partial result
#   $3  PRIME_SCRIPT  — path to count_tot_primes.py

#SBATCH --job-name=count_primes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --mem=512M

set -euo pipefail

RANGES_FILE="$1"
OUTPUT_DIR="$2"
PRIME_SCRIPT="$3"

# ── Read the line that corresponds to this array task index ──────────
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" "$RANGES_FILE")
BEGIN=$(echo "$LINE" | awk '{print $1}')
END=$(echo "$LINE"   | awk '{print $2}')

OUTPUT_FILE="${OUTPUT_DIR}/range_${SLURM_ARRAY_TASK_ID}.txt"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task ${SLURM_ARRAY_TASK_ID}: " \
     "range ${BEGIN}–${END} → ${OUTPUT_FILE}"

# ── Run the prime counter ────────────────────────────────────────────
python "$PRIME_SCRIPT" "$BEGIN" "$END" > "$OUTPUT_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task ${SLURM_ARRAY_TASK_ID}: done."
