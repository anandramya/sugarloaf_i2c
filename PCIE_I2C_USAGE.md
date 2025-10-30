# PCIe I2C Tool Usage Guide

This guide explains how to use `powertool_pcie.py` for PMBus access via PCIe-based I2C.

## Overview

`powertool_pcie.py` is a Python wrapper around the `i2ctool` binary that provides easy access to PMBus devices through PCIe addresses (e.g., `c1:00.0`).

## Prerequisites

1. **i2ctool binary** - Must be in the current directory or specify path with `--i2c-tool`
2. **Python 3.x** - No additional Python packages required (uses only standard library)
3. **PCIe device** - PMBus controller accessible via PCIe

## Configuration

Default settings in `powertool_pcie.py`:
```python
PCIE_DEVICE = "c1:00.0"      # PCIe address
SLAVE_ADDR = 0x5C            # I2C slave address
I2C_BUS_NUM = 0              # I2C bus number
I2C_TOOL_PATH = "./i2ctool"  # Path to binary
```

## Quick Start Examples

### Test Connection (Read Both Rails)
```bash
./powertool_pcie.py --device c1:00.0 --test
```

### Read Voltage
```bash
# Read TSP_CORE voltage
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd READ_VOUT

# Read TSP_C2C voltage
./powertool_pcie.py -d c1:00.0 --rail TSP_C2C --cmd READ_VOUT
```

### Read Current
```bash
# Read TSP_CORE current
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd READ_IOUT

# Read TSP_C2C current
./powertool_pcie.py -d c1:00.0 --rail TSP_C2C --cmd READ_IOUT
```

### Read Temperature
```bash
# Read temperature
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd READ_TEMP

# Read die temperature
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd READ_DIE_TEMP
```

### Read Status
```bash
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd STATUS_WORD
```

### Set Voltage
```bash
# Set TSP_CORE to 0.8V
./powertool_pcie.py -d c1:00.0 --rail TSP_CORE --cmd VOUT_COMMAND --value 0.8

# Set TSP_C2C to 0.75V
./powertool_pcie.py -d c1:00.0 --rail TSP_C2C --cmd VOUT_COMMAND --value 0.75
```

## Command-Line Options

```
Options:
  -h, --help            Show help message
  -d, --device TEXT     PCIe device address (e.g., c1:00.0)
  -a, --addr HEX        I2C slave address (default: 0x5C)
  -b, --bus INT         I2C bus number (default: 0)
  --i2c-tool PATH       Path to i2ctool binary (default: ./i2ctool)
  --rail RAIL           PMBus rail: TSP_CORE or TSP_C2C
  --cmd COMMAND         PMBus command to execute
  --value FLOAT         Value for write commands
  --test                Run test mode (read both rails)
  -v, --verbose         Verbose output
```

## Supported PMBus Commands

### Read Commands
- `READ_VOUT` - Output voltage
- `READ_IOUT` - Output current
- `READ_TEMP` - Temperature
- `READ_DIE_TEMP` - Die temperature
- `STATUS_WORD` - Status register
- `READ_STATUS` - Alias for STATUS_WORD

### Write Commands
- `VOUT_COMMAND` - Set output voltage (requires --value)

## Rail Mapping

- `TSP_CORE` → PMBus Page 0 (primary rail)
- `TSP_C2C` → PMBus Page 1 (secondary rail)

## Python API Usage

You can also use `powertool_pcie.py` as a Python module:

```python
from powertool_pcie import PowerToolPCIe, PMBusDict

# Initialize with PCIe device
pt = PowerToolPCIe(
    pcie_device="c1:00.0",
    i2c_addr=0x5C,
    bus_num=0,
    i2c_tool_path="./i2ctool"
)

# Read voltage from TSP_CORE (page 0)
vout = pt.Read_Vout(page=0)
print(f"Voltage: {vout:.4f} V")

# Read current from TSP_C2C (page 1)
iout = pt.Read_Iout(page=1)
print(f"Current: {iout:.2f} A")

# Read temperature
temp = pt.Read_Temp(page=0)
print(f"Temperature: {temp:.1f} °C")

# Read status
status = pt.Read_Status_Word(page=0)
print(f"Status: 0x{status:04X}")

# Set voltage
pt.Write_Vout_Command(page=0, voltage=0.8)
print("Voltage set to 0.8V")

# Direct low-level access
value = pt.i2c_read16PMBus(page=0, reg_addr=PMBusDict["READ_VOUT"])
pt.i2c_write16PMBus(page=0, reg_addr=PMBusDict["VOUT_COMMAND"], value=0x0C00)
```

## How It Works

The tool works by calling the `i2ctool` binary with appropriate arguments:

```bash
# Example read command generated internally:
./i2ctool -d c1:00.0 -a 92 -r 139 -t pmbus -l 2 -b 0 --reg-addr-len 1 -j /tmp/i2c_read.json

# Example write command generated internally:
./i2ctool -d c1:00.0 -a 92 -r 33 -t pmbus -b 0 -w 2048 --write-len 2 --reg-addr-len 1
```

The tool then parses the JSON output or stdout to extract values.

## Data Format Conversions

The tool automatically handles PMBus data formats:

- **Linear16** (VOUT): `voltage = mantissa × 2^exponent`
  - Exponent comes from VOUT_MODE register

- **Linear11** (IOUT, TEMP): `value = mantissa × 2^exponent`
  - Exponent embedded in data bits [15:11]
  - Mantissa in bits [10:0]

- **Direct** (DIE_TEMP): 1°C per LSB

## Troubleshooting

### "i2c tool binary not found"
- Ensure `i2ctool` binary is in current directory
- Or specify path: `--i2c-tool /path/to/i2ctool`
- Check file permissions: `chmod +x i2ctool`

### "i2c tool command failed"
- Verify PCIe device exists: check with `lspci | grep c1:00.0`
- Check I2C slave address is correct (default 0x5C)
- Try verbose mode: `-v` to see actual commands being run
- Verify bus number is correct

### "Failed to parse i2c tool output"
- The tool expects JSON output from i2ctool binary
- Check i2ctool version supports `-j` flag
- Run with `-v` to see raw output for debugging

### Permission errors
- May need root privileges: `sudo ./powertool_pcie.py ...`
- Or add user to appropriate group for PCIe device access

## Comparison with Serial I2C Version

| Feature | Serial (powertool.py) | PCIe (powertool_pcie.py) |
|---------|----------------------|--------------------------|
| Connection | USB-to-serial adapter | PCIe device |
| Speed | Slower (~0.3s per cmd) | Faster (direct PCIe) |
| Setup | Requires STM32MP25 | Direct to PCIe device |
| Dependencies | pyserial, serial_i2c_driver | i2ctool binary only |
| Remote | Yes (via serial) | Local only |

## Advanced Usage

### Use Different PCIe Device
```bash
./powertool_pcie.py -d b2:00.0 --test
```

### Use Different I2C Address
```bash
./powertool_pcie.py -d c1:00.0 -a 0x40 --rail TSP_CORE --cmd READ_VOUT
```

### Use Different Bus Number
```bash
./powertool_pcie.py -d c1:00.0 -b 1 --rail TSP_CORE --cmd READ_VOUT
```

### Specify i2ctool Path
```bash
./powertool_pcie.py --i2c-tool /usr/local/bin/i2ctool -d c1:00.0 --test
```

## Example Output

```bash
$ ./powertool_pcie.py -d c1:00.0 --test

✓ Initialized PCIe I2C tool
  PCIe Device: c1:00.0
  I2C Address: 0x5C
  I2C Bus: 0

============================================================
PMBus Test Mode - Reading Both Rails
============================================================

TSP_CORE (Page 0):
------------------------------------------------------------
  VOUT:        0.7461 V
  IOUT:        59.06 A
  TEMP:        48.0 °C
  STATUS_WORD: 0x9203

TSP_C2C (Page 1):
------------------------------------------------------------
  VOUT:        0.7500 V
  IOUT:        12.25 A
  TEMP:        46.0 °C
  STATUS_WORD: 0x9200

============================================================
✓ Test completed
```

## Support

For issues:
1. Check i2ctool binary is accessible and executable
2. Verify PCIe device address with `lspci`
3. Run with `-v` for verbose output
4. Check CLAUDE.md for PMBus register reference
