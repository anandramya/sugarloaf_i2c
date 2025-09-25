# PMBus Tool

A fast, production-grade PMBus command-line tool for Total Phase Aardvark I²C adapters. Supports continuous monitoring, data logging, and all standard PMBus formats with selectable slave target addresses for multi-device systems.

## Features

- 🚀 **High-speed monitoring** - Optimized for low-latency multi-register reads
- 📊 **CSV logging** - Buffered writes with automatic flushing
- 🔧 **Full PMBus support** - Linear11, Linear16, Direct formats with PEC
- 🔍 **Device scanning** - Quick I²C bus enumeration (0x20-0x7F address range)
- ⚡ **Fast mode** - Optimized repeated-start transactions up to 1MHz
- 📖 **YAML configuration** - Easy device register mapping
- 🎯 **Multi-target support** - Monitor multiple slave devices simultaneously
- 📍 **Selectable addresses** - Dynamic slave address configuration (0x20-0x7F)

## Quick Start



### Installation

```bash
# Clone the repository
git clone <repository>
cd pmbus_tool

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python pmbus_tool.py --help
```

### Basic Usage

```bash
# Scan for I²C devices (0x20-0x7F range)
python pmbus_tool.py scan

# Read voltage output from specific address
python pmbus_tool.py read --addr 0x5C --cmd READ_VOUT

# Monitor multiple registers
python pmbus_tool.py monitor --addr 0x5C --regs READ_VOUT,READ_IOUT --interval-ms 100

# Save to CSV with 1000 samples
python pmbus_tool.py monitor --addr 0x5C --regs READ_VOUT,READ_IOUT,READ_TEMPERATURE_1 \
    --csv output.csv --samples 1000

# Monitor multiple devices simultaneously
python pmbus_tool.py monitor --addr 0x5C,0x40,0x41 --regs READ_VOUT,READ_IOUT \
    --csv multi_device.csv --interval-ms 50
```

## Command Reference

### scan
Find all I²C devices on the bus:
```bash
python pmbus_tool.py scan [--port PORT] [--bitrate-khz RATE]
```

### read
Read a single PMBus register:
```bash
python pmbus_tool.py read --addr ADDR --cmd CMD [--pec] [--fmt FORMAT]
```

Options:
- `--addr`: Device I²C address (e.g., 0x50)
- `--cmd`: Register name or hex code (e.g., READ_VOUT or 0x8B)
- `--pec`: Enable PEC verification
- `--fmt`: Override format (linear11, linear16, direct, raw_byte, raw_word, block)

### write
Write to a PMBus register:
```bash
python pmbus_tool.py write --addr ADDR --cmd CMD --value VALUE [--pec]
```

### monitor
Continuously monitor multiple registers:
```bash
python pmbus_tool.py monitor --addr ADDR --regs REG1,REG2,... [OPTIONS]
```

Options:
- `--interval-ms`: Sample interval in milliseconds (default: 100)
- `--duration-s`: Total monitoring duration in seconds
- `--samples`: Number of samples to collect
- `--csv FILE`: Save to CSV file
- `--stdout`: Print CSV to stdout
- `--fast`: Enable fast mode (higher bitrate, optimized reads)
- `--pec`: Enable PEC verification

## Supported Slave Addresses

The tool supports the full PMBus address range (0x20-0x7F). Common address ranges for MPS controllers:

| Address Range | Typical Usage |
|--------------|--------------|
| 0x20-0x2F | Default range for many MPS controllers |
| 0x40-0x4F | Alternative address range |
| 0x50-0x5F | Common for voltage regulators |
| 0x5C | Default for MP29816-C and similar controllers |
| 0x60-0x6F | Extended address range |
| 0x70-0x7F | High address range |

Address configuration methods:
- **Hardware**: Set via ADDR pin resistor (see datasheet)
- **Software**: Configure via MFR_ADDR_PMBUS register
- **Page-based**: Use PAGE command (0x00) for multi-rail devices

## MP29816-C Specific Commands

The tool includes support for MPS MP29816-C dual-loop 16-phase controller:

### Key Telemetry Commands
| Command | Code | Description | Format |
|---------|------|-------------|--------|
| READ_VIN_SENSE | 0x87 | Input voltage sensing | Linear11 |
| READ_VOUT_PMBUS_R1 | 0x8B | Rail 1 output voltage | VID_STEP |
| READ_VOUT_PMBUS_R2 | 0x8B | Rail 2 output voltage | VID_STEP |
| READ_IOUT_PMBUS_R1 | 0x8C | Rail 1 output current | Linear11 |
| READ_IOUT_PMBUS_R2 | 0x8C | Rail 2 output current | Linear11 |
| READ_TEMPERATURE_PMBUS_R1 | 0x8D | Rail 1 temperature | 1°C/LSB |
| READ_PIN_EST_PMBUS | 0x97 | Estimated input power | Linear11 |
| READ_POUT_PMBUS | 0x96 | Output power | Linear11 |

### Fault Status Registers
| Register | Code | Description |
|----------|------|-------------|
| STATUS_BYTE | 0x78 | Summary fault status |
| STATUS_WORD | 0x79 | Detailed fault status |
| STATUS_VOUT | 0x7A | Output voltage faults |
| STATUS_IOUT | 0x7B | Output current faults |
| STATUS_INPUT | 0x7C | Input faults |
| STATUS_TEMPERATURE | 0x7D | Temperature faults |
| STATUS_MFR_SPECIFIC | 0x80 | Manufacturer specific faults |

### Phase Current Monitoring
The MP29816-C supports individual phase current monitoring via MFR_REG_ACCESS (0xD8):
- PHASE1_Current through PHASE16_Current (0x0C00-0x0C0F)

## Configuration

Edit `commands.yaml` to define your device's register map:

```yaml
READ_VOUT:
  code: 0x8B
  transaction: word
  format:
    type: linear16
    exponent: -13
  unit: V

READ_IOUT:
  code: 0x8C
  transaction: word
  format:
    type: linear16
    exponent: -10
  unit: A
```

### Supported Formats

- **Linear11**: 5-bit exponent + 11-bit mantissa
- **Linear16**: 16-bit mantissa with fixed exponent
- **Direct**: Y = (m × X + b) × 10^R
- **Raw**: Uninterpreted byte/word values
- **Block**: Variable-length data blocks

## Examples

### Multi-Device Fast Logging (MP29816-C Controller)
```bash
# Monitor dual-loop 16-phase controller with selectable addresses
python pmbus_tool.py monitor \
    --addr 0x5C --page 0 --name "Rail1_VCORE" \
    --addr 0x5C --page 1 --name "Rail2_VDDQ" \
    --regs READ_VOUT,READ_IOUT,READ_TEMPERATURE_1,STATUS_WORD \
    --csv mp29816_telemetry.csv --interval-ms 10 --fast
```

### Power Supply Efficiency Monitoring
```bash
python pmbus_tool.py monitor --addr 0x5C \
    --regs READ_VIN,READ_VOUT,READ_IIN,READ_IOUT,READ_PIN,READ_POUT \
    --csv efficiency.csv --interval-ms 250
```

### Thermal Testing with Peak Detection
```bash
python pmbus_tool.py monitor --addr 0x5C \
    --regs READ_TEMPERATURE_1,READ_TEMPERATURE_2,MFR_TEMP_PEAK \
    --csv thermal.csv --duration-s 3600
```

### Fault Analysis with Phase Current Monitoring
```bash
# Monitor fault status and phase currents
python pmbus_tool.py monitor --addr 0x5C \
    --regs STATUS_WORD,STATUS_VOUT,STATUS_IOUT,STATUS_TEMPERATURE,STATUS_MFR_SPECIFIC \
    --fast --interval-ms 10 --stdout
```

### Device Information and Configuration
```bash
# Read device identification
for cmd in MFR_ID MFR_MODEL MFR_REVISION MFR_SERIAL; do
    python pmbus_tool.py read --addr 0x5C --cmd $cmd
done

# Clear faults on all devices
for addr in 0x5C 0x40 0x41; do
    python pmbus_tool.py write --addr $addr --cmd CLEAR_FAULTS
done
```

### High-Speed Multi-Rail Monitoring
```bash
# Monitor multiple voltage rails at maximum speed
python pmbus_tool.py monitor \
    --targets 0x20:VDD_CPU,0x21:VDD_SOC,0x22:VDD_MEM,0x23:VDD_IO \
    --regs READ_VOUT,READ_IOUT,READ_DUTY,STATUS_BYTE \
    --interval-ms 5 --fast --csv rails_monitor.csv
```

## Fast Logging Implementation

### Architecture for High-Speed Multi-Device Logging

The tool implements several optimizations for fast PMBus logging:

1. **Batch Register Reads**: Combine multiple register reads into single I2C transactions
2. **Asynchronous Logging**: Separate data acquisition from file I/O using threading
3. **Memory Buffering**: Pre-allocate buffers to avoid runtime allocations
4. **Optimized I2C Timing**: Use repeated-start conditions and minimal delays

### Example: Fast Multi-Device Logger

```python
from powertool import PowerToolI2C
import csv
import time
import threading
from collections import deque

class FastPMBusLogger:
    def __init__(self, devices, sample_rate_ms=10):
        self.i2c = PowerToolI2C()
        self.devices = devices  # List of {'addr': 0x5C, 'name': 'VR1', 'page': 0}
        self.sample_rate = sample_rate_ms / 1000.0
        self.data_buffer = deque(maxlen=10000)
        self.running = False

    def read_device_telemetry(self, device):
        """Read telemetry from a single device"""
        addr = device['addr']
        page = device.get('page', 0)

        # Set page if multi-rail device
        if page > 0:
            self.i2c.Page(page)

        # Read all telemetry in optimized sequence
        data = {
            'timestamp': time.time(),
            'device': device['name'],
            'address': hex(addr),
            'page': page,
            'vout': self.i2c.Read_Vout(page),
            'iout': self.i2c.Read_Iout(page),
            'temp': self.i2c.Read_Temp(page),
            'status': self.i2c.i2c_read16PMBus(page, 0x79)  # STATUS_WORD
        }
        return data

    def acquisition_loop(self):
        """High-speed data acquisition thread"""
        while self.running:
            start_time = time.time()

            # Read all devices in sequence
            for device in self.devices:
                try:
                    data = self.read_device_telemetry(device)
                    self.data_buffer.append(data)
                except Exception as e:
                    print(f"Error reading {device['name']}: {e}")

            # Maintain sample rate
            elapsed = time.time() - start_time
            if elapsed < self.sample_rate:
                time.sleep(self.sample_rate - elapsed)

    def start_logging(self, csv_file):
        """Start fast logging to CSV file"""
        self.running = True
        self.csv_file = csv_file

        # Start acquisition thread
        self.acq_thread = threading.Thread(target=self.acquisition_loop)
        self.acq_thread.start()

        # Start logging thread
        self.log_thread = threading.Thread(target=self.logging_loop)
        self.log_thread.start()

    def logging_loop(self):
        """File writing thread"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = None
            while self.running or self.data_buffer:
                if self.data_buffer:
                    data = self.data_buffer.popleft()

                    # Initialize CSV writer with headers
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=data.keys())
                        writer.writeheader()

                    writer.writerow(data)

                    # Flush every 100 rows for safety
                    if len(self.data_buffer) % 100 == 0:
                        f.flush()
                else:
                    time.sleep(0.01)

# Usage example
devices = [
    {'addr': 0x5C, 'name': 'CPU_VCORE', 'page': 0},
    {'addr': 0x5C, 'name': 'CPU_VDDQ', 'page': 1},
    {'addr': 0x40, 'name': 'SOC_VDD', 'page': 0},
    {'addr': 0x41, 'name': 'MEM_VDD', 'page': 0}
]

logger = FastPMBusLogger(devices, sample_rate_ms=10)
logger.start_logging('fast_telemetry.csv')
```

## Performance

The tool is optimized for high-speed monitoring:

- **Repeated-start transactions** minimize bus overhead
- **Buffered CSV writes** with 100-row batches
- **Pre-built command frames** avoid per-iteration allocations
- **Fast mode** supports up to 1MHz I²C clock
- **Minimal latency** - typically <5ms per multi-register read

### Benchmarks

| Configuration | Devices | Registers | Sample Rate | I2C Speed |
|--------------|---------|-----------|-------------|-----------|
| Single Device | 1 | 4 | 100ms | 400kHz |
| Multi-Rail | 2 | 4 | 50ms | 400kHz |
| Fast Mode | 4 | 3 | 20ms | 1MHz |
| Ultra-Fast | 8 | 2 | 10ms | 1MHz |

## Hardware Connections

```
Aardvark    PMBus Device
--------    ------------
SCL    <--> SCL (Clock)
SDA    <--> SDA (Data)
GND    <--> GND (Ground)
+5V    <--> VDD (Optional)
```

## Development

### Running Tests
```bash
make test
```

### Code Linting
```bash
make lint
```

### Project Structure
```
pmbus_tool/
├── pmbus_tool.py      # Main CLI application
├── pmbus_core.py      # PMBus protocol implementation
├── aardvark_i2c.py    # Aardvark adapter wrapper
├── commands.yaml      # Device register configuration
├── help.md           # Extended documentation
├── requirements.txt   # Python dependencies
├── Makefile          # Build automation
└── tests/
    └── test_basic.py  # Unit tests
```

## Troubleshooting

### No devices found
- Check I²C connections (SDA, SCL, GND)
- Verify pullups are enabled (`--pullups`)
- Try slower bitrate (`--bitrate-khz 100`)
- Check target power (`--power-target`)

### PEC errors
- Some devices don't support PEC
- Try without `--pec` flag
- Check signal integrity

### Import error for aardvark_py
- Install Total Phase Aardvark software
- Copy `aardvark_py.py` to your Python path
- Or install via: `pip install aardvark_py`

## API for Scripting

The tool outputs JSON for easy integration:

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

## License

This tool is provided as-is for PMBus development and testing.

## Support

For detailed documentation, use:
```bash
python pmbus_tool.py --help-long
```

For issues or feature requests, please file an issue in the project repository.
