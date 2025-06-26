#!/usr/bin/env python3
import os
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
import sys
import pyshcmd as pyshcmd
version = '20250626'
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging for the wrapper
def setup_logging(batch_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'run_batch_{batch_name}_{timestamp}.log')
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s: %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger(__name__)

# Global paths
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CONFIG_DIR = os.path.join(PARENT_DIR, 'config')

def read_batch_file(batch_file):
    batch_path = os.path.join(CONFIG_DIR, batch_file)
    logger = logging.getLogger(__name__)
    try:
        with open(batch_path, 'r') as f:
            csv_files = [line.strip() for line in f if line.strip()]
        if not csv_files:
            logger.error(f"No CSV files listed in {batch_path}")
            return []
        logger.info(f"Read {len(csv_files)} CSV files from {batch_path}: {csv_files}")
        return csv_files
    except OSError as e:
        logger.error(f"Error reading {batch_path}: {str(e)}")
        return []

def validate_csv_files(csv_files):
    logger = logging.getLogger(__name__)
    valid_csvs = []
    for csv_file in csv_files:
        csv_path = os.path.join(CONFIG_DIR, csv_file)
        if os.path.isfile(csv_path):
            valid_csvs.append(csv_file)
        else:
            logger.error(f"CSV file {csv_path} does not exist")
    return valid_csvs

def run_pyshcmd(csv_file, max_workers=16, verbose=True, save_json=False, save_txt=False):
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Starting execution for {csv_file}")
        
        args = SimpleNamespace(
            input=csv_file,
            outname=None,  # Use default (CSV stem)
            verbose=verbose,
            save_json=save_json,
            save_txt=save_txt,
            workers=max_workers
        )
        
        pyshcmd.main(args)
        
        logger.info(f"Completed execution for {csv_file}")
        return csv_file, 0, "", ""
    except Exception as e:
        logger.error(f"Error executing {csv_file}: {str(e)}")
        return csv_file, 1, "", str(e)

def main():
    parser = argparse.ArgumentParser(description="Run pyshcmd for CSV files listed in a batch file with optional JSON and text output")
    parser.add_argument("-b", "--batch", required=True, help="Batch file in config/ (e.g., run_batch1.txt)")
    parser.add_argument("-json", "--save-json", action="store_true", help="Save output to JSON file in output/ directory")
    parser.add_argument("-txt", "--save-txt", action="store_true", help="Save per-device output to text files in output/ directory")
    args = parser.parse_args()

    batch_name = Path(args.batch).stem
    logger = setup_logging(batch_name)

    csv_files = read_batch_file(args.batch)
    if not csv_files:
        return

    valid_csvs = validate_csv_files(csv_files)
    if not valid_csvs:
        logger.error("No valid CSV files to process")
        return

    logger.info(f"Processing {len(valid_csvs)} valid CSV files: {valid_csvs}")

    max_csv_workers = 8
    with ThreadPoolExecutor(max_workers=max_csv_workers) as executor:
        future_to_csv = {
            executor.submit(run_pyshcmd, csv_file, save_json=args.save_json, save_txt=args.save_txt): csv_file
            for csv_file in valid_csvs
        }
        for future in as_completed(future_to_csv):
            csv_file = future_to_csv[future]
            try:
                csv_file, returncode, _, stderr = future.result()
                if returncode == 0:
                    logger.info(f"Successfully processed {csv_file}")
                else:
                    logger.error(f"Failed to process {csv_file}: {stderr}")
            except Exception as e:
                logger.error(f"Exception for {csv_file}: {str(e)}")

if __name__ == "__main__":
    main()