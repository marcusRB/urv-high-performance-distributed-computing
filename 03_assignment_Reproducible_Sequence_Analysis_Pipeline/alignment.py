#!/usr/bin/env python3
import argparse
import logging
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

ACCESSION_REGEX = re.compile(r'^>(\S+)')
DNA_BASE_REGEX = re.compile(r'[ATGCatgc]')

def edit_distance_dp(pattern, text):
    """
    Compute edit distance (Levenshtein) using DP.
    Returns (distance, dp_matrix).
    """
    n, m = len(pattern), len(text)
    dp = [[0] * (m+1) for _ in range(n+1)]
    
    # Initialize first row and column
    logging.debug(f"Initializing DP matrix for pattern length {n} and text length {m}")
    for i in range(n+1):
        dp[i][0] = i
    for j in range(m+1):
        dp[0][j] = j

    # Fill matrix
    logging.debug(f"Computing DP matrix for pattern: {pattern} and text: {text}")
    for i in range(1, n+1):
        for j in range(1, m+1):
            if pattern[i-1] == text[j-1]:
                cost = 0
            else:
                cost = 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost  # match/substitution
            )
            logging.debug(f"dp[{i}][{j}] = {dp[i][j]} (cost: {cost})")
    return dp[n][m], dp

def traceback_cigar(dp, pattern, text):
    """
    Recover CIGAR string from DP matrix.
    Returns expanded CIGAR string (e.g., "MMXXMMIDIM").
    """
    i, j = len(pattern), len(text)
    cigar = []

    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (0 if pattern[i-1]==text[j-1] else 1):
            if pattern[i-1] == text[j-1]:
                cigar.append('M')
            else:
                cigar.append('X')
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
            cigar.append('D')
            i -= 1
        else:  # j > 0 and dp[i][j] == dp[i][j-1] + 1
            cigar.append('I')
            j -= 1
    return ''.join(reversed(cigar))


def parse_fasta_records(fasta_path):
    """Read FASTA records and keep only DNA bases, normalized to uppercase."""
    records = []

    with open(fasta_path, 'r', encoding='utf-8') as fasta_handle:
        current_accession = None
        current_sequence = []

        for raw_line in fasta_handle:
            line = raw_line.strip()
            if not line:
                continue

            if line.startswith('>'):
                if current_accession is not None:
                    records.append((current_accession, ''.join(current_sequence)))

                match = ACCESSION_REGEX.match(line)
                if not match:
                    raise ValueError(f'Invalid FASTA header: {line}')

                current_accession = match.group(1)
                current_sequence = []
            else:
                filtered_bases = ''.join(DNA_BASE_REGEX.findall(line)).upper()
                current_sequence.append(filtered_bases)

        if current_accession is not None:
            records.append((current_accession, ''.join(current_sequence)))

    return records


def print_dp_matrix(pattern, text, dp_matrix):
    """Print the complete DP matrix for the first sequence comparison."""
    print('DP matrix for the first sequence (rows=reference, cols=target):')
    print('     ' + '  '.join([' '] + list(text)))

    for row_index in range(len(pattern) + 1):
        row_label = pattern[row_index - 1] if row_index > 0 else ' '
        row_values = '  '.join(str(dp_matrix[row_index][column_index]) for column_index in range(len(text) + 1))
        print(f'{row_label}  {row_values}')


def build_parser():
    parser = argparse.ArgumentParser(
        description='Compute edit distances and expanded CIGAR strings for FASTA fragments.'
    )
    parser.add_argument('input_fasta', nargs='?', default='PM_50.fasta', help='Path to the input FASTA file')
    parser.add_argument('output_distances', nargs='?', default='distances.tsv', help='Path to the output distances TSV')
    parser.add_argument('output_alignments', nargs='?', default='alignments.tsv', help='Path to the output alignments TSV')
    return parser

def main():
    args = build_parser().parse_args()

    records = parse_fasta_records(args.input_fasta)
    if not records:
        raise ValueError('The input FASTA file does not contain any sequences.')

    logging.info('Loaded %s FASTA records from %s', len(records), args.input_fasta)

    ref_seq = records[0][1][:18]
    print(f"Reference sequence (first 18 nt of {records[0][0]}): {ref_seq}\n")

    first_seq_frag = records[0][1][:18]
    dist, dp_matrix = edit_distance_dp(ref_seq, first_seq_frag)
    print_dp_matrix(ref_seq, first_seq_frag, dp_matrix)
    print(f"\nEdit distance: {dist}\n")

    with open(args.output_distances, 'w', encoding='utf-8') as f_dist, open(args.output_alignments, 'w', encoding='utf-8') as f_align:
        f_dist.write("Accession\tDistance\n")
        f_align.write("Accession\tDistance\tCIGAR\n")

        for acc, seq in records:
            frag = seq[:18]
            dist, dp = edit_distance_dp(ref_seq, frag)
            cigar = traceback_cigar(dp, ref_seq, frag)
            f_dist.write(f"{acc}\t{dist}\n")
            f_align.write(f"{acc}\t{dist}\t{cigar}\n")

    logging.info('Wrote %s and %s', args.output_distances, args.output_alignments)

if __name__ == "__main__":
    main()