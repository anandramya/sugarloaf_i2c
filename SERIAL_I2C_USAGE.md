# Serial I2C Driver Usage Guide

Complete documentation for PMBus monitoring via serial I2C interface with STM32MP25.

---

## Table of Contents
- [Hardware Setup](#hardware-setup)
- [Serial I2C Driver](#serial-i2c-driver)
- [PowerTool with Serial I2C](#powertool-with-serial-i2c)
- [Quick Start Examples](#quick-start-examples)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Hardware Setup

### Requirements
- **Host**: Linux system with Python 3.x
- **Microcontroller**: STM32MP25 (ursa_p1a) running embedded Linux
- **Connection**: USB-to-serial adapter (`/dev/ttyUSB0`)
- **Baud Rate**: 115200
- **I2C Device**: MP29816-C PMBus controller at address 0x5C on bus 1

### Physical Connection
```
Host PC <--USB--> Serial Adapter <--UART--> STM32MP25 <--I2C--> PMBus Device (0x5C)
```

### I2C Bus Topology
```
I2C Bus 1:
  ├── 0x09 (device)
  ├── 0x0C (device)
  ├── 0x5C (PMBus MP29816-C) ← Target device
  └── 0x6C (device)
```

**Important**: PMBus device is on **bus 1**, not bus 0.

---

## Serial I2C Driver

### Overview
`serial_i2c_driver.py` provides a Python interface to send `i2cget` and `i2cset` commands to the STM32MP25 microcontroller via serial connection.

### Basic Usage

#### 1. Initialize Driver
```python
from serial_i2c_driver import SerialI2CDriver

driver = SerialI2CDriver(
    port="/dev/ttyUSB0",
    baudrate=115200,
    timeout=3.0
)
```

#### 2. Read Single Byte
```python
# Read OPERATION register (0x01) from device 0x5C on bus 1
response = driver.i2cget(
    bus=1,
    chip_addr=0x5C,
    data_addr=0x01,
    mode='b',
    assume_yes=True
)

# Parse the response
value = driver.parse_i2cget_response(response)
print(f"OPERATION = 0x{value:02X}")
```

#### 3. Read Word (16-bit)
```python
# Read READ_VOUT register (0x8B) as word
response = driver.i2cget(
    bus=1,
    chip_addr=0x5C,
    data_addr=0x8B,
    mode='w',
    assume_yes=True
)

value = driver.parse_i2cget_response(response)
print(f"READ_VOUT = 0x{value:04X}")
```

#### 4. Write Single Byte
```python
# Write to PAGE register (0x00) to select page 0
response = driver.i2cset(
    bus=1,
    chip_addr=0x5C,
    data_addr=0x00,
    values=0,
    mode='b',
    assume_yes=True
)
```

#### 5. Write Word (16-bit)
```python
# Write word value to VOUT_COMMAND register (0x21)
response = driver.i2cset(
    bus=1,
    chip_addr=0x5C,
    data_addr=0x21,
    values=0x0C00,
    mode='w',
    assume_yes=True
)
```

#### 6. Raw Command
```python
# Send any i2c-tools command directly
response = driver.raw_command("i2cdetect -y 1")
print(response)
```

### API Reference

#### `i2cget(bus, chip_addr, data_addr, mode='b', assume_yes=True)`
Read data from I2C device.

**Parameters:**
- `bus`: I2C bus number (0-5)
- `chip_addr`: Device I2C address (0x00-0x7F)
- `data_addr`: Register address to read from
- `mode`: Read mode
  - `'b'` - byte (8-bit)
  - `'w'` - word (16-bit)
  - `'c'` - SMBus write/read byte
  - `'s'` - SMBus block read
  - `'i'` - I2C block read
  - Append `'p'` for PEC (e.g., `'bp'`, `'wp'`)
- `assume_yes`: Use `-y` flag (skip confirmation)

**Returns:** Response string from microcontroller

#### `i2cset(bus, chip_addr, data_addr, values, mode='b', assume_yes=True)`
Write data to I2C device.

**Parameters:**
- `bus`: I2C bus number (0-5)
- `chip_addr`: Device I2C address (0x00-0x7F)
- `data_addr`: Register address to write to
- `values`: Value to write (int or list of ints for block modes)
- `mode`: Write mode
  - `'c'` - command only (no value)
  - `'b'` - byte (8-bit)
  - `'w'` - word (16-bit)
  - `'i'` - I2C block write
  - `'s'` - SMBus block write
- `assume_yes`: Use `-y` flag (skip confirmation)

**Returns:** Response string from microcontroller

#### `parse_i2cget_response(response)`
Extract numeric value from i2cget response.

**Parameters:**
- `response`: Response string from i2cget command

**Returns:** Integer value or None if parsing fails

---

## PowerTool with Serial I2C

### Overview
`powertool.py` has been refactored to use the serial I2C driver instead of the Aardvark adapter. All CLI commands remain identical.

### Configuration
Edit these constants in `powertool.py` if needed:

```python
SLAVE_ADDR = 0x5C              # PMBus device address
I2C_BUS = 1                    # I2C bus number
SERIAL_PORT = "/dev/ttyUSB0"   # Serial port
SERIAL_BAUD = 115200           # Baud rate
```

### Command Line Usage

#### Read Telemetry
```bash
# Read voltage from TSP_CORE rail
./powertool.py TSP_CORE READ_VOUT

# Read current from TSP_C2C rail
./powertool.py TSP_C2C READ_IOUT

# Read temperature
./powertool.py TSP_CORE READ_TEMP

# Read status word
./powertool.py TSP_CORE STATUS_WORD
```

#### Set Voltage
```bash
# Set TSP_CORE voltage to 0.8V
./powertool.py TSP_CORE VOUT_COMMAND 0.8

# Set TSP_C2C voltage to 0.75V
./powertool.py TSP_C2C VOUT_COMMAND 0.75
```

#### Direct Register Access
```bash
# Read single byte from register 0x01
./powertool.py TSP_CORE READ 0x01

# Read word from register 0x8B
./powertool.py TSP_CORE READ 0x8B 2

# Write byte to register 0x21
./powertool.py TSP_CORE WRITE 0x21 0x80 1

# Write word to register 0x21
./powertool.py TSP_CORE WRITE 0x21 0x0C00 2
```

#### Continuous Logging
```bash
# Log voltage to CSV file (auto-generated filename)
./powertool.py TSP_CORE READ_VOUT log

# Log current to CSV
./powertool.py TSP_CORE READ_IOUT log

# Stop logging with Ctrl+C
```

#### Legacy Page-Based Access
```bash
# Read from page 0, register 0x8B (2 bytes)
./powertool.py page 0 READ_VOUT READ 2

# Read from page 1, register 0x8C (2 bytes)
./powertool.py page 1 READ_IOUT READ 2

# Log to CSV
./powertool.py page 0 STATUS_WORD LOG 2
```

### Rail Mapping
- **TSP_CORE** → Page 0 (primary voltage rail)
- **TSP_C2C** → Page 1 (secondary voltage rail)

---

## Quick Start Examples

### Example 1: Simple Read Test
```bash
python3 test_simple_read.py
```

**Output:**
```
Connected
Authenticated

Reading OPERATION register (0x01):
Response: 'i2cget -y 1 0x5c 0x01
0x38
root@stm32mp25-ursa_p1a:~#'
Value: 0x38 (56 decimal)
Binary: 00111000
```

### Example 2: Read Both Rails
```bash
python3 demo_both_rails.py
```

**Output:**
```
======================================================================
PMBus Demo - TSP_CORE and TSP_C2C (Serial I2C)
======================================================================

Initializing...
✓ Connected

TSP_CORE (Page 0):
----------------------------------------------------------------------
  OPERATION: 0x38
  READ_VOUT: 0x0000

✓ TSP_CORE complete

TSP_C2C (Page 1):
----------------------------------------------------------------------
  OPERATION: 0x38
  READ_VOUT: 0x0000

✓ TSP_C2C complete

======================================================================
✓ Demo complete - Both rails read successfully!
```

### Example 3: Scan I2C Buses
```bash
python3 test_i2c_buses.py
```

### Example 4: Using PowerTool Library
```python
from powertool import PowerToolI2C, PMBusDict
import time

# Initialize
pt = PowerToolI2C()

# Read from TSP_CORE (page 0)
operation = pt.i2c_read8PMBus(0, PMBusDict["OPERATION"])
print(f"OPERATION: 0x{operation:02X}")

vout = pt.i2c_read16PMBus(0, PMBusDict["READ_VOUT"])
print(f"READ_VOUT: 0x{vout:04X}")

# Read from TSP_C2C (page 1)
operation = pt.i2c_read8PMBus(1, PMBusDict["OPERATION"])
print(f"OPERATION: 0x{operation:02X}")

vout = pt.i2c_read16PMBus(1, PMBusDict["READ_VOUT"])
print(f"READ_VOUT: 0x{vout:04X}")

# Clean up
pt.driver.close()
```

---

## Configuration

### Serial Port Permissions
If you get "Permission denied" error:

```bash
# Option 1: Add user to dialout group (recommended)
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect

# Option 2: Temporarily change permissions
sudo chmod 666 /dev/ttyUSB0
```

### Verify Serial Connection
```bash
# List available serial ports
ls -l /dev/ttyUSB*

# Test serial connection with screen
screen /dev/ttyUSB0 115200
# Press Enter, you should see a shell prompt
# Exit with Ctrl+A then K
```

### Timing Adjustments
If you experience timeouts, adjust these values:

**In `serial_i2c_driver.py` (line ~87):**
```python
time.sleep(0.3)  # Increase if commands timeout (try 0.5)
```

**In `SerialI2CDriver.__init__()`:**
```python
timeout=3.0  # Increase if reads timeout (try 5.0)
```

**In `powertool.py`:**
```python
# After page writes (line ~214)
time.sleep(0.1)  # Increase if page switching fails

# After byte writes (line ~160)
time.sleep(0.05)  # Increase if writes fail
```

---

## Troubleshooting

### Problem: "Could not open file '/dev/ttyUSB0'"
**Solutions:**
- Check device is connected: `ls -l /dev/ttyUSB*`
- Check permissions: `sudo chmod 666 /dev/ttyUSB0`
- Add user to dialout group: `sudo usermod -a -G dialout $USER`

### Problem: "Read failed" errors
**Solutions:**
- Verify device is on bus 1: `i2cdetect -y 1` (on STM32MP25)
- Check device address is 0x5C
- Ensure power is applied to PMBus device
- Increase timeout in SerialI2CDriver initialization

### Problem: Commands timeout
**Solutions:**
- Increase `time.sleep()` values in `serial_i2c_driver.py`
- Increase timeout: `SerialI2CDriver(timeout=5.0)`
- Check STM32MP25 responsiveness with screen/minicom

### Problem: Wrong values returned
**Solutions:**
- Check correct page is selected (0 or 1)
- Verify register address
- Use correct mode: 'b' for 8-bit, 'w' for 16-bit
- Check PMBus uses little-endian format

### Problem: Serial buffer overflow
**Solutions:**
- Increase delays between commands
- Add `time.sleep(0.2)` between operations
- Reduce logging frequency

---

## Demo Scripts Reference

| Script | Purpose |
|--------|---------|
| `test_simple_read.py` | Basic read - OPERATION register |
| `test_word_read.py` | Test byte and word reads |
| `test_i2c_buses.py` | Scan all I2C buses |
| `test_i2c_detect.py` | Detect devices on bus 0 |
| `demo_both_rails.py` | Read TSP_CORE and TSP_C2C |
| `demo_debug.py` | Verbose debug output |
| `test_powertool_simple.py` | Test PowerToolI2C class |

---

## Technical Details

### Command Flow
```
Python Script
    ↓
SerialI2CDriver.i2cget()
    ↓
Serial: "i2cget -y 1 0x5c 0x8b w\n"
    ↓
STM32MP25 Shell
    ↓
Linux i2c-tools
    ↓
I2C Bus 1
    ↓
PMBus Device (0x5C)
    ↓
Response: "0x0ABC"
    ↓
parse_i2cget_response()
    ↓
Return: 0x0ABC
```

### Timing Requirements
- **Initialization**: 0.5s wait + 0.2s buffer clear
- **Command execution**: 0.3s wait for I2C operation
- **Page write**: Additional 0.1s delay
- **Between commands**: 0.05-0.2s recommended

### Data Formats
- **Linear11**: 5-bit exponent + 11-bit mantissa (IOUT, TEMP)
- **Linear16**: 16-bit mantissa with VOUT_MODE exponent (VOUT)
- **VID Mode**: Custom step size from MFR_VID_RES_R1

### Key Differences from Aardvark Version
| Aspect | Aardvark | Serial I2C |
|--------|----------|------------|
| Connection | USB direct | Serial/UART |
| Speed | ~400 kHz | Limited by serial (slower) |
| Latency | Low (~ms) | Higher (~0.3s per command) |
| Setup | Native library | Standard Python serial |
| Remote | No | Yes (via serial) |
| Cost | $$$ | $ |

---

## Additional Resources

- **PMBus Specification**: https://pmbus.org/
- **i2c-tools Manual**: `man i2cget`, `man i2cset`
- **MP29816-C Datasheet**: Contact MPS
- **Original Tool**: See `CLAUDE.md` for Aardvark usage

---

## Support

For issues:
1. Check this guide and troubleshooting section
2. Run demo scripts to verify hardware
3. Test serial connection with `screen` or `minicom`
4. Verify I2C devices: `i2cdetect -y 1` (on STM32MP25)
5. Review logs: `dmesg | grep ttyUSB`

---

**Last Updated**: 2025-10-07
**Version**: 1.0 (Serial I2C Driver)
**Hardware**: STM32MP25-URSA_P1A with MP29816-C PMBus Controller
