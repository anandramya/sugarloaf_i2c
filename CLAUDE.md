# CLAUDE.md - PMBus Tool Project Documentation

## Project Overview
PMBus monitoring and control tool for Total Phase Aardvark I²C adapters, specifically designed for Sugarloaf power management ICs. This tool provides high-speed PMBus telemetry logging, multi-device monitoring, and comprehensive command support.

## Main Files
- **Sugarloaf_I2C_ver2.py**: Core PMBus interface implementation with Aardvark adapter
- **test_all_pmbus_commands.py**: Comprehensive test suite for PMBus commands
- **help.md**: User documentation and command reference
- **README.md**: Project overview and quick start guide

## Key Features
- High-speed PMBus monitoring (up to 1MHz I²C)
- Multi-device/multi-rail support
- CSV data logging with buffered writes
- Support for Linear11, Linear16, Direct formats
- PEC (Packet Error Checking) support
- Phase current monitoring (16 phases)

## PMBus Commands Supported
### Standard Commands
- READ_VOUT (0x8B), READ_IOUT (0x8C), READ_TEMPERATURE_1 (0x8D)
- READ_PIN (0x97), READ_POUT (0x96), READ_IIN (0x89)
- STATUS_BYTE (0x78), STATUS_WORD (0x79)
- STATUS_VOUT (0x7A), STATUS_IOUT (0x7B), STATUS_INPUT (0x7C)
- VOUT_MODE (0x20), VOUT_COMMAND (0x21)
- PAGE (0x00), CLEAR_FAULTS (0x03)

### MFR Specific Commands
- MFR_VR_CONFIG (0x67), MFR_TEMP_PEAK (0xD1), MFR_IOUT_PEAK (0xD7)
- MFR_REG_ACCESS (0xD8) for extended register access
- Phase current monitoring (PHASE1-16_Current: 0x0C00-0x0C0F)

## Target Devices
- **Primary**: MP29816-C dual-loop 16-phase controller
- **Default Address**: 0x5C (configurable via ADDR pin)
- **Address Range**: 0x20-0x7F (full PMBus range)
- **Rails**: TSP_CORE, TSP_C2C (multi-page support)

## Usage Examples
```bash
# Basic voltage read
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT

# Monitor multiple parameters with CSV logging
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT,READ_IOUT,READ_TEMPERATURE_1 --csv --interval 100

# Test all commands on both rails
python3 test_all_pmbus_commands.py
```

## Testing Commands
```bash
# Run comprehensive PMBus command tests
python3 test_all_pmbus_commands.py

# Test specific rail
python3 Sugarloaf_I2C_ver2.py TSP_CORE STATUS_WORD

# Continuous monitoring with data logging
python3 Sugarloaf_I2C_ver2.py TSP_CORE READ_VOUT --monitor --csv output.csv
```

## Hardware Requirements
- Total Phase Aardvark I²C/SPI Host Adapter
- PMBus-compliant power management IC
- Proper I²C connections (SDA, SCL, GND)
- Pull-up resistors (or enable internal pull-ups)

## Dependencies
- Python 3.6+
- aardvark_py (Total Phase Python API)
- PyYAML (for configuration)
- Standard libraries: csv, datetime, argparse

## Performance Notes
- Default I²C bitrate: 400 kHz
- Fast mode available: up to 1 MHz
- Buffered CSV writes (100-row batches)
- Optimized repeated-start transactions
- Typical latency: <5ms per multi-register read

## Common Issues and Solutions
1. **No Aardvark found**: Check USB connection, install drivers
2. **PEC errors**: Some devices don't support PEC, disable with --no-pec
3. **Address not responding**: Verify device address, check pull-ups
4. **Import errors**: Install aardvark_py from Total Phase

## Data Format
- CSV output includes timestamp, rail name, command, and value
- Linear11/16 values automatically converted to engineering units
- Status registers decoded to hex with fault bits
- Phase currents reported in Amperes

## Project Structure
```
pmbustool/
├── Sugarloaf_I2C_ver2.py    # Main PMBus interface
├── test_all_pmbus_commands.py # Test suite
├── data/                     # CSV output directory
├── help.md                   # Extended documentation
├── README.md                 # Project overview
└── CLAUDE.md                 # This file - AI assistant reference
```

## Important Constants
- SLAVE_ADDR: 0x5C (default)
- I2C_BITRATE: 400 kHz
- ENDIAN: 0 (Little endian)
- CSV buffer size: 100 rows
- Default monitor interval: 100ms

## Development Notes
- Uses aardvark_py library for hardware interface
- Implements PMBus protocol with PEC support
- Handles Linear11/Linear16 format conversions
- Supports multi-page devices (dual-rail controllers)
- Thread-safe CSV logging for high-speed monitoring

## Future Enhancements
- YAML configuration for custom devices
- GUI interface for real-time monitoring
- Extended manufacturer-specific commands
- Automated fault detection and alerting
- Power efficiency calculations