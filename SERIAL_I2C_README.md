# Serial I2C Driver

Python driver for sending i2cget/i2cset commands to a microcontroller via serial connection.

## Overview

This driver allows you to control I2C devices through a microcontroller connected via USB serial (/dev/ttyUSB0). The microcontroller acts as an I2C bridge, executing i2cget and i2cset commands sent over the serial connection.

## Features

- **Full i2cget support**: All modes (byte, word, SMBus block, I2C block) with PEC
- **Full i2cset support**: Byte, word, and block writes with mask and readback verification
- **Response parsing**: Automatic extraction of values from command responses
- **Easy-to-use API**: Python methods mirror i2cget/i2cset command syntax
- **Raw command mode**: Send any command string to the microcontroller
- **Interactive mode**: Command-line interface for testing

## Hardware Setup

1. Connect microcontroller to /dev/ttyUSB0
2. Configure serial port: 115200 baud, 8N1 (default)
3. Ensure microcontroller firmware responds to i2cget/i2cset commands

## Installation

```bash
# Install pyserial dependency
pip install pyserial

# Make scripts executable
chmod +x serial_i2c_driver.py
chmod +x test_serial_i2c.py
```

## Quick Start

### Basic Usage

```python
from serial_i2c_driver import SerialI2CDriver

# Initialize driver
driver = SerialI2CDriver(port="/dev/ttyUSB0", baudrate=115200)

# Read byte from I2C device
response = driver.i2cget(bus=0, chip_addr=0x50, data_addr=0x00, mode='b')
value = driver.parse_i2cget_response(response)
print(f"Value: 0x{value:02X}")

# Write byte to I2C device
driver.i2cset(bus=0, chip_addr=0x50, data_addr=0x10, values=0xFF, mode='b')

# Close connection
driver.close()
```

### Running Tests

```bash
# Run all tests
./test_serial_i2c.py

# Run specific tests
./test_serial_i2c.py --basic      # Basic I2C operations
./test_serial_i2c.py --pmbus      # PMBus monitoring example
./test_serial_i2c.py --interactive # Interactive command mode
```

## API Reference

### SerialI2CDriver Class

#### Constructor

```python
driver = SerialI2CDriver(port="/dev/ttyUSB0", baudrate=115200, timeout=1.0)
```

**Parameters:**
- `port`: Serial port device (default: "/dev/ttyUSB0")
- `baudrate`: Serial baud rate (default: 115200)
- `timeout`: Read timeout in seconds (default: 1.0)

#### i2cget Method

```python
response = driver.i2cget(bus, chip_addr, data_addr=None, mode='b',
                        length=None, force=False, assume_yes=False,
                        allow_reserved=False)
```

**Parameters:**
- `bus`: I2C bus number or name
- `chip_addr`: I2C chip address (0x08-0x77, or 0x00-0x7f with allow_reserved)
- `data_addr`: Data address/register (optional)
- `mode`: Read mode
  - `'b'` - Read byte data (default)
  - `'w'` - Read word data
  - `'c'` - Write byte/read byte
  - `'s'` - Read SMBus block data
  - `'i'` - Read I2C block data
  - Append `'p'` for PEC (e.g., `'bp'`, `'wp'`)
- `length`: I2C block data length (1-32, default 32 for mode 'i')
- `force`: Use -f flag (force access)
- `assume_yes`: Use -y flag (skip confirmation prompts)
- `allow_reserved`: Use -a flag (allow reserved addresses 0x00-0x07)

**Examples:**

```python
# Read byte
response = driver.i2cget(1, 0x50, 0x00, 'b')

# Read word with PEC
response = driver.i2cget(1, 0x50, 0x00, 'wp')

# Read I2C block (16 bytes)
response = driver.i2cget(1, 0x50, 0x00, 'i', length=16)

# Force access with assume yes
response = driver.i2cget(1, 0x50, 0x00, 'b', force=True, assume_yes=True)
```

#### i2cset Method

```python
response = driver.i2cset(bus, chip_addr, data_addr, values=None,
                        mode='b', mask=None, readback=False,
                        force=False, assume_yes=False,
                        allow_reserved=False)
```

**Parameters:**
- `bus`: I2C bus number or name
- `chip_addr`: I2C chip address (0x08-0x77, or 0x00-0x7f with allow_reserved)
- `data_addr`: Data address/register
- `values`: Value(s) to write - single int or list of ints for block modes
- `mode`: Write mode
  - `'c'` - Byte, no value (command only)
  - `'b'` - Byte data (default)
  - `'w'` - Word data
  - `'i'` - I2C block data
  - `'s'` - SMBus block data
  - Append `'p'` for PEC (e.g., `'bp'`, `'wp'`)
- `mask`: Mask value for -m flag (only bits set in mask are modified)
- `readback`: Use -r flag (read back and verify)
- `force`: Use -f flag (force access)
- `assume_yes`: Use -y flag (skip confirmation prompts)
- `allow_reserved`: Use -a flag (allow reserved addresses)

**Examples:**

```python
# Write single byte
response = driver.i2cset(1, 0x50, 0x10, 0xFF, 'b')

# Write word with readback
response = driver.i2cset(1, 0x50, 0x10, 0x1234, 'w', readback=True)

# Write with mask (modify only bits 0-3)
response = driver.i2cset(1, 0x50, 0x10, 0x0F, 'b', mask=0x0F)

# Write I2C block data
response = driver.i2cset(1, 0x50, 0x00, [0x01, 0x02, 0x03, 0x04], 'i')

# Send command without data
response = driver.i2cset(1, 0x50, 0x03, mode='c')  # CLEAR_FAULTS
```

#### Utility Methods

```python
# Send raw command
response = driver.raw_command("i2cdetect -y 1")

# Parse response to extract value
value = driver.parse_i2cget_response(response)

# Test connection
is_connected = driver.test_connection()

# Close connection
driver.close()
```

## PMBus Example

```python
from serial_i2c_driver import SerialI2CDriver

# Initialize
driver = SerialI2CDriver()

# PMBus device address
PMBUS_ADDR = 0x5C

# Set page to 0 (TSP_CORE rail)
driver.i2cset(0, PMBUS_ADDR, 0x00, 0x00, 'b', assume_yes=True)

# Read voltage (READ_VOUT register 0x8B)
response = driver.i2cget(0, PMBUS_ADDR, 0x8B, 'w', assume_yes=True)
vout_raw = driver.parse_i2cget_response(response)
print(f"VOUT raw: 0x{vout_raw:04X}")

# Read current (READ_IOUT register 0x8C)
response = driver.i2cget(0, PMBUS_ADDR, 0x8C, 'w', assume_yes=True)
iout_raw = driver.parse_i2cget_response(response)
print(f"IOUT raw: 0x{iout_raw:04X}")

# Read status word
response = driver.i2cget(0, PMBUS_ADDR, 0x79, 'w', assume_yes=True)
status = driver.parse_i2cget_response(response)
print(f"STATUS_WORD: 0x{status:04X}")

# Set voltage (VOUT_COMMAND register 0x21)
vout_cmd = 0x0C00  # Example voltage setpoint
driver.i2cset(0, PMBUS_ADDR, 0x21, vout_cmd, 'w', assume_yes=True, readback=True)

driver.close()
```

## Interactive Mode

```bash
./test_serial_i2c.py --interactive
```

In interactive mode, you can send commands directly:

```
>> i2cget -y 0 0x5c 0x8b w
0x0c42

>> i2cset -y 0 0x5c 0x00 0x00 b
(command executes)

>> i2cdetect -y 0
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- --
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- 5c -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --

>> quit
```

## Integration with PowerTool

You can integrate this driver with the existing PowerTool PMBus monitoring:

```python
from serial_i2c_driver import SerialI2CDriver

class PowerToolSerial:
    """PowerTool using serial I2C instead of Aardvark"""

    def __init__(self, serial_port="/dev/ttyUSB0"):
        self.driver = SerialI2CDriver(port=serial_port)
        self.bus = 0  # I2C bus number
        self.slave_addr = 0x5C

    def Read_Vout(self, page):
        # Set page
        self.driver.i2cset(self.bus, self.slave_addr, 0x00, page, 'b', assume_yes=True)

        # Read VOUT
        response = self.driver.i2cget(self.bus, self.slave_addr, 0x8B, 'w', assume_yes=True)
        raw_value = self.driver.parse_i2cget_response(response)

        # Convert using Linear16 format (add VID step calculation here)
        return raw_value

    def Read_Iout(self, page):
        # Set page
        self.driver.i2cset(self.bus, self.slave_addr, 0x00, page, 'b', assume_yes=True)

        # Read IOUT
        response = self.driver.i2cget(self.bus, self.slave_addr, 0x8C, 'w', assume_yes=True)
        raw_value = self.driver.parse_i2cget_response(response)

        # Convert using Linear11 format (add conversion here)
        return raw_value
```

## Troubleshooting

### Serial Port Permission Denied

```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Log out and back in for changes to take effect

# Or change port permissions (temporary)
sudo chmod 666 /dev/ttyUSB0
```

### No Response from Microcontroller

1. Check serial connection: `ls -l /dev/ttyUSB*`
2. Verify baud rate matches microcontroller (115200)
3. Test with screen: `screen /dev/ttyUSB0 115200`
4. Check microcontroller firmware is running
5. Increase timeout: `SerialI2CDriver(timeout=5.0)`

### Parsing Errors

If `parse_i2cget_response()` returns None:
- Print the raw response to see format
- Microcontroller may be returning error messages
- Check command syntax is correct

### I2C Communication Errors

- Verify I2C bus number is correct
- Check device address (use i2cdetect)
- Ensure pull-up resistors are present
- Try with `-f` (force) flag if needed

## Command Reference

### i2cget Command Format

```
i2cget [-f] [-y] [-a] I2CBUS CHIP-ADDRESS [DATA-ADDRESS [MODE [LENGTH]]]
```

**Modes:**
- `b` - Read byte data (default)
- `w` - Read word data
- `c` - Write byte/read byte
- `s` - Read SMBus block data
- `i` - Read I2C block data
- Append `p` for SMBus PEC

### i2cset Command Format

```
i2cset [-f] [-y] [-m MASK] [-r] [-a] I2CBUS CHIP-ADDRESS DATA-ADDRESS [VALUE] ... [MODE]
```

**Modes:**
- `c` - Byte, no value (command only)
- `b` - Byte data (default)
- `w` - Word data
- `i` - I2C block data
- `s` - SMBus block data
- Append `p` for SMBus PEC

## License

This tool is provided as-is for I2C/PMBus development and testing.
