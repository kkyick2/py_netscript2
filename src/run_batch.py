#!/usr/bin/env python3
import os
import logging
import logging.config
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from types import SimpleNamespace
import sys
import json
import pyshcmd as pyshcmd
version = '20250627'
# Fixed --output-structure: option1 (timestamp/name), option2 (name_timestamp); removed run_batch_mp.py; added --verbose; aligned setup_logging with pyshcmd.py using JSON config (20250627_1508)

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Configure logging using JSON configuration
def setup_logging(verbose=False):
    log_configs = {
        "dev": "logging.dev.json",
        "prod": "logging.prod.json"
    }
    log_name = Path(os.path.basename(__file__)).stem
    log_config = log_configs.get('dev', "logging.dev.json")
    log_config_path = os.path.join(PARENT_DIR, CONFIG_DIR, log_config)
    log_file_path = os.path.join(PARENT_DIR, LOG_DIR, f'{log_name}_{DATETIME}.log')
    os.makedirs(LOG_DIR, exist_ok=True)

    with open(log_config_path, 'r') as f:
        config = json.load(f)
    
    for handler in config['handlers'].values():
        if handler['class'] == 'logging.FileHandler':
            handler['filename'] = log_file_path

    if verbose:
        config['handlers']['console']['level'] = 'DEBUG'

    logging.config.dictConfig(config)
    return logging.getLogger(__name__)

# Global paths
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CONFIG_DIR = os.path.join(PARENT_DIR, 'config')
LOG_DIR = os.path.join(PARENT_DIR, 'log')
DATETIME = datetime.now().strftime("%Y%m%d_%H%M%S")

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

def run_pyshcmd(csv_file, max_workers=16, verbose=False, save_json=False, save_txt=False, output_structure="option1"):
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Starting execution for {csv_file}")
        
        args = SimpleNamespace(
            input=csv_file,
            outname=None,  # Use default (CSV stem)
            verbose=verbose,
            save_json=save_json,
            save_txt=save_txt,
            workers=max_workers,
            output_structure=output_structure
        )
        
        pyshcmd.main(args)
        
        logger.info(f"Completed execution for {csv_file}")
        return csv_file, 0, "", ""
    except Exception as e:
        logger.error(f"Error executing {csv_file}: {str(e)}")
        return csv_file, 1, "", str(e)

def main():
    parser = argparse.ArgumentParser(description="Run pyshcmd for CSV files listed in a batch file with optional JSON/text output and structure")
    parser.add_argument("-b", "--batch", required=True, help="Batch file in config/ (e.g., run_batch1.txt)")
    parser.add_argument("-json", "--save-json", action="store_true", help="Save output to JSON file in output/ directory")
    parser.add_argument("-txt", "--save-txt", action="store_true", help="Save per-device output to text files in output/ directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging for console")
    parser.add_argument("-s", "--output-structure", choices=["option1", "option2"], default="option1", 
                       help="Output folder structure: option1 (yyyymmdd_hhmmss/name.json) or option2 (name_yyyymmdd_hhmmss.json)")
    args = parser.parse_args()

    logger = setup_logging(verbose=args.verbose)

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
            executor.submit(run_pyshcmd, csv_file, save_json=args.save_json, save_txt=args.save_txt, 
                           verbose=args.verbose, output_structure=args.output_structure): csv_file
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