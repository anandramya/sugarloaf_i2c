# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
PowerTool - PMBus monitoring and control tool for remote I²C access via serial connection. Uses STM32MP25 microcontroller running embedded Linux to interface with PMBus devices. Provides high-speed telemetry logging and voltage control for power management ICs, specifically the MP29816-C dual-loop 16-phase controller.

**Important**: This tool uses a **serial I²C driver** (not Aardvark). The PMBus device is on **I²C bus 1** (not bus 0).

## Quick Start - Simple Usage

```bash
# Make the tool executable
chmod +x powertool.py

# Test connection and read both rails
./powertool.py test

# Read voltage from TSP_CORE rail
./powertool.py TSP_CORE READ_VOUT

# Read current from TSP_C2C rail
./powertool.py TSP_C2C READ_IOUT

# Read multiple telemetry values at once
./powertool.py TSP_CORE READ_VOUT READ_IOUT READ_TEMP READ_DIE_TEMP

# Set voltage to 0.8V on TSP_CORE
./powertool.py TSP_CORE VOUT_COMMAND 0.8

# Start continuous logging (creates CSV in data/ directory)
./powertool.py TSP_CORE READ_VOUT READ_IOUT log
# Press Ctrl+C to stop logging

# Read status registers
./powertool.py TSP_CORE STATUS_WORD
```

**First-time setup**:
1. Connect USB-to-serial adapter to /dev/ttyUSB0 (115200 baud)
2. Ensure STM32MP25 is powered and connected via I2C bus 1 to PMBus device at 0x5C
3. Install dependencies: `pip install pyserial`
4. Run test: `./powertool.py test`

## Quick Start - PCIe I2C Version

```bash
# Make the tool executable
chmod +x powertool_pcie.py

# Test connection and read both rails
./powertool_pcie.py --test

# Read voltage from TSP_CORE rail
./powertool_pcie.py --rail TSP_CORE --cmd READ_VOUT

# Read current from TSP_C2C rail
./powertool_pcie.py --rail TSP_C2C --cmd READ_IOUT

# Read die temperature
./powertool_pcie.py --rail TSP_CORE --cmd READ_DIE_TEMP

# Set voltage to 0.8V on TSP_CORE
./powertool_pcie.py --rail TSP_CORE --cmd VOUT_COMMAND --value 0.8

# Read status word
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
```

**Requirements**:
- i2ctool binary in current directory (./i2ctool)
- PCIe device at 0000:c1:00.0
- I2C bus 1 (critical - not bus 0)
- PMBus device at address 0x5C

## Core Architecture

### Main Components

- **pmbus_common.py**: Shared PMBus library used by both serial and PCIe implementations (~460 lines)
  - **PMBusDict**: Register definitions for all PMBus commands (standard, manufacturer-specific, phase currents)
  - **Parsing Functions**: Standalone data format converters
    - `parse_vout_mode()` - Extract exponent from VOUT_MODE register
    - `parse_linear11()` - Convert Linear11 format (IOUT, TEMP, power)
    - `parse_linear16()` - Convert Linear16 format (VOUT)
    - `parse_die_temp()` - Voltage-based temperature conversion
    - `calculate_vout_command()` - Calculate VOUT_COMMAND value
  - **STATUS Register Decoders**: Human-readable fault/warning decoding for all major STATUS registers
    - **STATUS_WORD (0x79)**: 16-bit comprehensive status
      - `decode_status_word()` - Parse all 16 bits into dictionary with descriptions
      - `format_status_word()` - Format as human-readable string with ✓/✗ indicators
      - Decodes: VOUT, IOUT, INPUT, POWER_GOOD_N, OFF, VOUT_OV_FAULT, IOUT_OC_FAULT, VIN_UV_FAULT, TEMPERATURE, CML, etc.
    - **STATUS_VOUT (0x7A)**: 8-bit output voltage status
      - `decode_status_vout()` - Parse VOUT-specific faults (LINE_FLOAT, VOUT_SHORT)
      - `format_status_vout()` - Format with ✓/✗ indicators
    - **STATUS_IOUT (0x7B)**: 8-bit output current status
      - `decode_status_iout()` - Parse IOUT-specific faults (IOUT_OC_FAULT, OCP_UV_FAULT, IOUT_OC_WARN)
      - `format_status_iout()` - Format with ✓/✗ indicators and WARN/FAULT distinction
  - **PMBusCommands Mixin**: Common command implementations for both tools
    - `Read_VOUT_MODE()`, `Read_Vout()`, `Read_Iout()`, `Read_Temp()`, `Read_Die_Temp()`, `Read_Status_Word()`, `Write_Vout_Command()`
    - Classes using this mixin must implement: `i2c_read8PMBus()`, `i2c_read16PMBus()`, `i2c_write8PMBus()`, `i2c_write16PMBus()`
  - **Benefit**: Single source of truth - changes to PMBus logic apply to both tools automatically

- **powertool_pcie.py**: PCIe-based implementation (~365 lines) using i2ctool binary
  - **Class**: `PowerToolPCIe(PMBusCommands)` - inherits PMBus commands from common library
  - Hardware layer: PCIe I2C access via i2ctool binary to device at 0000:c1:00.0
  - I2C communication: `_run_i2c_command()`, `i2c_read_bytes()`, `i2c_write_bytes()` with JSON parsing
  - PMBus interface: Implements required `i2c_read8PMBus()`, `i2c_read16PMBus()`, `i2c_write8PMBus()`, `i2c_write16PMBus()` methods
  - CLI: Argparse-based interface (`--rail`, `--cmd`, `--test` modes)
  - **Critical**: Requires `I2C_BUS_NUM = 1` (not 0) for this hardware

- **powertool.py**: Serial-based implementation (2680 lines) containing the `PowerToolI2C` class and CLI interface
  - Hardware layer: Serial I²C driver interface via `serial_i2c_driver` module (connects to STM32MP25)
  - Initialization: Handles serial connection, authentication, and GPIO setup (sets PB1=1 to enable I2C)
  - PMBus protocol: Implements read/write operations with page-based addressing
  - Data conversion: Linear11/Linear16 format handling with VID step calculations
  - CLI: Argparse-based command interface supporting multiple usage patterns
  - **Note**: This file needs refactoring to use pmbus_common.py (currently has duplicated code)

- **serial_i2c_driver.py**: Python wrapper for sending i2c-tools commands (i2cget, i2cset) over serial connection
  - Not included in repository but required dependency for powertool.py
  - Provides `SerialI2CDriver` class with `i2cget()`, `i2cset()`, and `parse_i2cget_response()` methods

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

**PMBusDict** (in `pmbus_common.py`): Dictionary mapping command names to register addresses
- Standard PMBus commands (0x00-0x97)
- Manufacturer-specific commands (0x67, 0xD1-0xD8)
- Phase current registers (0x0C00-0x0C0F)
- Shared by both powertool.py and powertool_pcie.py

**Rail Mapping**:
- TSP_CORE → Page 0 (primary voltage rail)
- TSP_C2C → Page 1 (secondary voltage rail)

### Important Implementation Details

**Serial I2C Communication** (lines 116-142, 204-312):
- Uses `SerialI2CDriver` to send Linux i2c-tools commands (i2cget, i2cset) over UART
- All operations go through serial connection to STM32MP25 running embedded Linux
- Response parsing extracts hex values from shell output (e.g., "0x38\nroot@stm32mp25:~#")
- Timing is critical - delays of 0.05-0.3s between operations to prevent buffer overflow

**GPIO Initialization** (`I2Cinit`, lines 143-201):
- Checks if `gpioset PB1=1` is already running using `pgrep`
- Starts gpioset in background if not running (enables I2C on hardware)
- Handles serial buffer clearing to remove login prompts and command echoes
- This is required before any I2C operations can succeed

**Voltage Reading** (`Read_Vout`, lines 448-465):
- Reads VOUT_MODE register first to get exponent (5-bit two's complement in bits [0:4])
- Applies Linear16 formula: `voltage = mantissa × 2^exponent`
- Alternative methods `Read_Vout_Rail1()` and `Read_Vout_Rail2()` for specific rails
- Debug print on line 464 is commented out for logging performance

**Multi-Page Device Support** (`i2c_write8PMBus`, `i2c_read16PMBus`):
- Always writes PAGE register (0x00) before accessing device
- Page 0 = TSP_CORE, Page 1 = TSP_C2C
- Critical for dual-rail controllers
- Each page write adds ~0.1s delay

**Data Format Conversions**:
- `Linear11`: 5-bit exponent [15:11] + 11-bit mantissa [10:0], used for IOUT, temperature
- `Linear16`: 16-bit mantissa with fixed exponent from VOUT_MODE register
- `Read_VOUT_MODE()` (lines 467-481): Extracts exponent as 5-bit two's complement

## Common Development Commands

### Running the Serial Tool (powertool.py)
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

### Running the PCIe Tool (powertool_pcie.py)
```bash
# Make executable (first time only)
chmod +x powertool_pcie.py

# Test hardware connection
./powertool_pcie.py --test

# Read single telemetry commands
./powertool_pcie.py --rail TSP_CORE --cmd READ_VOUT
./powertool_pcie.py --rail TSP_C2C --cmd READ_IOUT
./powertool_pcie.py --rail TSP_CORE --cmd READ_TEMP
./powertool_pcie.py --rail TSP_CORE --cmd READ_DIE_TEMP

# Read status
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
./powertool_pcie.py --rail TSP_C2C --cmd READ_STATUS  # Alias for STATUS_WORD

# Set voltage
./powertool_pcie.py --rail TSP_CORE --cmd VOUT_COMMAND --value 0.8

# Specify custom PCIe device or I2C address
./powertool_pcie.py -d 0000:c1:00.0 -a 0x5C -b 1 --rail TSP_CORE --cmd READ_VOUT
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

**Connection Settings** (lines 93-98):
- `SLAVE_ADDR = 0x5C` (PMBus device address)
- `I2C_BUS = 0` (⚠️ **CRITICAL**: The actual hardware uses bus 1, but this constant says 0 - verify before use)
- `SERIAL_PORT = "/dev/ttyUSB0"` (USB-to-serial adapter)
- `SERIAL_BAUD = 115200` (baud rate)
- `SERIAL_PASSWORD = "root"` (authentication - not currently used)
- `ENDIAN = 0` (little endian)

**Physical Connection Chain**:
```
Host PC <--USB--> Serial Adapter <--UART--> STM32MP25 <--I2C Bus 1--> PMBus Device (0x5C)
```

**GPIO Initialization**: The tool sets GPIO PB1=1 on the STM32MP25 to enable I2C (see `I2Cinit()` method, lines 143-201)

**Address Range**: Full PMBus range 0x20-0x7F supported

## Common Gotchas

1. **I2C Bus Number**: The PMBus device is on **bus 1**, not bus 0. The constant `I2C_BUS = 0` in the code may be incorrect - always verify which bus is being used in the actual `i2cget/i2cset` calls. Check SERIAL_I2C_USAGE.md for correct bus configuration.

2. **Serial Connection Initialization**: The tool requires careful initialization sequence:
   - Serial connection (0.5s wait)
   - Buffer clearing (removes login prompts and command echoes)
   - GPIO setup (sets PB1=1, checks if already running with `pgrep`)
   - Additional delays (0.2-0.3s) for stability

3. **Timing Requirements**: Serial I2C is much slower than native I2C adapters:
   - Command execution: ~0.3s per operation
   - Page write: additional 0.1s delay
   - Between commands: 0.05-0.2s recommended
   - Multi-command logging: 3-5 seconds per sample (see gotcha #8)

4. **Page Register**: The tool automatically sets the PAGE register before every operation. When adding new commands, ensure page-based methods use `i2c_read16PMBus(page, addr)` pattern.

5. **Byte Width for Writes**: Write operations support both 1-byte and 2-byte modes:
   - Use `i2c_write8PMBus()` for single-byte registers (VOUT_MODE, STATUS_BYTE)
   - Use `i2c_write16PMBus()` for two-byte registers (VOUT_COMMAND, STATUS_WORD)
   - Auto-detection based on value size (≤0xFF = 1 byte, >0xFF = 2 bytes)

6. **VID Step Resolution**: VOUT calculations depend on reading MFR_VID_RES_R1 to determine the correct step size. The `Read_Vout()` method handles this automatically. Note: The implementation uses `Read_VOUT_MODE()` to get exponent instead (lines 467-481).

7. **CSV Buffering**: CSV writes are buffered and flushed every 100 rows for performance. Data is also flushed on Ctrl+C for safety.

8. **Linear11 vs Linear16**: Different telemetry commands use different formats:
   - VOUT uses Linear16 with exponent from VOUT_MODE register (not VID step as CLAUDE.md previously stated)
   - IOUT, temperature, power use Linear11 (exponent embedded in data)

9. **Multi-Command Performance**: When using multi-command logging, each command requires a separate I2C transaction over serial. Performance notes:
   - Serial I2C overhead: ~700-800ms per register read
   - 3 commands: ~3-4 seconds per sample (0.3 samples/sec)
   - 5 commands: ~4-5 seconds per sample (0.2 samples/sec)
   - For faster logging, reduce the number of commands or use single-command mode
   - The `Read_Vout()` debug print statement has been commented out to reduce overhead (line 464)

10. **READ_STATUS Alias**: `READ_STATUS` is an alias for `STATUS_WORD` for convenience in multi-command operations.

11. **Serial Port Permissions**: You may need to add your user to the dialout group or set permissions: `sudo chmod 666 /dev/ttyUSB0`

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
pip install pyserial
```

The tool auto-installs `pyserial` if not found (see lines 21-33 in powertool.py).

**Required Module**: `serial_i2c_driver.py` - Not included in repository but required. This module provides:
- `SerialI2CDriver` class
- `i2cget()` and `i2cset()` methods for sending i2c-tools commands over serial
- `parse_i2cget_response()` for parsing command output

See SERIAL_I2C_USAGE.md for detailed documentation on the serial I2C driver.

## Troubleshooting

### "Could not connect to serial I2C driver"
- Check device is connected: `ls -l /dev/ttyUSB*`
- Fix permissions: `sudo chmod 666 /dev/ttyUSB0` or `sudo usermod -a -G dialout $USER`
- Verify correct port and baud rate in powertool.py (lines 95-96)
- Test with: `screen /dev/ttyUSB0 115200` (Ctrl+A then K to exit)

### "Read failed" or wrong values returned
- Verify PMBus device is on **bus 1** (not bus 0) on the STM32MP25
- Check device address is 0x5C: `i2cdetect -y 1` (run on STM32MP25)
- Ensure GPIO PB1 is set correctly (tool does this automatically)
- Check correct page is selected (0 for TSP_CORE, 1 for TSP_C2C)

### Timeout errors
- Increase timeout in serial_i2c_driver.py: `timeout=5.0`
- Increase delays in powertool.py:
  - After page writes (line ~296): `time.sleep(0.2)`
  - After byte writes (line ~242): `time.sleep(0.1)`
- Check STM32MP25 responsiveness with screen/minicom

### "ImportError: No module named serial_i2c_driver"
- This module is not in the repository but is required
- Contact maintainer for serial_i2c_driver.py
- See SERIAL_I2C_USAGE.md for API documentation

### GPIO initialization warnings
- "⚠ Warning: GPIO PB1 may not have started correctly" - usually safe to ignore if reads work
- If I2C operations fail, manually run on STM32MP25: `gpioset PB1=1 &`
- Check GPIO status: `pgrep -f "gpioset PB1=1"`

## Code Architecture and Refactoring

### Shared Library Design

The codebase uses a **shared library pattern** to eliminate code duplication between serial and PCIe implementations:

**pmbus_common.py** - Single source of truth for PMBus logic
- All PMBus register definitions (PMBusDict)
- All data format conversion functions (Linear11, Linear16, voltage-based)
- Common command implementations (Read_Vout, Read_Iout, Read_Temp, etc.)
- Mixin class pattern for easy integration

**Benefits:**
1. **Maintainability**: Changes to PMBus logic automatically apply to both tools
2. **Consistency**: Identical behavior across serial and PCIe implementations
3. **Testability**: PMBus logic can be tested independently
4. **Documentation**: Single location for PMBus specifications

### Implementation Pattern

Tools inherit from `PMBusCommands` mixin and implement the I2C transport layer:

```python
from pmbus_common import PMBusDict, PMBusCommands

class MyPMBusTool(PMBusCommands):
    """Implements specific I2C transport (serial, PCIe, etc.)"""

    def i2c_read8PMBus(self, page, reg_addr):
        """Read 8-bit register - transport specific"""
        # Implementation here

    def i2c_read16PMBus(self, page, reg_addr):
        """Read 16-bit register - transport specific"""
        # Implementation here

    def i2c_write8PMBus(self, reg_addr, value):
        """Write 8-bit value - transport specific"""
        # Implementation here

    def i2c_write16PMBus(self, page, reg_addr, value):
        """Write 16-bit value - transport specific"""
        # Implementation here

    # All PMBus commands (Read_Vout, Read_Iout, etc.) inherited from mixin
```

### Refactoring Status

✅ **Completed:**
- Created `pmbus_common.py` with shared functions and mixin class
- Refactored `powertool_pcie.py` to use shared library (~206 lines removed)
- All PCIe tool functionality verified working

⏳ **Pending:**
- Refactor `powertool.py` (serial version) to use shared library
- Expected benefit: ~200 lines of duplicated code removed

**Note**: When modifying PMBus command functions (Read_Vout, Read_Iout, etc.), edit `pmbus_common.py` to apply changes to both tools.

## Additional Documentation Files

- **pmbus_common.py**: Shared PMBus library for both serial and PCIe tools (see docstrings)
- **STATUS_DECODERS.md**: Complete guide to all STATUS register decoders (STATUS_WORD, STATUS_VOUT, STATUS_IOUT)
- **STATUS_WORD_DECODER.md**: Detailed STATUS_WORD bit decoding, fault interpretation, examples
- **REFACTORING_SUMMARY.md**: Details on code refactoring and shared library architecture
- **PCIE_I2C_USAGE.md**: Complete usage guide for PCIe version (powertool_pcie.py)
- **PMBUS_TEST_RESULTS.md**: Comprehensive test results for all PMBus commands
- **PCIE_STATUS.md**: PCIe tool development status and milestones
- **PCIE_SUCCESS.md**: PCIe tool success summary
- **SERIAL_I2C_USAGE.md**: Complete guide to serial I2C driver usage, API reference, timing requirements
- **SERIAL_I2C_README.md**: Overview of serial I2C implementation
- **QUICK_REFERENCE.md**: Fast reference for common commands and operations
- **README.md**: General project documentation (may describe different hardware setup - Aardvark vs Serial)
- **help.md**: Extended help documentation
