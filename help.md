# PMBus Tool — Extended Help

A fast PMBus read/write + logger for Aardvark I²C adapters.

## Quick Start

1. Connect the Aardvark to your DUT (I²C master mode).
2. Power the DUT; if needed, enable target power with `--power-target`.
3. Install dependencies:
   ```bash
   pip install PyYAML
   # Also install Total Phase Aardvark drivers
   ```

## Commands

### Scan
Find all I²C devices on the bus:
```bash
python pmbus_tool.py scan
python pmbus_tool.py scan --port 0 --bitrate-khz 100
```

### Read
Read a single PMBus register:
```bash
# Read by command name (from commands.yaml)
python pmbus_tool.py read --addr 0x50 --cmd READ_VOUT

# Read by hex code
python pmbus_tool.py read --addr 0x50 --cmd 0x8B

# With PEC verification
python pmbus_tool.py read --addr 0x50 --cmd READ_VOUT --pec

# Force specific format
python pmbus_tool.py read --addr 0x50 --cmd 0x8B --fmt linear16 --exponent -13

# Block read
python pmbus_tool.py read --addr 0x50 --cmd MFR_MODEL --fmt block
```

### Write
Write a PMBus register:
```bash
# Write voltage command (12.5V)
python pmbus_tool.py write --addr 0x50 --cmd VOUT_COMMAND --value 12.5

# Write raw hex value
python pmbus_tool.py write --addr 0x50 --cmd 0x21 --value 0x199A

# With PEC
python pmbus_tool.py write --addr 0x50 --cmd VOUT_COMMAND --value 12.5 --pec
```

### Monitor
Continuously monitor multiple registers:
```bash
# Monitor voltage and current
python pmbus_tool.py monitor --addr 0x50 --regs READ_VOUT,READ_IOUT --interval-ms 100

# Save to CSV with 1000 samples
python pmbus_tool.py monitor --addr 0x50 --regs READ_VOUT,READ_IOUT,READ_TEMPERATURE_1 \
    --csv output.csv --samples 1000

# Fast mode with stdout output
python pmbus_tool.py monitor --addr 0x50 --regs STATUS_WORD,READ_VOUT,READ_IOUT \
    --fast --stdout --interval-ms 50

# Monitor for 60 seconds
python pmbus_tool.py monitor --addr 0x50 --regs READ_VOUT,READ_PIN \
    --duration-s 60 --csv power_log.csv
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

Edit `commands.yaml` to define your device's registers:

```yaml
READ_VOUT:
  code: 0x8B
  transaction: word  # byte/word/block
  format:
    type: linear16
    exponent: -13
  unit: V

CUSTOM_REG:
  code: 0xD0
  transaction: word
  format:
    type: direct
    m: 0.5
    b: 0
    R: -3
  unit: A
```

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
python pmbus_tool.py monitor --addr 0x58 \
    --regs READ_VIN,READ_VOUT,READ_IIN,READ_IOUT,READ_PIN,READ_POUT \
    --csv efficiency.csv --interval-ms 250
```

### Thermal Testing
```bash
# Log all temperature sensors
python pmbus_tool.py monitor --addr 0x50 \
    --regs READ_TEMPERATURE_1,READ_TEMPERATURE_2,OT_FAULT_LIMIT \
    --csv thermal.csv --duration-s 3600
```

### Fault Analysis
```bash
# Fast status monitoring
python pmbus_tool.py monitor --addr 0x50 \
    --regs STATUS_WORD,STATUS_VOUT,STATUS_IOUT,STATUS_TEMPERATURE \
    --fast --interval-ms 10 --stdout
```

### Production Test
```bash
# Read device info
for cmd in MFR_ID MFR_MODEL MFR_REVISION MFR_SERIAL; do
    python pmbus_tool.py read --addr 0x50 --cmd $cmd
done
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
The tool outputs JSON for easy scripting:

```python
import subprocess
import json

result = subprocess.run(
    ['python', 'pmbus_tool.py', 'read', '--addr', '0x50', '--cmd', 'READ_VOUT'],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
voltage = float(data['value'])
```

### Batch Operations
```bash
# Read multiple registers
for reg in READ_VOUT READ_IOUT READ_TEMPERATURE_1; do
    python pmbus_tool.py read --addr 0x50 --cmd $reg
done | jq -s '.'
```

## License and Support

This tool is provided as-is for PMBus development and testing.
For bugs or feature requests, please file an issue on the project repository.