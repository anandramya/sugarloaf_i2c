# Serial I2C Quick Reference

Fast reference for common commands and operations.

---

## Hardware
- **Device**: MP29816-C PMBus @ 0x5C on I2C Bus 1
- **Connection**: /dev/ttyUSB0 @ 115200 baud
- **Rails**: TSP_CORE (Page 0), TSP_C2C (Page 1)

---

## PowerTool CLI Commands

### Read Telemetry
```bash
./powertool.py TSP_CORE READ_VOUT         # Voltage
./powertool.py TSP_CORE READ_IOUT         # Current
./powertool.py TSP_CORE READ_TEMP         # Temperature
./powertool.py TSP_CORE READ_DIE_TEMP     # Die Temperature
./powertool.py TSP_CORE STATUS_WORD       # Status
```

### Set Voltage
```bash
./powertool.py TSP_CORE VOUT_COMMAND 0.8  # Set 0.8V
./powertool.py TSP_C2C VOUT_COMMAND 0.75  # Set 0.75V
```

### Direct Register Access
```bash
./powertool.py TSP_CORE READ 0x01         # Read byte
./powertool.py TSP_CORE READ 0x8B 2       # Read word
./powertool.py TSP_CORE WRITE 0x21 0x80 1  # Write byte
```

### Logging
```bash
./powertool.py TSP_CORE READ_VOUT log     # Start logging
# Ctrl+C to stop
```

---

## Python API - Serial Driver

### Initialize
```python
from serial_i2c_driver import SerialI2CDriver
driver = SerialI2CDriver("/dev/ttyUSB0", 115200)
```

### Read Byte
```python
resp = driver.i2cget(1, 0x5C, 0x01, 'b', assume_yes=True)
val = driver.parse_i2cget_response(resp)
```

### Read Word
```python
resp = driver.i2cget(1, 0x5C, 0x8B, 'w', assume_yes=True)
val = driver.parse_i2cget_response(resp)
```

### Write Byte
```python
driver.i2cset(1, 0x5C, 0x00, 0, 'b', assume_yes=True)
```

### Write Word
```python
driver.i2cset(1, 0x5C, 0x21, 0x0C00, 'w', assume_yes=True)
```

---

## Python API - PowerTool

### Initialize
```python
from powertool import PowerToolI2C, PMBusDict
pt = PowerToolI2C()
```

### Read Byte
```python
val = pt.i2c_read8PMBus(0, PMBusDict["OPERATION"])  # Page 0
```

### Read Word
```python
val = pt.i2c_read16PMBus(0, PMBusDict["READ_VOUT"])  # Page 0
```

### Write Byte
```python
pt.i2c_write8PMBus(PMBusDict["PAGE"], 0)  # Set page 0
```

### Write Word
```python
pt.i2c_write16PMBus(0, PMBusDict["VOUT_COMMAND"], 0x0C00)
```

---

## Common PMBus Registers

| Register | Address | Type | Description |
|----------|---------|------|-------------|
| PAGE | 0x00 | Byte | Page select (0 or 1) |
| OPERATION | 0x01 | Byte | Enable/control |
| VOUT_MODE | 0x20 | Byte | Voltage format |
| VOUT_COMMAND | 0x21 | Word | Voltage setpoint |
| STATUS_WORD | 0x79 | Word | Fault status |
| READ_VOUT | 0x8B | Word | Output voltage |
| READ_IOUT | 0x8C | Word | Output current |
| READ_TEMP | 0x8D | Word | Temperature |
| READ_DIE_TEMP | 0x8E | Word | Die Temperature |

---

## Test & Demo Scripts

```bash
python3 test_simple_read.py       # Test single read
python3 demo_both_rails.py        # Read both rails
python3 test_i2c_buses.py         # Scan I2C buses
python3 test_word_read.py         # Test byte/word
```

---

## Troubleshooting Commands

### Check Serial Port
```bash
ls -l /dev/ttyUSB*
sudo chmod 666 /dev/ttyUSB0
```

### Test Serial Connection
```bash
screen /dev/ttyUSB0 115200
# Ctrl+A then K to exit
```

### Check I2C Bus (on STM32MP25)
```bash
i2cdetect -y 1
```

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Permission denied | `sudo chmod 666 /dev/ttyUSB0` |
| Read failed | Check device on bus 1, not bus 0 |
| Timeout | Increase delays in serial_i2c_driver.py |
| Wrong values | Verify page selection (0 or 1) |

---

## Important Notes

⚠️ **Device is on BUS 1, not bus 0**
⚠️ **Use word mode ('w') for 16-bit registers**
⚠️ **Always set PAGE before reading multi-page registers**
⚠️ **Wait 0.1-0.3s between commands**

---

**See SERIAL_I2C_USAGE.md for complete documentation**
