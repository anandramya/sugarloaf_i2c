# PMBus Tool — Extended Help

A fast, production-grade PMBus command-line tool for Total Phase Aardvark I²C adapters.

## Quick Start

1. Connect the Aardvark to your PMBus device (I²C master mode)
2. Power the device; if needed, enable target power with `--power-target`
3. Install dependencies:
   ```bash
   pip install PyYAML aardvark_py
   # Also install Total Phase Aardvark drivers from totalphase.com
   ```

## Commands

### Scan
Find all I²C devices on the bus (0x20-0x7F range):
```bash
python3 Sugarloaf_I2C_ver2.py scan
python3 Sugarloaf_I2C_ver2.py scan --port 0 --bitrate-khz 100
```

### Read
Read a single PMBus register:
```bash
# Read by rail and command name
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT
python3 Sugarloaf_I2C_ver2.py TSP_C2C READ_IOUT

# Read by address and command
python3 Sugarloaf_I2C_ver2.py --addr 0x5C --cmd READ_VOUT

# With PEC verification
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT --pec

# Read status registers
python3 Sugarloaf_I2C_ver2.py TSP_CORE STATUS_WORD
```

### Write
Write a PMBus register:
```bash
# Write voltage command
python3 Sugarloaf_I2C_ver2.py TSP_CORE VOUT_COMMAND --value 1.8

# Clear faults
python3 Sugarloaf_I2C_ver2.py TSP_CORE CLEAR_FAULTS

# Set page for multi-rail devices
python3 Sugarloaf_I2C_ver2.py --addr 0x5C PAGE --value 1
```

### Monitor
Continuously monitor multiple registers:
```bash
# Monitor voltage and current
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT,READ_IOUT --monitor --interval 100

# Save to CSV with timestamps
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT,READ_IOUT,READ_TEMPERATURE_1 \
    --csv --interval 100 --samples 1000

# Monitor both rails simultaneously
python3 Sugarloaf_I2C_ver2.py TSP_CORE,TSP_C2C READ_VOUT,READ_IOUT \
    --csv multi_rail.csv --interval 50

# Monitor for specific duration
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT,READ_PIN \
    --monitor --duration 60 --csv power_log.csv
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

The tool includes built-in support for standard PMBus commands and MPS-specific registers. Key registers are defined in the PMBusDict within Sugarloaf_I2C_ver2.py:

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

## Examples

### Power Supply Monitoring
```bash
# Monitor efficiency
python3 Sugarloaf_I2C_ver2.py TSP_CORE \
    READ_IIN,READ_PIN,READ_VOUT,READ_IOUT,READ_POUT \
    --csv efficiency.csv --interval 250
```

### Thermal Testing
```bash
# Log temperature with peak detection
python3 Sugarloaf_I2C_ver2.py TSP_CORE \
    READ_TEMPERATURE_1,MFR_TEMP_PEAK \
    --csv thermal.csv --monitor --duration 3600
```

### Fault Analysis
```bash
# Fast status monitoring
python3 Sugarloaf_I2C_ver2.py TSP_CORE \
    STATUS_WORD,STATUS_VOUT,STATUS_IOUT,STATUS_TEMPERATURE \
    --monitor --interval 10
```

### Test All Commands
```bash
# Run comprehensive test suite
python3 test_all_pmbus_commands.py
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
    ['python3', 'Sugarloaf_I2C_ver2.py', 'TSP_CORE', 'READ_VOUT'],
    capture_output=True, text=True
)
voltage = result.stdout.strip().split()[-1]  # Extract value
```

### Batch Operations
```bash
# Test all commands on both rails
for rail in TSP_CORE TSP_C2C; do
    for cmd in READ_VOUT READ_IOUT READ_TEMPERATURE_1; do
        python3 Sugarloaf_I2C_ver2.py $rail $cmd
    done
done
```

## License and Support

This tool is provided as-is for PMBus development and testing.
For bugs or feature requests, please file an issue on the project repository.