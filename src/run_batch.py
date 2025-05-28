#!/usr/bin/env python3
import os
import subprocess
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

# Configure basic logging for the wrapper
def setup_logging(batch_name):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f'log/run_batch_{batch_name}_{timestamp}.log'
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
SCRIPT_PATH = os.path.join(PARENT_DIR, 'src', '1pyshcmd.py')

def read_batch_file(batch_file):
    """
    Read CSV filenames from the specified batch file.
    """
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
    """
    Validate that each CSV file exists in config/.
    """
    logger = logging.getLogger(__name__)
    valid_csvs = []
    for csv_file in csv_files:
        csv_path = os.path.join(CONFIG_DIR, csv_file)
        if os.path.isfile(csv_path):
            valid_csvs.append(csv_file)
        else:
            logger.error(f"CSV file {csv_path} does not exist")
    return valid_csvs

def run_1pyshcmd(csv_file, max_workers=16, verbose=True, save_json=True, save_txt=True):
    """
    Execute 1pyshcmd.py for a single CSV file.
    """
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Starting execution for {csv_file}")

        # Build command, relying on 1pyshcmd.py's default outname and log suffix
        cmd = [
            'python', SCRIPT_PATH,
            '-i', csv_file,
            '-w', str(max_workers)
        ]
        if verbose:
            cmd.append('-v')
        if save_json:
            cmd.append('-json')
        if save_txt:
            cmd.append('-txt')

        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        # Log output
        if result.returncode == 0:
            logger.info(f"Completed execution for {csv_file}")
            logger.debug(f"stdout for {csv_file}: {result.stdout}")
        else:
            logger.error(f"Failed execution for {csv_file}: {result.stderr}")

        return csv_file, result.returncode, result.stdout, result.stderr

    except Exception as e:
        logger.error(f"Error executing {csv_file}: {str(e)}")
        return csv_file, 1, "", str(e)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run 1pyshcmd.py for CSV files listed in a batch file")
    parser.add_argument(
        "-b", "--batch", required=True,
        help="Batch file in config/ containing CSV filenames (e.g., run_batch1.txt)"
    )
    args = parser.parse_args()

    # Setup logging with batch name
    batch_name = Path(args.batch).stem  # e.g., 'run_batch1'
    logger = setup_logging(batch_name)

    # Read and validate CSV files from the batch file
    csv_files = read_batch_file(args.batch)
    if not csv_files:
        return

    valid_csvs = validate_csv_files(csv_files)
    if not valid_csvs:
        logger.error("No valid CSV files to process")
        return

    logger.info(f"Processing {len(valid_csvs)} valid CSV files: {valid_csvs}")

    # Run 1pyshcmd.py for each CSV file concurrently
    max_csv_workers = 8  # Limit concurrent CSV executions
    with ThreadPoolExecutor(max_workers=max_csv_workers) as executor:
        future_to_csv = {
            executor.submit(run_1pyshcmd, csv_file): csv_file
            for csv_file in valid_csvs
        }
        for future in as_completed(future_to_csv):
            csv_file = future_to_csv[future]
            try:
                csv_file, returncode, stdout, stderr = future.result()
                if returncode == 0:
                    logger.info(f"Successfully processed {csv_file}")
                else:
                    logger.error(f"Failed to process {csv_file}: {stderr}")
            except Exception as e:
                logger.error(f"Exception for {csv_file}: {str(e)}")

if __name__ == "__main__":
    main()