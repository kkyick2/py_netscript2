# py_netscript2

This Python script (version `20250704`) uses `Netmiko` to execute commands on network devices concurrently via SSH, reading device details from CSV files and commands from text files. It skips termination commands (e.g., `exit`, `quit`), saves outputs to JSON and per-device text files (if enabled), and logs to a single timestamped file (`log/pyshcmd_<timestamp>.log`) based on a JSON configuration (`logging.dev.json` or `logging.prod.json`). It supports Netmiko's device type autodetection when the `device_type` field in the CSV is empty, saving detected types and connection status to `report_<batch>_<timestamp>.txt` in the `output/` directory, including a device count. The script uses `ThreadPoolExecutor` for device-level parallelism. The wrapper script `run_batch.py` processes multiple CSV files listed in a batch file (e.g., `run_batch1.txt`) using direct function calls, logging to `log/run_batch_<timestamp>.log`. The output structure is configurable via `-s/--output-structure` with `option1` (yyyymmdd_hhmmss/name, default) or `option2` (name_yyyymmdd_hhmmss). Debug logging for the console is enabled with `-v/--verbose`.

## Folder Structure

### Option 1 (-s/--output-structure option1, default)

```
py_netscript2/
├── readme.md
├── src/
│   ├── pyshcmd.py
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
│   ├── run_batch2.txt
│   ├── logging.dev.json
│   └── logging.prod.json
├── output/
│   ├── 20250704_120123/
│   │   ├── devices2.json
│   │   ├── report_devices2.txt
│   │   ├── devices2/
│   │   │   ├── n1pnecint1301.txt
│   │   │   └── n1pneaisn1301.txt
│   │   ├── devices4.json
│   │   ├── report_devices4.txt
│   │   ├── devices4/
│   │   │   ├── n2pnecint1301.txt
│   │   │   └── n2pneaisn1301.txt
│   │   ├── devices50.json
│   │   ├── report_devices50.txt
│   │   ├── devices50/
│   │   │   ├── n3pnecint1301.txt
│   │   │   └── n3pneaisn1301.txt
└── log/
    ├── pyshcmd_20250704_120123.log
    ├── run_batch_20250704_120123.log
```

### Option 2 (-s/--output-structure option2)

```
py_netscript2/
├── output/
│   ├── devices2_20250704_120123.json
│   ├── report_devices2_20250704_120123.txt
│   ├── devices2_20250704_120123/
│   │   ├── n1pnecint1301.txt
│   │   └── n1pneaisn1301.txt
│   ├── devices4_20250704_120123.json
│   ├── report_devices4_20250704_120123.txt
│   ├── devices4_20250704_120123/
│   │   ├── n2pnecint1301.txt
│   │   └── n2pneaisn1301.txt
│   ├── devices50_20250704_120123.json
│   ├── report_devices50_20250704_120123.txt
│   ├── devices50_20250704_120123/
│   │   ├── n3pnecint1301.txt
│   │   └── n3pneaisn1301.txt
└── log/
    ├── pyshcmd_20250704_120123.log
    ├── run_batch_20250704_120123.log
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
username,password,hostname,ip,port,cmdfile,device_type
admin,cisco,n1pnecint1301,172.30.210.11,22,cmd_cisco_ios_all.txt,
admin,cisco,n1pneaisn1301,172.30.210.71,22,cmd_cisco_nxos_all.txt,
```

- **Note**: If `device_type` is empty, Netmiko’s `SSHDetect` autodetects the device type (e.g., `cisco_ios`, `cisco_nxos`), and the result is saved in `report_<batch>_<timestamp>.txt` (e.g., `report_devices2_20250704_120123.txt`) along with connection status and device count.

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
python3 src/pyshcmd.py -i devices2.csv -w 16 -v -json -txt -s option1
```

**Arguments**:

- `-i/--input`: CSV file in `config/` (required).
- `-w/--workers`: Concurrent device connections (default: 16).
- `-o/--outname`: Output folder/JSON base name (defaults to CSV stem).
- `-v/--verbose`: Enable debug logging for console.
- `-json/--save-json`: Save JSON output.
- `-txt/--save-txt`: Save per-device text files.
- `-s/--output-structure`: `option1` (yyyymmdd_hhmmss/name.json, default) or `option2` (name_yyyymmdd_hhmmss.json).

### Batch CSV Execution

```bash
python3 src/run_batch.py -b run_batch1.txt -json -txt -s option2 -v
```

**Arguments**:

- `-b/--batch`: Batch file in `config/` (required, e.g., `run_batch1.txt`).
- `-json/--save-json`: Save JSON output for each CSV.
- `-txt/--save-txt`: Save per-device text files for each CSV.
- `-v/--verbose`: Enable debug logging for console.
- `-s/--output-structure`: `option1` (yyyymmdd_hhmmss/name.json, default) or `option2` (name_yyyymmdd_hhmmss.json).

**Example Outputs** (for `run_batch1.txt` with `-json -txt`):

- **Option 1** (`-s option1`):
  - JSON: `output/20250704_120123/devices2.json`, `output/20250704_120123/devices4.json`, `output/20250704_120123/devices50.json`
  - Text: `output/20250704_120123/devices2/n1pnecint1301.txt`, etc.
  - Report: `output/20250704_120123/report_devices2.txt`, `output/20250704_120123/report_devices4.txt`, etc.
- **Option 2** (`-s option2`):
  - JSON: `output/devices2_20250704_120123.json`, `output/devices4_20250704_120123.json`, `output/devices50_20250704_120123.json`
  - Text: `output/devices2_20250704_120123/n1pnecint1301.txt`, etc.
  - Report: `output/report_devices2_20250704_120123.txt`, `output/report_devices4_20250704_120123.txt`, etc.
- Logs: `log/pyshcmd_20250704_120123.log`, `log/run_batch_20250704_120123.log`

**Text Output Format** (e.g., `output/20250704_120123/devices2/n1pnecint1301.txt` or `output/devices2_20250704_120123/n1pnecint1301.txt`):

```
##### OUTPUT FOR 172.30.210.11 n1pnecint1301 (cisco_ios)
##### WILL EXECUTE:
show clock
show ip interface brief
show running-config | include hostname
##### EXECUTE CMD: show clock
*12:34:56.789 UTC Thu Jul 04 2025
##### EXECUTE CMD: show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
...
##### EXECUTE CMD: show running-config | include hostname
hostname n1pnecint1301
```

**Connection Report Format** (e.g., `output/20250704_120123/report_devices2.txt` or `output/report_devices2_20250704_120123.txt`):

```
Device Connection Report
Generated: 2025-07-04 12:01:23
Number of device: 3
Batch: devices2
IP               Hostname             Input Device Type    Detected Device Type Connection
--------------------------------------------------------------------------------
172.30.210.11    n1pnecint1301        None                 cisco_ios            Success
172.30.210.71    n1pneaisn1301        None                 cisco_nxos           Success
172.31.210.13    n1pnecint1302        cisco_xe             cisco_xe             Success
```

## Notes

- **Output Structure**:
  - Use `-s option1` for time-based grouping (default, e.g., `output/20250704_120123/devices2.json`), ideal for daily or per-run backups.
  - Use `-s option2` for CSV-name-based output (e.g., `output/devices2_20250704_120123.json`), suitable for device-centric organization.
- **Security**: Use a secrets manager instead of CSV credentials in production.
- **Performance**:
  - `pyshcmd.py` uses `ThreadPoolExecutor` with 16 device workers (override with `-w`).
  - `run_batch.py` uses 8 CSV workers, for up to 128 threads. Tune `max_csv_workers` or `-w` if timeouts occur.
  - Option 1 may increase I/O overhead due to nested directories.
  - Autodetection adds slight overhead due to SSH probing.
- **Logging**:
  - Single log file per `pyshcmd.py` run: `log/pyshcmd_<timestamp>.log` (e.g., `log/pyshcmd_20250704_120123.log`).
  - Single log file per `run_batch.py` run: `log/run_batch_<timestamp>.log` (e.g., `log/run_batch_20250704_120123.log`).
  - Both scripts use JSON config (`logging.dev.json` or `logging.prod.json`).
  - Default: `INFO` level for console and file.
  - With `-v/--verbose`: Console at `DEBUG`, file at `INFO` (per JSON config).
  - Autodetected device types are logged at `INFO` level (e.g., `Autodetected device type for 172.30.210.11: cisco_ios`).
  - Connection logs include input and detected device types (e.g., `===> 12:01:23.123 Connection: 172.30.210.11 | hostname: n1pnecint1301 | input device type: None, Detected Device Type: cisco_ios`).
- **Connection Report**:
  - Saved as `report_<batch>_<timestamp>.txt` when devices are processed.
  - Includes `Number of device` (count of devices processed), `IP`, `Hostname`, `Input Device Type`, `Detected Device Type`, and `Connection` (`Success` or `Failed`).
  - `Connection` is `Success` if SSH connection and `enable()` succeed; otherwise, `Failed`.
- **Version**: `pyshcmd.py` version `20250704`, `run_batch.py` version `20250627`.
- **Output Control**:
  - Both scripts support `-json`, `-txt`, and `-s/--output-structure`.
  - Connection report saved as `report_<batch>_<timestamp>.txt` when devices are processed.
- **Fixes**:
  - Corrected `SSHDetect` usage to avoid context manager error (20250703_1643).
  - Updated log message and report format to include input and detected device types (20250703_1756).
  - Added connection status to report (20250704_1120).
  - Removed failed commands from report (20250704_1129).
  - Renamed report file to `report_<batch>_<timestamp>.txt` (20250704_1153).
  - Added device count to report (20250704_1201).
- **Extensibility**:
  - Add `TextFSM`: `ssh.send_command(command, use_textfsm=True)`.
  - Implement retries in `execute_commands`.
