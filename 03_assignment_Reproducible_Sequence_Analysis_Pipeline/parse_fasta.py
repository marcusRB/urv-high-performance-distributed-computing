#!/usr/bin/env python3
import re
import logging
import time

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_fasta(fasta_file, output_tsv):
    """
    Parse FASTA file, extract accession and length using regex.
    """
    with open(fasta_file, 'r') as fin, open(output_tsv, 'w') as fout:
        fout.write("Accession\tLength\n")
        logger.info(f"Processing FASTA file: {fasta_file} \nOutput TSV: {output_tsv} \n")
        logger.info("Simulating processing time. Waiting 3 seconds...")
        time.sleep(3)  # Simulate processing time
        
        current_acc = None
        current_seq = []
        for line in fin:
            line = line.strip()
            if line.startswith('>'):
                # Save previous record
                if current_acc is not None:
                    seq_len = len(''.join(current_seq))
                    fout.write(f"{current_acc}\t{seq_len}\n")
                    logger.info(f"###--- Processed record: {current_acc} with length {seq_len} ---###")
                # Extract accession: first non‑whitespace after '>'
                match = re.match(r'^>(\S+)', line)
                if match:
                    current_acc = match.group(1)
                else:
                    current_acc = line[1:].split()[0]  # fallback
                current_seq = []
            else:
                current_seq.append(line)
        # Last record
        if current_acc is not None:
            seq_len = len(''.join(current_seq))
            fout.write(f"{current_acc}\t{seq_len}\n")
            logger.info(f"###--- Processed record: {current_acc} with length {seq_len} ---###\n")
if __name__ == "__main__":
    logger.info(f"###--- Starting to parse FASTA file: PM_50.fasta ---###")
    parse_fasta("PM_50.fasta", "sequences.tsv")
    logger.info(f"###--- Finished parsing FASTA file: PM_50.fasta ---###")
