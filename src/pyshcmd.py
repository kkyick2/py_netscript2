#!/usr/bin/env python3
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import time
import sys
import os
import logging
import logging.config
import csv
import json
import argparse
from pathlib import Path
from netmiko import ConnectHandler, NetMikoAuthenticationException, NetmikoTimeoutException
version = '20250627'
# Fixed --output-structure: option1 (timestamp/name), option2 (name_timestamp); removed run_batch_mp.py; single log file pyshcmd_<timestamp>.log (20250627_1454)

# Global variables for directory paths and logging
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOG_ENV = 'dev'
LOG_DIR = 'log'
LOG_DIR_FULL = os.path.join(PARENT_DIR, LOG_DIR)
CONFIG_DIR = 'config'
CONFIG_DIR_FULL = os.path.join(PARENT_DIR, CONFIG_DIR)
OUTPUT_DIR = 'output'
OUTPUT_DIR_FULL = os.path.join(PARENT_DIR, OUTPUT_DIR)
CMD_DIR = 'cmd'
CMD_DIR_FULL = os.path.join(PARENT_DIR, CMD_DIR)
DATETIME = datetime.now().strftime("%Y%m%d_%H%M%S")

# Configure logging using JSON configuration
def setup_logging(verbose=False):
    log_configs = {
        "dev": "logging.dev.json",
        "prod": "logging.prod.json"
    }
    log_name = Path(os.path.basename(__file__)).stem
    log_config = log_configs.get(LOG_ENV, "logging.dev.json")
    log_config_path = os.path.join(PARENT_DIR, CONFIG_DIR, log_config)
    log_file_path = os.path.join(PARENT_DIR, LOG_DIR, f'{log_name}_{DATETIME}.log')
    os.makedirs(LOG_DIR_FULL, exist_ok=True)

    with open(log_config_path, 'r') as f:
        config = json.load(f)
    
    for handler in config['handlers'].values():
        if handler['class'] == 'logging.FileHandler':
            handler['filename'] = log_file_path

    if verbose:
        config['handlers']['console']['level'] = 'DEBUG'

    logging.config.dictConfig(config)

# Timing decorator
def count_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        logger = logging.getLogger(__name__)
        logger.info(f"[{func.__name__}] Running time: {round(time.time() - start, 6)}s")
        return result
    return wrapper

# Read commands from a text file
def read_commands(commands_file):
    logger = logging.getLogger(__name__)
    commands_path = os.path.join(CMD_DIR_FULL, commands_file)
    termination_commands = {"exit", "quit"}
    try:
        with open(commands_path, "r") as f:
            commands = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
                and line.strip().lower() not in termination_commands
            ]
        with open(commands_path, "r") as f:
            for line in f:
                if line.strip().lower() in termination_commands:
                    logger.debug(f"Skipped termination command '{line.strip()}' in {commands_path}")
        if not commands:
            logger.error(f"No valid commands found in {commands_path}")
            return []
        logger.debug(f"Read {len(commands)} commands from {commands_path}")
        return commands
    except OSError as e:
        logger.error(f"Error reading {commands_path}: {str(e)}")
        return []

# Read devices from a CSV file
def read_devices(csv_file):
    logger = logging.getLogger(__name__)
    csv_path = os.path.join(CONFIG_DIR_FULL, csv_file)
    devices = []
    required_fields = ["username", "password", "hostname", "ip", "port", "cmdfile"]
    try:
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            if not all(field in reader.fieldnames for field in required_fields):
                missing = [field for field in required_fields if field not in reader.fieldnames]
                logger.error(f"CSV file {csv_path} missing required fields: {missing}")
                sys.exit(1)
            
            for row in reader:
                device = {
                    "username": row["username"],
                    "password": row["password"],
                    "hostname": row["hostname"],
                    "ip": row["ip"],
                    "port": int(row["port"]),
                    "cmdfile": row["cmdfile"],
                    "device_type": row.get("device_type", "cisco_ios")
                }
                cmd_file_path = os.path.join(CMD_DIR_FULL, device["cmdfile"])
                if not os.path.isfile(cmd_file_path):
                    logger.error(f"Command file {cmd_file_path} for device {device['ip']} does not exist")
                    sys.exit(1)
                try:
                    if not (1 <= device["port"] <= 65535):
                        logger.error(f"Invalid port {device['port']} for device {device['ip']}")
                        sys.exit(1)
                except ValueError:
                    logger.error(f"Port {row['port']} for device {device['ip']} is not a valid integer")
                    sys.exit(1)
                devices.append(device)
        
        if not devices:
            logger.error(f"No devices found in {csv_path}")
            sys.exit(1)
        logger.debug(f"Read {len(devices)} devices from {csv_path}")
        return devices
    except OSError as e:
        logger.error(f"Error reading {csv_path}: {str(e)}")
        sys.exit(1)

# Execute commands on a single device
def execute_commands(device_dict, output_dir, save_txt):
    logger = logging.getLogger(__name__)
    start_msg = "===> {} Connection: {}"
    received_msg = "<=== {} Received: {} for command: {}"
    ip = device_dict.get("ip", "Unknown")
    hostname = device_dict.get("hostname", ip)
    results = {}
    
    logger.info(start_msg.format(datetime.now().time(), ip))

    commands = read_commands(device_dict["cmdfile"])
    if not commands:
        logger.error(f"No commands to execute for {ip}")
        return {ip: {}}

    try:
        with ConnectHandler(
            device_type=device_dict["device_type"],
            ip=str(device_dict["ip"]),
            username=device_dict["username"],
            password=device_dict["password"],
            port=device_dict["port"]
        ) as ssh:
            ssh.enable()
            for command in commands:
                try:
                    output = ssh.send_command(command)
                    results[command] = output
                    logger.debug(received_msg.format(datetime.now().time(), ip, command))
                except Exception as e:
                    logger.error(f"Failed to execute '{command}' on {ip}: {str(e)}")
                    results[command] = f"Error: {str(e)}"
        
        if save_txt:
            filename = os.path.join(output_dir, f"{hostname}.txt")
            try:
                with open(filename, "w") as f:
                    f.write(f"##### OUTPUT FOR {ip} {hostname}\n")
                    f.write(f"##### WILL EXECUTE:\n")
                    for command in commands:
                        f.write(f"{command}\n")
                    for command, output in results.items():
                        f.write(f"##### EXECUTE CMD: {command}\n")
                        f.write(f"{output}\n\n")
                logger.info(f"Text output saved to {filename}")
            except OSError as e:
                logger.error(f"Failed to save text output to {filename}: {str(e)}")
        
        return {ip: results}
    except (NetMikoAuthenticationException, NetmikoTimeoutException) as e:
        logger.error(f"Failed to connect to {ip}: {str(e)}")
        return {ip: {cmd: f"Error: {str(e)}" for cmd in commands}}

# Send commands to multiple devices
def send_command_to_devices(devices, max_workers=4, output_dir="", save_txt=False):
    logger = logging.getLogger(__name__)
    data = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_list = [
            executor.submit(execute_commands, device, output_dir, save_txt)
            for device in devices
        ]
        logger.debug(f"Submitted {len(future_list)} tasks to executor")

        for future in as_completed(future_list):
            try:
                result = future.result()
                logger.debug(f"Completed task for {list(result.keys())[0]}")
                data.update(result)
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
    
    return data

# Save output to JSON
def save_json_output(data, output_base, timestamp, output_structure):
    logger = logging.getLogger(__name__)
    os.makedirs(OUTPUT_DIR_FULL, exist_ok=True)
    if output_structure == "option1":
        os.makedirs(os.path.join(OUTPUT_DIR_FULL, timestamp), exist_ok=True)
        filename = os.path.join(OUTPUT_DIR_FULL, timestamp, f"{output_base}.json")
    else:  # option2
        filename = os.path.join(OUTPUT_DIR_FULL, f"{output_base}_{timestamp}.json")
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
        logger.info(f"JSON output saved to {filename}")
    except OSError as e:
        logger.error(f"Error saving JSON output to {filename}: {str(e)}")

@count_time
def main(args=None):
    if args is None:
        parser = argparse.ArgumentParser(description="Execute commands on network devices with configurable output structure")
        parser.add_argument("-i", "--input", required=True, help="CSV file name as input in config/ directory")
        parser.add_argument("-o", "--outname", default=None, help="Base name for output folder and JSON file")
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
        parser.add_argument("-json", "--save-json", action="store_true", help="Save output to JSON file in output/ directory")
        parser.add_argument("-txt", "--save-txt", action="store_true", help="Save per-device output to text files in output/ directory")
        parser.add_argument("-w", "--workers", type=int, default=16, help="Number of parallel device connections")
        parser.add_argument("-s", "--output-structure", choices=["option1", "option2"], default="option1", 
                           help="Output folder structure: option1 (yyyymmdd_hhmmss/name.json) or option2 (name_yyyymmdd_hhmmss.json)")
        args = parser.parse_args()

    inname = Path(args.input).stem
    outname = args.outname if args.outname is not None else inname

    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    if args.save_txt:
        if args.output_structure == "option1":
            output_dir = os.path.join(OUTPUT_DIR_FULL, DATETIME, outname)
        else:  # option2
            output_dir = os.path.join(OUTPUT_DIR_FULL, f"{outname}_{DATETIME}")
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory created: {output_dir}")
    else:
        output_dir = ""

    devices = read_devices(args.input)

    result = send_command_to_devices(
        devices, max_workers=args.workers, output_dir=output_dir, save_txt=args.save_txt
    )

    if args.save_json:
        save_json_output(result, outname, DATETIME, args.output_structure)

if __name__ == "__main__":
    main()