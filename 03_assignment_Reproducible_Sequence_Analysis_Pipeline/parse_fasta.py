#!/usr/bin/env python3
import argparse
import re

DNA_BASE_REGEX = re.compile(r"[ATGCatgc]")

def parse_fasta(fasta_file, output_tsv):
    """Parse a FASTA file and write accession identifiers and lengths as TSV."""
    with open(fasta_file, 'r', encoding='utf-8') as fin, open(output_tsv, 'w', encoding='utf-8') as fout:
        fout.write("Accession\tLength\n")

        current_acc = None
        current_seq = []
        for line in fin:
            line = line.strip()
            if line.startswith('>'):
                if current_acc is not None:
                    seq_len = len(''.join(current_seq))
                    fout.write(f"{current_acc}\t{seq_len}\n")

                # The accession is the first non-whitespace token after '>'.
                match = re.match(r'^>(\S+)', line)
                if match:
                    current_acc = match.group(1)
                else:
                    current_acc = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(''.join(DNA_BASE_REGEX.findall(line)))

        if current_acc is not None:
            seq_len = len(''.join(current_seq))
            fout.write(f"{current_acc}\t{seq_len}\n")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Extract accession identifiers and sequence lengths from a FASTA file."
    )
    parser.add_argument("input_fasta", help="Path to the input FASTA file")
    parser.add_argument(
        "-o",
        "--output",
        default="sequences.tsv",
        help="Path to the output TSV file (default: sequences.tsv)",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    parse_fasta(args.input_fasta, args.output)
