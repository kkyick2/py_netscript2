# py_netscript2

This Python script (version `20250626`) uses `Netmiko` to execute commands on network devices concurrently via SSH, reading device details from CSV files and commands from text files. It skips termination commands (e.g., `exit`, `quit`), saves outputs to JSON and per-device text files (if enabled), and logs to timestamped files based on a JSON configuration. The script uses `ThreadPoolExecutor` for device-level parallelism. Wrapper scripts (`run_batch.py` and `run_batch_mp.py`) process multiple CSV files listed in a batch file (e.g., `run_batch1.txt`) using direct function calls or multiprocessing, respectively.

## Folder Structure

```
py_netscript2/
├── readme.md
├── src/
│   ├── pyshcmd.py
│   ├── run_batch.py
│   ├── run_batch_mp.py
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
│   ├── run_batch2.txt
│   └── logging.dev.json
├── output/
│   ├── devices2_20250626_230323.json
│   ├── devices2_20250626_230323/
│   │   ├── n1pnecint1301.txt
│   │   └── n1pneaisn1301.txt
│   ├── devices4_20250626_230323.json
│   ├── devices4_20250626_230323/
│   │   ├── n2pnecint1301.txt
│   │   └── n2pneaisn1301.txt
│   ├── devices50_20250626_230323.json
│   ├── devices50_20250626_230323/
│   │   ├── n3pnecint1301.txt
│   │   └── n3pneaisn1301.txt
└── log/
    ├── pyshcmd_devices2_20250626_230323.log
    ├── pyshcmd_devices4_20250626_230323.log
    ├── pyshcmd_devices50_20250626_230323.log
    ├── run_batch_run_batch1_20250626_230323.log
    ├── run_batch_mp_run_batch1_20250626_230323.log
```

## Requirements

- **Python 3.7+**:

  - Download from [python.org/downloads](https://www.python.org/downloads/).
  - Check **“Add Python to PATH”** during installation.
  - Verify: `python3 --version`, `pip --version`.
  - On Windows, disable Microsoft Store aliases in **Settings > Apps > Advanced app settings > App execution aliases** if `python` prompts the Store.
  - Add Python and Scripts directories to PATH if needed (e.g., `C:\Users\<Username>\AppData\Local\Programs\Python\Python39\`).

- **Dependencies**:
  ```bash
  pip install netmiko
  ```

## CSV File Format

**Example** `config/devices2.csv`:

```csv
username,password,hostname,ip,port,cmdfile
admin,cisco,n1pnecint1301,172.30.210.11,22,cmd_cisco_ios_all.txt
admin,cisco,n1pneaisn1301,172.30.210.71,22,cmd_cisco_nxos_all.txt
```

## Command File Format

**Example** `cmd/cmd_cisco_ios_all.txt`:

```
# Cisco IOS commands
show clock
show ip interface brief
show running-config | include hostname
exit  # Skipped
```

## Batch File Format

**Example** `config/run_batch1.txt`:

```
devices2.csv
devices4.csv
devices50.csv
```

**Example** `config/run_batch2.txt`:

```
devices1.csv
devices5.csv
devices11.csv
```

## Usage

### Single CSV Execution

```bash
python3 src/pyshcmd.py -i devices2.csv -w 16 -v -json -txt
```

**Arguments**:

- `-i/--input`: CSV file in `config/` (required).
- `-w/--workers`: Concurrent device connections (default: 4).
- `-o/--outname`: Output folder/JSON base name (defaults to CSV stem).
- `-v/--verbose`: Debug-level console logging.
- `-json/--save-json`: Save JSON output.
- `-txt/--save-txt`: Save per-device text files.

### Batch CSV Execution (Direct Call)

```bash
python3 src/run_batch.py -b run_batch1.txt -json -txt
```

**Arguments**:

- `-b/--batch`: Batch file in `config/` (required, e.g., `run_batch1.txt`).
- `-json/--save-json`: Save JSON output for each CSV.
- `-txt/--save-txt`: Save per-device text files for each CSV.

### Batch CSV Execution (Multiprocessing)

```bash
python3 src/run_batch_mp.py -b run_batch1.txt
```

**Arguments**:

- `-b/--batch`: Batch file in `config/` (required, e.g., `run_batch1.txt`).

**Example Outputs** (for `run_batch1.txt` with `-json -txt`):

- JSON: `output/devices2_20250626_230323.json`, `output/devices4_20250626_230323.json`, `output/devices50_20250626_230323.json`
- Text: `output/devices2_20250626_230323/n1pnecint1301.txt`, etc.
- Logs: `log/pyshcmd_devices2_20250626_230323.log`, `log/run_batch_run_batch1_20250626_230323.log` or `log/run_batch_mp_run_batch1_20250626_230323.log`

**Text Output Format** (e.g., `output/devices2_20250626_230323/n1pnecint1301.txt`):

```
##### OUTPUT FOR 172.30.210.11 n1pnecint1301
##### WILL EXECUTE:
show clock
show ip interface brief
show running-config | include hostname
##### EXECUTE CMD: show clock
*12:34:56.789 UTC Thu Jun 26 2025
##### EXECUTE CMD: show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
...
##### EXECUTE CMD: show running-config | include hostname
hostname n1pnecint1301
```

## Notes

- **Security**: Use a secrets manager instead of CSV credentials in production.
- **Performance**:
  - `pyshcmd.py` uses `ThreadPoolExecutor` with 4 device workers (override with `-w`).
  - `run_batch.py` uses 8 CSV workers; `run_batch_mp.py` uses 8 processes.
  - Total: up to 32 threads (`run_batch.py`) or processes (`run_batch_mp.py`). Tune `max_csv_workers` or `-w` if timeouts occur.
- **Logging**: Per-CSV logs (`pyshcmd_<csv_stem>_<timestamp>.log`) and batch logs (`run_batch_<batch_name>_<timestamp>.log` or `run_batch_mp_<batch_name>_<timestamp>.log`).
- **Version**: `pyshcmd.py` and `run_batch.py` version `20250626`.
- **Output Control**:
  - `run_batch.py` supports `--save-json` and `--save-txt` to toggle outputs.
  - `run_batch_mp.py` always saves JSON and text outputs.
- **Extensibility**:
  - Add `TextFSM`: `ssh.send_command(command, use_textfsm=True)`.
  - Implement retries in `execute_commands`.
  - Extend `run_batch_mp.py` to support `--save-json` and `--save-txt`.
