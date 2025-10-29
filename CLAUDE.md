# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
PowerTool - PMBus monitoring and control tool for Total Phase Aardvark I²C adapters. Provides high-speed telemetry logging and voltage control for power management ICs, specifically the MP29816-C dual-loop 16-phase controller.

## Core Architecture

### Main Components
- **powertool.py**: Single-file implementation containing the `PowerToolI2C` class and CLI interface
  - Hardware layer: Aardvark I²C adapter interface via `aardvark_py` library
  - PMBus protocol: Implements read/write operations with page-based addressing
  - Data conversion: Linear11/Linear16 format handling with VID step calculations
  - CLI: Argparse-based command interface supporting multiple usage patterns

### Command Interface Patterns
The tool supports five distinct command patterns:

1. **Rail-based commands** (primary interface):
   ```bash
   ./powertool.py [RAIL] [COMMAND] [OPTIONS]
   ./powertool.py TSP_CORE READ_VOUT
   ./powertool.py TSP_C2C VOUT_COMMAND 0.75
   ```

2. **Multi-command execution** (new):
   ```bash
   ./powertool.py [RAIL] [COMMAND1] [COMMAND2] [COMMAND3] ...
   ./powertool.py TSP_CORE READ_VOUT READ_IOUT READ_TEMP READ_DIE_TEMP
   ./powertool.py TSP_C2C READ_VOUT READ_IOUT READ_STATUS
   ```

3. **Multi-command logging** (new):
   ```bash
   ./powertool.py [RAIL] [COMMAND1] [COMMAND2] ... log [DURATION]
   ./powertool.py TSP_CORE READ_VOUT READ_IOUT READ_STATUS READ_TEMP READ_DIE_TEMP log
   ./powertool.py TSP_CORE READ_VOUT READ_IOUT log 0.5m  # 30 seconds
   ./powertool.py TSP_C2C READ_VOUT READ_IOUT READ_TEMP log 100  # 100 samples
   ```

4. **Direct hex register access** (simplified):
   ```bash
   ./powertool.py [RAIL] READ [HEX_ADDR] [BYTES]
   ./powertool.py TSP_CORE READ 0x21
   ./powertool.py TSP_CORE WRITE 0x21 0x0C00 2
   ```

5. **Legacy page-based access** (for advanced users):
   ```bash
   ./powertool.py page [0/1] [ADDRESS|COMMAND] [READ|LOG|WRITE] [BYTES|VALUE]
   ./powertool.py page 0 READ_VOUT LOG 2
   ```

### Key Data Structures

**PMBusDict** (lines 21-75): Dictionary mapping command names to register addresses
- Standard PMBus commands (0x00-0x97)
- Manufacturer-specific commands (0x67, 0xD1-0xD8)
- Phase current registers (0x0C00-0x0C0F)

**Rail Mapping**:
- TSP_CORE → Page 0 (primary voltage rail)
- TSP_C2C → Page 1 (secondary voltage rail)

### Important Implementation Details

**VID Step Calculation** (`Read_Vout`, lines 450-580):
- Reads MFR_VID_RES_R1 register to extract VID_STEP bits [12:10]
- Calculates step size using formula: 0.005 / (2^VID_STEP)
- Converts raw Linear16 data to voltage using calculated step size

**Multi-Page Device Support** (`i2c_write8PMBus`, `i2c_read16PMBus`):
- Always writes PAGE register (0x00) before accessing device
- Page 0 = TSP_CORE, Page 1 = TSP_C2C
- Critical for dual-rail controllers

**Data Format Conversions**:
- `Linear11`: 5-bit exponent [15:11] + 11-bit mantissa [10:0], see `Read_Iout` (line 620)
- `Linear16`: 16-bit mantissa with fixed exponent from VOUT_MODE, see `Read_Vout` (line 450)
- `twos_comp()`: Converts unsigned to signed for exponents (line 270)

## Common Development Commands

### Running the tool
```bash
# Make executable (first time only)
chmod +x powertool.py

# Test hardware connection
./powertool.py test

# Read single telemetry command
./powertool.py TSP_CORE READ_VOUT
./powertool.py TSP_C2C READ_IOUT

# Read multiple telemetry commands
./powertool.py TSP_CORE READ_VOUT READ_IOUT READ_TEMP READ_DIE_TEMP
./powertool.py TSP_C2C READ_VOUT READ_IOUT READ_STATUS

# Set voltage
./powertool.py TSP_CORE VOUT_COMMAND 0.8

# Continuous logging to CSV (single command)
./powertool.py TSP_CORE READ_VOUT log
./powertool.py page 0 STATUS_WORD LOG 2

# Continuous logging to CSV (multiple commands)
./powertool.py TSP_CORE READ_VOUT READ_IOUT READ_STATUS READ_TEMP READ_DIE_TEMP log
./powertool.py TSP_CORE READ_VOUT READ_IOUT log 0.5m    # Log for 30 seconds
./powertool.py TSP_C2C READ_VOUT READ_IOUT READ_TEMP log 100  # Log 100 samples

# Direct register access
./powertool.py TSP_CORE READ 0x8B      # Read READ_VOUT register
./powertool.py TSP_CORE WRITE 0x21 0x0C00 2   # Write VOUT_COMMAND
```

### Testing
```bash
# Run comprehensive test suite
./test_all_pmbus_commands.py

# Single readback test
./powertool.py test
```

### CSV Data Output
All logging modes save to `data/` directory with auto-generated timestamped filenames:
- Single command: `data/{RAIL}_{COMMAND}_{timestamp}.csv`
- Multi-command (up to 3 commands in filename): `data/{RAIL}_{CMD1}_{CMD2}_{CMD3}_{timestamp}.csv`
- Multi-command (4+ commands): `data/{RAIL}_{CMD1}_{CMD2}_{CMD3}_etc_{timestamp}.csv`
- Multi-rail: `data/pmbus_log_{timestamp}.csv`
- Direct register: `data/PAGE{page}_{command}_{timestamp}.csv`

**Multi-Command CSV Format:**
```csv
timestamp,sample_num,READ_VOUT,READ_IOUT,READ_STATUS,READ_TEMP,READ_DIE_TEMP
0.000,1,0.746094,59.062,0x9203,48.000,48.000
4.954,2,0.746094,59.312,0x9203,48.000,48.000
```
- `timestamp`: Seconds since logging started
- `sample_num`: Sequential sample number
- Each command appears as a column with its converted value

## Hardware Configuration

**Default I²C Settings** (lines 77-79):
- `SLAVE_ADDR = 0x5C` (configurable via ADDR pin)
- `I2C_BITRATE = 400` kHz
- `ENDIAN = 0` (little endian)

**Address Range**: Full PMBus range 0x20-0x7F supported

## Common Gotchas

1. **Page Register**: The tool automatically sets the PAGE register before every operation. When adding new commands, ensure page-based methods use `i2c_read16PMBus(page, addr)` pattern.

2. **Byte Width for Writes**: Write operations support both 1-byte and 2-byte modes:
   - Use `i2c_write8PMBus()` for single-byte registers (VOUT_MODE, STATUS_BYTE)
   - Use `i2c_write16PMBus()` for two-byte registers (VOUT_COMMAND, STATUS_WORD)
   - Auto-detection based on value size (≤0xFF = 1 byte, >0xFF = 2 bytes)

3. **VID Step Resolution**: VOUT calculations depend on reading MFR_VID_RES_R1 to determine the correct step size. The `Read_Vout()` method handles this automatically.

4. **CSV Buffering**: CSV writes are buffered and flushed every 100 rows for performance. Data is also flushed on Ctrl+C for safety.

5. **Linear11 vs Linear16**: Different telemetry commands use different formats:
   - VOUT uses Linear16 with VID step (exponent from MFR_VID_RES_R1)
   - IOUT, temperature, power use Linear11 (exponent embedded in data)

6. **Multi-Command Performance**: When using multi-command logging, each command requires a separate I2C transaction over serial. Performance notes:
   - Serial I2C overhead: ~700-800ms per register read
   - 3 commands: ~3-4 seconds per sample (0.3 samples/sec)
   - 5 commands: ~4-5 seconds per sample (0.2 samples/sec)
   - For faster logging, reduce the number of commands or use single-command mode
   - The `Read_Vout()` debug print statement has been commented out to reduce overhead

7. **READ_STATUS Alias**: `READ_STATUS` is an alias for `STATUS_WORD` for convenience in multi-command operations.

## PMBus Register Reference

Key registers for development:
- `0x00` PAGE - Select rail (0=TSP_CORE, 1=TSP_C2C)
- `0x20` VOUT_MODE - Voltage encoding mode (read exponent)
- `0x21` VOUT_COMMAND - Voltage setpoint (write)
- `0x29` MFR_VID_RES_R1 - VID resolution settings (bits [12:10])
- `0x79` STATUS_WORD - Detailed fault status (2 bytes)
- `0x8B` READ_VOUT - Actual output voltage (Linear16)
- `0x8C` READ_IOUT - Output current (Linear11)
- `0x8D` READ_TEMP - Temperature (Linear11)
- `0x8E` READ_DIE_TEMP - Die Temperature (1°C per LSB)
- `0xD8` MFR_REG_ACCESS - Extended register access for phase currents

## Dependencies

Install with:
```bash
pip install PyYAML
```

The `aardvark_py` module requires Total Phase Aardvark drivers from totalphase.com.
