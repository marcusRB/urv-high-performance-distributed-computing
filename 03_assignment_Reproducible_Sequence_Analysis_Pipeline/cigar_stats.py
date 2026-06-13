#!/usr/bin/env python3
import argparse
import re
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def analyze_cigar(cigar):
    """Return counts of M, I, D, X using regex."""
    # Each operation is a single character in expanded CIGAR
    m_count = len(re.findall(r'M', cigar))
    i_count = len(re.findall(r'I', cigar))
    d_count = len(re.findall(r'D', cigar))
    x_count = len(re.findall(r'X', cigar))
    return m_count, i_count, d_count, x_count


def read_alignments(alignments_path):
    records = []

    with open(alignments_path, 'r', encoding='utf-8') as fin:
        next(fin)
        for line in fin:
            if not line.strip():
                continue
            accession, distance, cigar = line.strip().split('\t')
            records.append((accession, int(distance), cigar))

    return records


def read_distances(distances_path):
    distances = {}

    with open(distances_path, 'r', encoding='utf-8') as fin:
        next(fin)
        for line in fin:
            if not line.strip():
                continue
            accession, distance = line.strip().split('\t')
            distances[accession] = int(distance)

    return distances


def read_cigar_stats(cigar_stats_path):
    stats = {}

    with open(cigar_stats_path, 'r', encoding='utf-8') as fin:
        next(fin)
        for line in fin:
            if not line.strip():
                continue
            accession, matches, insertions, deletions, substitutions = line.strip().split('\t')
            stats[accession] = {
                'M': int(matches),
                'I': int(insertions),
                'D': int(deletions),
                'X': int(substitutions),
            }

    return stats


def write_report_section(handle, title, accession, distance, stats):
    handle.write(f'{title}:\n')
    handle.write(f'{accession}\n')
    handle.write(f'Distance: {distance}\n')
    handle.write(f"Matches: {stats['M']}\n")
    handle.write(f"Insertions: {stats['I']}\n")
    handle.write(f"Deletions: {stats['D']}\n")
    handle.write(f"Substitutions: {stats['X']}\n\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description='Compute CIGAR statistics and write the summary report.'
    )
    parser.add_argument('input_alignments', nargs='?', default='alignments.tsv', help='Path to alignments.tsv')
    parser.add_argument('input_distances', nargs='?', default='distances.tsv', help='Path to distances.tsv')
    parser.add_argument('output_cigar_stats', nargs='?', default='cigar_stats.tsv', help='Path to cigar_stats.tsv')
    parser.add_argument('output_report', nargs='?', default='report.txt', help='Path to report.txt')
    return parser

def main():
    args = build_parser().parse_args()

    records = read_alignments(args.input_alignments)
    if not records:
        raise ValueError('The alignments file does not contain any records.')

    logging.info('Read %s alignments from %s', len(records), args.input_alignments)

    logging.info('Writing CIGAR statistics to %s', args.output_cigar_stats)
    with open(args.output_cigar_stats, 'w', encoding='utf-8') as fout:
        fout.write("Accession\tM\tI\tD\tX\n")
        for acc, dist, cigar in records:
            m, i, d, x = analyze_cigar(cigar)
            fout.write(f"{acc}\t{m}\t{i}\t{d}\t{x}\n")
    logging.info('CIGAR analysis complete')

    distances = read_distances(args.input_distances)
    stats = read_cigar_stats(args.output_cigar_stats)

    if set(distances) != set(stats):
        raise ValueError('distances.tsv and cigar_stats.tsv do not contain the same accessions.')

    smallest_distance_accession = min(distances, key=distances.get)
    largest_distance_accession = max(distances, key=distances.get)
    largest_matches_accession = max(stats, key=lambda accession: stats[accession]['M'])

    logging.info('Writing summary report to %s', args.output_report)
    with open(args.output_report, 'w', encoding='utf-8') as rep:
        write_report_section(
            rep,
            'Sequence with smallest edit distance',
            smallest_distance_accession,
            distances[smallest_distance_accession],
            stats[smallest_distance_accession],
        )
        write_report_section(
            rep,
            'Sequence with largest edit distance',
            largest_distance_accession,
            distances[largest_distance_accession],
            stats[largest_distance_accession],
        )
        write_report_section(
            rep,
            'Sequence with largest number of matches',
            largest_matches_accession,
            distances[largest_matches_accession],
            stats[largest_matches_accession],
        )

    logging.info('Report written to %s', args.output_report)

if __name__ == "__main__":
    main()