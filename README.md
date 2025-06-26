# py_netscript2

This Python script (version `20250528_1737`) uses `Netmiko` to execute commands on network devices concurrently, reading device details from CSV files and commands from text files. It skips special termination commands (e.g., `exit`, `quit`), saves outputs to JSON and per-device text files, and logs to timestamped files based on a JSON configuration. A wrapper script (`run_batch.py`) enables concurrent execution for multiple CSV files listed in a batch file (`run_batch1.txt`).

## Folder Structure

```
py_netscript2/
├── readme.md
├── src/
│   ├── 1pyshcmd.py
│   ├── run_batch.py
├── cmd/
│   ├── cmd_cisco_ios_all.txt
│   └── cmd_cisco_nxos_all.txt
├── config/
│   ├── devices.csv
│   ├── devices2.csv
│   ├── devices3.csv
│   ├── devices4.csv
│   ├── ...
│   ├── devices50.csv
│   ├── run_batch1.txt
│   └── logging.dev.json
├── output/
│   ├── devices2_20250528_190523.json
│   ├── devices2_20250528_190523/
│   │   ├── n1pnecint1301.txt
│   │   └── n1pneaisn1301.txt
│   ├── devices4_20250528_190523.json
│   ├── devices4_20250528_190523/
│   │   ├── n2pnecint1301.txt
│   │   └── n2pneaisn1301.txt
│   ├── devices50_20250528_190523.json
│   ├── devices50_20250528_190523/
│   │   ├── n3pnecint1301.txt
│   │   └── n3pneaisn1301.txt
└── log/
    ├── 1pyshcmd_devices2_20250528_190523.log
    ├── 1pyshcmd_devices4_20250528_190523.log
    ├── 1pyshcmd_devices50_20250528_190523.log
    ├── run_batch_20250528_190523.log
```

- **`readme.md`**: This documentation.
- **`src/`**: Contains the main script (`1pyshcmd.py`) and wrapper script (`run_batch.py`).
- **`cmd/`**: Contains command files (e.g., `cmd_cisco_ios_all.txt`), each listing commands to execute on a device.
- **`config/`**: Contains CSV files (e.g., `devices2.csv`), a batch file (`run_batch1.txt`), and logging configuration (`logging.dev.json`).
- **`output/`**: Stores JSON output files and text output directories (e.g., `devices2_20250528_190523/` with per-device text files).
- **`log/`**: Stores timestamped log files (e.g., `1pyshcmd_devices2_20250528_190523.log`).

## Global Variables

The script defines the following global variables in `src/1pyshcmd.py` for path management:

- `PARENT_DIR`: Root directory (`py_netscript2/`), computed as `os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))`.
- `LOG_ENV`: Logging environment, set to `'dev'`.
- `LOG_DIR`: Log directory name (`'log'`).
- `LOG_DIR_FULL`: Full path to `log/` (`PARENT_DIR/log`).
- `CONFIG_DIR`: Configuration directory name (`'config'`).
- `CONFIG_DIR_FULL`: Full path to `config/` (`PARENT_DIR/config`).
- `OUTPUT_DIR`: Output directory name (`'output'`).
- `OUTPUT_DIR_FULL`: Full path to `output/` (`PARENT_DIR/output`).
- `CMD_DIR`: Command directory name (`'cmd'`).
- `CMD_DIR_FULL`: Full path to `cmd/` (`PARENT_DIR/cmd`).
- `DATETIME`: Timestamp for logs and outputs (format: `%Y%m%d_%H%M%S`).
- `version`: Script version, set to `'20250528_1737'`.

## Logging Configuration

Logging is configured via `config/logging.dev.json` (or `logging.prod.json` if `LOG_ENV='prod'`). The configuration defines:

- **Formatters**:
  - `console`: `%(asctime)s: %(levelname)s: %(name)s: %(message)s`
  - `file`: `%(asctime)s: %(levelname)s: %(name)s: %(funcName)18s: %(message)s`
- **Handlers**:
  - `console`: Outputs to stdout, default level `INFO` (switches to `DEBUG` with `-v/--verbose`).
  - `file`: Outputs to `log/1pyshcmd_<input_stem>_<timestamp>.log`, level `INFO`.
- **Loggers**:
  - Root logger (`""`): Level `DEBUG`, uses both `console` and `file` handlers.
  - `file` logger: Level `DEBUG`, uses only the `file` handler.
  - `paramiko` logger: Level `WARNING`, uses both handlers, with `propagate: false` to suppress `INFO`-level messages (e.g., SSH connection details).

Skipped termination commands (`exit`, `quit`) and command execution outputs are logged at `DEBUG` level, reducing log verbosity unless `-v/--verbose` is used.

## Requirements

- Python 3.7+
- Install dependencies:
  ```bash
  pip install netmiko
  ```

## CSV File Format

Each CSV file in `config/` must have the following headers:

- `username`: Device login username.
- `password`: Device login password.
- `hostname`: Device hostname (used for text file names).
- `ip`: Device IP address.
- `port`: SSH port (1–65535).
- `cmdfile`: Name of the command file in `cmd/` (e.g., `cmd_cisco_ios_all.txt`).
- `device_type` (optional): Netmiko device type (defaults to `cisco_ios`).

Example `config/devices2.csv`:

```csv
username,password,hostname,ip,port,cmdfile
admin,cisco,n1pnecint1301,172.30.210.11,22,cmd_cisco_ios_all.txt
admin,cisco,n1pneaisn1301,172.30.210.71,22,cmd_cisco_nxos_all.txt
```

## Command File Format

Command files in `cmd/` list one command per line. Empty lines and lines starting with `#` are ignored. Special termination commands (`exit`, `quit`, case-insensitive) are skipped to prevent closing SSH sessions and logged at `DEBUG` level.

Example `cmd/cmd_cisco_ios_all.txt`:

```
# Cisco IOS commands
show clock
show ip interface brief
show running-config | include hostname
exit  # This will be skipped
```

Example `cmd/cmd_cisco_nxos_all.txt`:

```
# Cisco NX-OS commands
show clock
show interface brief
show running-config | include hostname
quit  # This will be skipped
```

## Batch File Format

The batch file `config/run_batch1.txt` lists CSV filenames to process, one per line. Empty lines are ignored.

Example `config/run_batch1.txt`:

```
devices2.csv
devices4.csv
devices50.csv
```

## Usage

### Single CSV Execution

Run `pyshcmd.py` for a single CSV file:

```bash
python3 src/pyshcmd.py -i devices2.csv -w 16 -v -json -txt
```

**Arguments**:

- `-i/--input`: CSV file in `config/` (required, e.g., `devices2.csv`).
- `-w/--workers`: Number of concurrent device connections (default: 16).
- `-o/--outname`: Base name for output folder and JSON file in `output/` (defaults to input CSV name without extension, e.g., `devices2` for `devices2.csv`).
- `-v/--verbose`: Enable debug-level logging to console.
- `-json/--save-json`: Save output to a JSON file (e.g., `output/devices2_20250528_190523.json`).
- `-txt/--save-txt`: Save per-device text files in a timestamped directory (e.g., `output/devices2_20250528_190523/`).

### Batch CSV Execution

To process multiple CSV files listed in `config/run_batch1.txt` concurrently, use `run_batch.py`:

```bash
python3 src/run_batch.py
python src\run_batch.py -b batch_empf_n.txt -txt -json
```

This script:

- Reads `run_batch1.txt` to get CSV filenames.
- Validates that each CSV exists in `config/`.
- Executes `1pyshcmd.py` for each CSV concurrently using `ThreadPoolExecutor` (8 concurrent CSV executions).
- Uses `1pyshcmd.py`’s default output naming (`<csv_stem>_<timestamp>`) and log naming (`1pyshcmd_<csv_stem>_<timestamp>.log`).
- Logs wrapper activities to `log/run_batch_<timestamp>.log`.

**Output Example** (for `run_batch1.txt` with `devices2.csv`, `devices4.csv`, `devices50.csv`, May 28, 2025, 19:05 HKT):

- JSON files: `output/devices2_20250528_190523.json`, `output/devices4_20250528_190523.json`, `output/devices50_20250528_190523.json`
- Text directories: `output/devices2_20250528_190523/`, `output/devices4_20250528_190523/`, `output/devices50_20250528_190523/`
- Log files: `log/1pyshcmd_devices2_20250528_190523.log`, `log/1pyshcmd_devices4_20250528_190523.log`, `log/1pyshcmd_devices50_20250528_190523.log`, `log/run_batch_20250528_190523.log`

### Example Console Output (Single CSV, `1pyshcmd.py` with `-v`)

```bash
2025-05-28 19:05:23,123: INFO: __main__: Output directory created: output/devices2_20250528_190523
2025-05-28 19:05:23,124: DEBUG: __main__: Skipped termination command 'exit' in cmd/cmd_cisco_ios_all.txt
2025-05-28 19:05:23,124: DEBUG: __main__: Skipped termination command 'quit' in cmd/cmd_cisco_nxos_all.txt
2025-05-28 19:05:23,125: DEBUG: __main__: Read 3 commands from cmd/cmd_cisco_ios_all.txt
2025-05-28 19:05:23,125: DEBUG: __main__: Read 3 commands from cmd/cmd_cisco_nxos_all.txt
2025-05-28 19:05:23,126: DEBUG: __main__: Read 2 devices from config/devices2.csv
2025-05-28 19:05:23,127: INFO: __main__: ===> 19:05:23.123456 Connection: 172.30.210.11
2025-05-28 19:05:23,127: INFO: __main__: ===> 19:05:23.123457 Connection: 172.30.210.71
2025-05-28 19:05:23,223: DEBUG: __main__: <=== 19:05:23.223457 Received: 172.30.210.71 for command: show clock
2025-05-28 19:05:23,323: DEBUG: __main__: <=== 19:05:23.323457 Received: 172.30.210.71 for command: show interface brief
2025-05-28 19:05:23,423: DEBUG: __main__: <=== 19:05:23.423457 Received: 172.30.210.71 for command: show running-config | include hostname
2025-05-28 19:05:23,424: INFO: __main__: Text output saved to output/devices2_20250528_190523/n1pneaisn1301.txt
2025-05-28 19:05:23,523: DEBUG: __main__: <=== 19:05:23.523456 Received: 172.30.210.11 for command: show clock
2025-05-28 19:05:23,623: DEBUG: __main__: <=== 19:05:23.623456 Received: 172.30.210.11 for command: show ip interface brief
2025-05-28 19:05:23,723: DEBUG: __main__: <=== 19:05:23.723456 Received: 172.30.210.11 for command: show running-config | include hostname
2025-05-28 19:05:23,724: INFO: __main__: Text output saved to output/devices2_20250528_190523/n1pnecint1301.txt
2025-05-28 19:05:23,725: INFO: __main__: [main] Running time: 0.823456s
2025-05-28 19:05:23,726: INFO: __main__: JSON output saved to output/devices2_20250528_190523.json
```

### Example Console Output (Batch Execution, `run_batch.py`)

```bash
2025-05-28 19:05:23,123: INFO: Read 3 CSV files from config/run_batch1.txt: ['devices2.csv', 'devices4.csv', 'devices50.csv']
2025-05-28 19:05:23,124: INFO: Processing 3 valid CSV files: ['devices2.csv', 'devices4.csv', 'devices50.csv']
2025-05-28 19:05:23,125: INFO: Starting execution for devices2.csv
2025-05-28 19:05:23,126: INFO: Starting execution for devices4.csv
2025-05-28 19:05:23,127: INFO: Starting execution for devices50.csv
2025-05-28 19:06:23,456: INFO: Completed execution for devices2.csv
2025-05-28 19:06:23,457: INFO: Completed execution for devices4.csv
2025-05-28 19:06:23,458: INFO: Completed execution for devices50.csv
2025-05-28 19:06:23,459: INFO: Successfully processed devices2.csv
2025-05-28 19:06:23,460: INFO: Successfully processed devices4.csv
2025-05-28 19:06:23,461: INFO: Successfully processed devices50.csv
```

## Notes

- **Security**: Storing credentials in CSV files is insecure for production. Use a secrets manager or environment variables.
- **Error Handling**: Validates CSV headers, port numbers, and command file existence in `1pyshcmd.py`. `run_batch.py` validates CSV file existence and captures `stdout`/`stderr` for troubleshooting.
- **Performance**: Concurrent execution with `run_batch.py` speeds up processing of multiple CSVs. The default of 8 CSV workers and 16 device workers per CSV (up to 128 SSH connections) may need tuning based on system and network capacity.
- **Logging**:
  - `1pyshcmd.py` logs to `log/1pyshcmd_<csv_stem>_<timestamp>.log`.
  - `run_batch.py` logs to `log/run_batch_<timestamp>.log` for high-level execution status.
- **Version**: The `1pyshcmd.py` version is `20250528_1737`.
- **Output Organization**:
  - JSON files and text directories are named with the CSV stem (e.g., `devices2_20250528_190523.json`).
  - Text files are stored in corresponding directories (e.g., `devices2_20250528_190523/n1pnecint1301.txt`).
- **Extensibility**:
  - Add `TextFSM` in `1pyshcmd.py` for structured output: `ssh.send_command(command, use_textfsm=True)`.
  - Implement retries in `execute_commands` for failed commands.
  - Extend `run_batch.py` to support multiple batch files or custom arguments per CSV.
