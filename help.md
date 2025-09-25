# PowerTool — Extended Help

A fast, production-grade PMBus command-line tool for Total Phase Aardvark I²C adapters.

## Quick Start

1. Connect the Aardvark to your PMBus device (I²C master mode)
2. Power the device; if needed, enable target power with `--power-target`
3. Install dependencies:
   ```bash
   pip install PyYAML aardvark_py
   # Also install Total Phase Aardvark drivers from totalphase.com
   ```
4. Make the script executable (optional):
   ```bash
   chmod +x powertool.py
   # Now you can run: ./powertool.py instead of python3 powertool.py
   ```

## Commands

### Scan
Find all I²C devices on the bus (0x20-0x7F range):
```bash
./powertool.py scan
./powertool.py scan --port 0 --bitrate-khz 100
```

### Read
Read a single PMBus register:
```bash
# Read by rail and command name
./powertool.py TSP_CORE READ_VOUT
./powertool.py TSP_C2C READ_IOUT

# Read status registers
./powertool.py TSP_CORE STATUS_WORD
./powertool.py TSP_C2C STATUS_BYTE
```

### Direct Hex Register Access (New)
Read/write any PMBus register directly by hex address with simplified syntax:
```bash
# Simplified hex register reads (defaults to 2 bytes)
./powertool.py TSP_CORE READ 0x21      # Read VOUT_COMMAND from page 0
./powertool.py TSP_C2C READ 0x8B       # Read READ_VOUT from page 1
./powertool.py TSP_CORE READ 0x79      # Read STATUS_WORD from page 0

# Single-byte register reads
./powertool.py TSP_CORE READ 0x20 1    # Read VOUT_MODE (1 byte)
./powertool.py TSP_C2C READ 0x78 1     # Read STATUS_BYTE (1 byte)

# Direct hex register writes (with verification)
./powertool.py TSP_CORE WRITE 0x21 0x0800    # Write to VOUT_COMMAND
./powertool.py TSP_C2C WRITE 0x03 0x00       # Clear faults on page 1

# Multiple hex formats supported
./powertool.py TSP_CORE READ 0x8B      # Standard hex (0x prefix)
./powertool.py TSP_CORE READ 8Bh       # Intel hex format (h suffix)
./powertool.py TSP_CORE READ 8B        # Plain hex (no prefix)
```

### Legacy Direct Register Access
Read any PMBus register by English name or hex address using the legacy format:
```bash
# Single reads using English command names (preferred)
./powertool.py page 0 READ_VOUT READ 2
./powertool.py page 1 STATUS_WORD READ 2
./powertool.py page 0 VOUT_MODE READ 1
./powertool.py page 0 MFR_VID_RES_R1 READ 2

# Continuous logging using English command names
./powertool.py page 0 READ_VOUT LOG 2     # Logs to CSV
./powertool.py page 1 STATUS_WORD LOG 2   # Monitor status
./powertool.py page 0 VOUT_MODE LOG 1     # Monitor mode changes

# Using hex addresses (alternative)
./powertool.py page 0 0x8B READ 2    # Single read
./powertool.py page 0 0x8B LOG 2     # Continuous log
./powertool.py page 0 8Bh READ 2     # Alternative hex format
```

### Write
Write a PMBus register:
```bash
# Set voltage command (requires voltage value)
./powertool.py TSP_CORE VOUT_COMMAND 0.8
./powertool.py TSP_C2C VOUT_COMMAND 0.75

# Clear faults
./powertool.py TSP_CORE CLEAR_FAULTS
./powertool.py TSP_C2C CLEAR_FAULTS
```

### Monitor
Continuously monitor registers:
```bash
# Monitor single command and log to CSV
./powertool.py TSP_CORE READ_VOUT log
./powertool.py TSP_C2C READ_IOUT log

# Monitor status registers
./powertool.py TSP_CORE STATUS_WORD log
./powertool.py TSP_C2C STATUS_BYTE log

# Continuous logging mode (all rails)
./powertool.py log
```

## PMBus Formats

### Linear11
- 16-bit format: 5-bit exponent + 11-bit mantissa
- Value = mantissa × 2^exponent
- Range: ±1024 × 2^(-16...15)

### Linear16
- 16-bit mantissa with fixed exponent
- Value = mantissa × 2^exponent
- Exponent from VOUT_MODE or command spec

### Direct
- Value = (Y × 10^(-R) - b) / m
- Where Y is raw register value
- Coefficients m, b, R from datasheet

### Raw
- Uninterpreted byte/word values
- Displayed as hex

## Configuration

The tool includes built-in support for standard PMBus commands and MPS-specific registers. Key registers are defined in the PMBusDict within powertool.py:

- Standard PMBus commands (0x00-0x97)
- MFR-specific commands (0x67, 0xD1-0xD8)
- Phase current registers (0x0C00-0x0C0F)
- Rail selection via PAGE command (0x00)

Supported rails:
- TSP_CORE: Primary voltage rail
- TSP_C2C: Secondary voltage rail

## Performance Tips

1. **Fast Mode**: Use `--fast` for optimized I²C transactions
2. **Buffering**: CSV writes are buffered (100 rows)
3. **Bitrate**: Higher bitrates reduce latency but may cause errors
4. **PEC**: Disabling PEC slightly improves speed
5. **Repeated Start**: Tool uses combined write-read for efficiency

## Troubleshooting

### No devices found
- Check connections (SDA, SCL, GND)
- Verify pullups are enabled
- Try slower bitrate (100 kHz)
- Check target power

### PEC errors
- Some devices don't support PEC
- Try without `--pec` flag
- Check for signal integrity issues

### Read errors
- Verify correct I²C address
- Check command code in datasheet
- Some registers may be write-only

### Performance issues
- Reduce number of monitored registers
- Increase interval between samples
- Use `--fast` mode
- Check USB connection quality

## Common Register Reference

### PMBus Register Map (Hex Addresses)
| Register | Address | Size | Description |
|----------|---------|------|-------------|
| VOUT_COMMAND | 0x21 | 2 bytes | Voltage setpoint command |
| VOUT_MODE | 0x20 | 1 byte | Voltage encoding mode |
| READ_VOUT | 0x8B | 2 bytes | Actual output voltage |
| READ_IOUT | 0x8C | 2 bytes | Output current |
| READ_TEMPERATURE_1 | 0x8D | 2 bytes | Primary temperature |
| STATUS_BYTE | 0x78 | 1 byte | Summary status |
| STATUS_WORD | 0x79 | 2 bytes | Detailed status |
| STATUS_VOUT | 0x7A | 1 byte | Output voltage status |
| STATUS_IOUT | 0x7B | 1 byte | Output current status |
| CLEAR_FAULTS | 0x03 | 0 bytes | Clear all faults command |
| MFR_VID_RES_R1 | 0x29 | 2 bytes | VID resolution settings |
| MFR_VR_CONFIG | 0x67 | 2 bytes | VR configuration |

## Examples

### Hex Register Examples (New Simplified Format)
```bash
# Quick voltage check
./powertool.py TSP_CORE READ 0x8B      # Read actual voltage
./powertool.py TSP_C2C READ 0x8B       # Read TSP_C2C voltage

# Status monitoring
./powertool.py TSP_CORE READ 0x79      # Check detailed status
./powertool.py TSP_CORE READ 0x78 1    # Check summary status

# Configuration reads
./powertool.py TSP_CORE READ 0x29      # Check VID resolution
./powertool.py TSP_CORE READ 0x20 1    # Check voltage mode

# Write operations (with verification)
./powertool.py TSP_CORE WRITE 0x21 0x0C00  # Set voltage to ~0.75V
./powertool.py TSP_CORE WRITE 0x03 0x00    # Clear all faults

# Both rails comparison
./powertool.py TSP_CORE READ 0x21      # TSP_CORE setpoint
./powertool.py TSP_C2C READ 0x21       # TSP_C2C setpoint
```

### Power Supply Monitoring
```bash
# Monitor voltage and current
./powertool.py TSP_CORE READ_VOUT log
./powertool.py TSP_C2C READ_IOUT log

# Set specific voltages
./powertool.py TSP_CORE VOUT_COMMAND 0.8
./powertool.py TSP_C2C VOUT_COMMAND 0.75
```

### Direct Register Analysis
```bash
# Read configuration registers using English names
./powertool.py page 0 MFR_VID_RES_R1 READ 2    # VID resolution settings
./powertool.py page 0 VOUT_MODE READ 1         # Output voltage mode
./powertool.py page 0 MFR_VR_CONFIG READ 2     # VR configuration

# Continuous monitoring with CSV logging
./powertool.py page 0 READ_VOUT LOG 2          # Log TSP_CORE voltage
./powertool.py page 1 READ_VOUT LOG 2          # Log TSP_C2C voltage
./powertool.py page 0 STATUS_WORD LOG 2        # Monitor TSP_CORE status
./powertool.py page 1 STATUS_WORD LOG 2        # Monitor TSP_C2C status
```

### Fault Analysis
```bash
# Monitor status registers
./powertool.py TSP_CORE STATUS_WORD log

# Direct status register reads using English names
./powertool.py page 0 STATUS_WORD READ 2       # Overall status
./powertool.py page 0 STATUS_VOUT READ 1       # Voltage status
./powertool.py page 0 STATUS_IOUT READ 1       # Current status
./powertool.py page 0 STATUS_TEMPERATURE READ 1 # Temperature status
```

### Test All Commands
```bash
# Run comprehensive test suite
./test_all_pmbus_commands.py

# Run single readback test
./powertool.py test
```

## Signal Connections

Typical Aardvark to PMBus device connections:

```
Aardvark    PMBus Device
--------    ------------
SCL    <--> SCL (Clock)
SDA    <--> SDA (Data)
GND    <--> GND (Ground)
+5V    <--> VDD (Optional, if powering from Aardvark)
```

## API Return Codes

- 0: Success
- 1: General error
- 2: Device not found
- 3: Communication error
- 4: PEC error

## Advanced Usage

### Custom Scripts
Integrate with Python scripts:

```python
import subprocess

# Read voltage from TSP_CORE
result = subprocess.run(
    ['python3', 'powertool.py', 'TSP_CORE', 'READ_VOUT'],
    capture_output=True, text=True
)
voltage = result.stdout.strip().split()[-1]  # Extract value
```

### Batch Operations
```bash
# Test all commands on both rails
for rail in TSP_CORE TSP_C2C; do
    for cmd in READ_VOUT READ_IOUT READ_TEMPERATURE_1; do
        python3 powertool.py $rail $cmd
    done
done
```

## License and Support

This tool is provided as-is for PMBus development and testing.
For bugs or feature requests, please file an issue on the project repository.