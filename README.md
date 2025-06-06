# py_netscript2

This Python script (version `20250528_1737`) uses `Netmiko` to execute commands on network devices concurrently, reading device details from a CSV file and commands from text files. It skips special termination commands (e.g., `exit`, `quit`), saves outputs to JSON and per-device text files, and logs to timestamped files based on a JSON configuration.

## Folder Structure

```
py_netscript2/
├── readme.md
├── src/
│   ├── 1pyshcmd.py
├── cmd/
│   ├── cmd_cisco_ios_all.txt
│   └── cmd_cisco_nxos_all.txt
├── config/
│   ├── devices.csv
│   ├── devices2.csv
│   ├── devices3.csv
│   ├── ...
│   ├── devices50.csv
│   └── logging.dev.json
├── output/
│   ├── devices_20250528_173737.json
│   ├── devices_20250528_173737/
│   │   ├── n1pnecint1301.txt
│   │   └── n1pneaisn1301.txt
│   ├── devices2_20250528_173737.json
│   ├── devices2_20250528_173737/
│   │   ├── n2pnecint1301.txt
│   │   └── n2pneaisn1301.txt
└── log/
    ├── 1pyshcmd_devices_20250528_173737.log
    ├── 1pyshcmd_devices2_20250528_173737.log
```

- **`readme.md`**: This documentation.
- **`src/`**: Contains the main script (`1pyshcmd.py`).
- **`cmd/`**: Contains command files (e.g., `cmd_cisco_ios_all.txt`), each listing commands to execute on a device.
- **`config/`**: Contains CSV files (e.g., `devices.csv`) and logging configuration (`logging.dev.json`).
- **`output/`**: Stores JSON output files and text output directories (e.g., `devices_20250528_173737/` with per-device text files).
- **`log/`**: Stores timestamped log files (e.g., `1pyshcmd_devices_20250528_173737.log`).

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

Example `config/devices.csv`:

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

## Usage

Run `1pyshcmd.py` for a single CSV file:

```bash
python3 src/1pyshcmd.py -i devices2.csv -w 16 -v -json -txt
```

### Arguments

- `-i/--input`: CSV file in `config/` (required, e.g., `devices2.csv`).
- `-w/--workers`: Number of concurrent device connections (default: 16).
- `-o/--outname`: Base name for output folder and JSON file in `output/` (defaults to input CSV name without extension, e.g., `devices2` for `devices2.csv`).
- `-v/--verbose`: Enable debug-level logging to console.
- `-json/--save-json`: Save output to a JSON file (e.g., `output/devices2_20250528_173737.json`).
- `-txt/--save-txt`: Save per-device text files in a timestamped directory (e.g., `output/devices2_20250528_173737/`).

### Example Output

**Console** (example, based on May 28, 2025, 17:37 HKT, with `-v`):

```
2025-05-28 17:37:37,123: INFO: __main__: Output directory created: output/devices2_20250528_173737
2025-05-28 17:37:37,124: DEBUG: __main__: Skipped termination command 'exit' in cmd/cmd_cisco_ios_all.txt
2025-05-28 17:37:37,124: DEBUG: __main__: Skipped termination command 'quit' in cmd/cmd_cisco_nxos_all.txt
2025-05-28 17:37:37,125: DEBUG: __main__: Read 3 commands from cmd/cmd_cisco_ios_all.txt
2025-05-28 17:37:37,125: DEBUG: __main__: Read 3 commands from cmd/cmd_cisco_nxos_all.txt
2025-05-28 17:37:37,126: DEBUG: __main__: Read 2 devices from config/devices2.csv
2025-05-28 17:37:37,127: INFO: __main__: ===> 17:37:37.123456 Connection: 172.30.210.11
2025-05-28 17:37:37,127: INFO: __main__: ===> 17:37:37.123457 Connection: 172.30.210.71
2025-05-28 17:37:37,223: DEBUG: __main__: <=== 17:37:37.223457 Received: 172.30.210.71 for command: show clock
2025-05-28 17:37:37,323: DEBUG: __main__: <=== 17:37:37.323457 Received: 172.30.210.71 for command: show interface brief
2025-05-28 17:37:37,423: DEBUG: __main__: <=== 17:37:37.423457 Received: 172.30.210.71 for command: show running-config | include hostname
2025-05-28 17:37:37,424: INFO: __main__: Text output saved to output/devices2_20250528_173737/n1pneaisn1301.txt
2025-05-28 17:37:37,523: DEBUG: __main__: <=== 17:37:37.523456 Received: 172.30.210.11 for command: show clock
2025-05-28 17:37:37,623: DEBUG: __main__: <=== 17:37:37.623456 Received: 172.30.210.11 for command: show ip interface brief
2025-05-28 17:37:37,723: DEBUG: __main__: <=== 17:37:37.723456 Received: 172.30.210.11 for command: show running-config | include hostname
2025-05-28 17:37:37,724: INFO: __main__: Text output saved to output/devices2_20250528_173737/n1pnecint1301.txt
2025-05-28 17:37:37,725: INFO: __main__: [main] Running time: 0.823456s
2025-05-28 17:37:37,726: INFO: __main__: JSON output saved to output/devices2_20250528_173737.json
```

**Log File** (`log/1pyshcmd_devices2_20250528_173737.log` excerpt):

```
2025-05-28 17:37:37,123: INFO: __main__: main                  : Output directory created: output/devices2_20250528_173737
2025-05-28 17:37:37,124: DEBUG: __main__: read_commands         : Skipped termination command 'exit' in cmd/cmd_cisco_ios_all.txt
2025-05-28 17:37:37,124: DEBUG: __main__: read_commands         : Skipped termination command 'quit' in cmd/cmd_cisco_nxos_all.txt
2025-05-28 17:37:37,125: DEBUG: __main__: read_commands         : Read 3 commands from cmd/cmd_cisco_ios_all.txt
2025-05-28 17:37:37,125: DEBUG: __main__: read_commands         : Read 3 commands from cmd/cmd_cisco_nxos_all.txt
2025-05-28 17:37:37,126: DEBUG: __main__: read_devices          : Read 2 devices from config/devices2.csv
2025-05-28 17:37:37,127: INFO: __main__: execute_commands      : ===> 17:37:37.123456 Connection: 172.30.210.11
2025-05-28 17:37:37,127: INFO: __main__: execute_commands      : ===> 17:37:37.123457 Connection: 172.30.210.71
2025-05-28 17:37:37,223: DEBUG: __main__: execute_commands      : <=== 17:37:37.223457 Received: 172.30.210.71 for command: show clock
2025-05-28 17:37:37,323: DEBUG: __main__: execute_commands      : <=== 17:37:37.323457 Received: 172.30.210.71 for command: show interface brief
```

## Notes

- **Security**: Storing credentials in CSV files is insecure for production. Use a secrets manager or environment variables.
- **Error Handling**: Validates CSV headers, port numbers, and command file existence. Skips termination commands (`exit`, `quit`) with `DEBUG` logs. Connection and command errors are logged per device.
- **Performance**: Text files are generated as each device completes, improving speed for large device lists. The default of 16 workers may need tuning based on system and network capacity.
- **Logging**: Logs are saved to `log/1pyshcmd_<input_stem>_<timestamp>.log` with detailed formatting. The `-v/--verbose` flag enables `DEBUG` output to the console, including skipped commands and command outputs. `paramiko` logs are suppressed below `WARNING` level.
- **Version**: The script version is `20250528_1737`.
- **Output Naming**: The `--outname` argument defaults to the input CSV’s stem (e.g., `devices2` for `devices2.csv`), ensuring intuitive output file and directory names.
- **Extensibility**:
  - Add `TextFSM` for structured output: `ssh.send_command(command, use_textfsm=True)`.
  - Implement retries in `execute_commands` for failed commands.
  - Extend CSV schema for additional `Netmiko` parameters (e.g., `secret`).
